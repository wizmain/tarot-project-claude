"""
Settings API Routes - 애플리케이션 설정 관리 API

이 모듈의 목적:
- 데이터베이스에 저장된 동적 설정 관리
- 관리자 이메일 관리
- LLM Provider 설정 관리
- 관리자만 접근 가능 (get_current_admin_user)

주요 엔드포인트:
- GET /api/v1/settings: 현재 설정 조회
- PUT /api/v1/settings/admin: 관리자 설정 업데이트
- PUT /api/v1/settings/ai: AI 설정 업데이트
- POST /api/v1/settings/admin/emails: 관리자 이메일 추가
- DELETE /api/v1/settings/admin/emails/{email}: 관리자 이메일 제거
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path

from src.core.logging import get_logger
from src.database.factory import get_database_provider
from src.database.provider import DatabaseProvider
from src.api.dependencies.auth import get_current_admin_user
from src.schemas.settings import (
    SettingsResponse,
    UpdateAdminSettingsRequest,
    UpdateAISettingsRequest,
    AdminSettings,
    AISettings,
    LLMProviderConfig,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    애플리케이션 설정 조회 (관리자 전용)
    
    Returns:
        SettingsResponse: 현재 설정 (API 키는 마스킹됨)
    """
    try:
        settings_data = await db_provider.get_app_settings()
        
        if not settings_data:
            # Return default settings
            return SettingsResponse(
                admin=AdminSettings(admin_emails=[]),
                ai=AISettings(
                    provider_priority=["openai", "anthropic"],
                    providers=[],
                    default_timeout=30
                ),
                updated_at=None,
                updated_by=None
            )
        
        # Mask API keys for security
        ai_settings = settings_data.get('ai', {})
        providers = ai_settings.get('providers', [])
        
        masked_providers = []
        for provider in providers:
            masked_provider = provider.copy()
            api_key = masked_provider.get('api_key', '')
            if api_key and len(api_key) > 10:
                # Show only first 7 and last 4 characters
                masked_provider['api_key'] = f"{api_key[:7]}***{api_key[-4:]}"
            masked_providers.append(masked_provider)
        
        ai_settings['providers'] = masked_providers
        
        return SettingsResponse(
            admin=AdminSettings(**settings_data.get('admin', {})),
            ai=AISettings(**ai_settings),
            updated_at=settings_data.get('updated_at'),
            updated_by=settings_data.get('updated_by')
        )
        
    except Exception as e:
        logger.error(f"[Settings] 설정 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="설정 조회 중 오류가 발생했습니다"
        )


@router.put("/admin", response_model=SettingsResponse)
async def update_admin_settings(
    request: UpdateAdminSettingsRequest,
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    관리자 설정 업데이트 (관리자 전용)
    
    Args:
        request: 관리자 설정 업데이트 요청
        
    Returns:
        SettingsResponse: 업데이트된 설정
    """
    try:
        admin_email = getattr(current_admin, 'email', 'unknown')
        user_id = getattr(current_admin, 'id', 'unknown')
        
        logger.info(f"[Settings] 관리자 설정 업데이트 by {admin_email}")
        
        # Get current settings
        current_settings = await db_provider.get_app_settings() or {}
        
        # Update admin settings
        updated_settings = {
            **current_settings,
            'admin': {
                'admin_emails': request.admin_emails
            }
        }
        
        # Save to database
        result = await db_provider.update_app_settings(
            updated_settings,
            updated_by=str(user_id)
        )
        
        return SettingsResponse(
            admin=AdminSettings(**result.get('admin', {})),
            ai=AISettings(**result.get('ai', {})),
            updated_at=result.get('updated_at'),
            updated_by=result.get('updated_by')
        )
        
    except Exception as e:
        logger.error(f"[Settings] 관리자 설정 업데이트 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="설정 업데이트 중 오류가 발생했습니다"
        )


@router.put("/ai", response_model=SettingsResponse)
async def update_ai_settings(
    request: UpdateAISettingsRequest,
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    AI 설정 업데이트 (관리자 전용)
    
    Args:
        request: AI 설정 업데이트 요청
        
    Returns:
        SettingsResponse: 업데이트된 설정
    """
    try:
        admin_email = getattr(current_admin, 'email', 'unknown')
        user_id = getattr(current_admin, 'id', 'unknown')
        
        logger.info(f"[Settings] AI 설정 업데이트 by {admin_email}")
        
        # Get current settings
        current_settings = await db_provider.get_app_settings() or {}
        current_ai = current_settings.get('ai', {})
        
        # Update AI settings (only provided fields)
        updated_ai = current_ai.copy()
        if request.provider_priority is not None:
            updated_ai['provider_priority'] = request.provider_priority
        if request.providers is not None:
            updated_ai['providers'] = [p.model_dump() for p in request.providers]
        if request.default_timeout is not None:
            updated_ai['default_timeout'] = request.default_timeout
        
        updated_settings = {
            **current_settings,
            'ai': updated_ai
        }
        
        # Save to database
        result = await db_provider.update_app_settings(
            updated_settings,
            updated_by=str(user_id)
        )
        
        # Invalidate orchestrator cache to apply new settings
        from src.api.routes.readings import invalidate_orchestrator_cache as inv_readings
        from src.api.routes.readings_stream import invalidate_orchestrator_cache as inv_stream
        inv_readings()
        inv_stream()
        logger.info("[Settings] ✓ AI Orchestrator cache invalidated after settings update")
        
        # Mask API keys in response
        ai_result = result.get('ai', {})
        providers = ai_result.get('providers', [])
        masked_providers = []
        for provider in providers:
            masked_provider = provider.copy()
            api_key = masked_provider.get('api_key', '')
            if api_key and len(api_key) > 10:
                masked_provider['api_key'] = f"{api_key[:7]}***{api_key[-4:]}"
            masked_providers.append(masked_provider)
        ai_result['providers'] = masked_providers
        
        return SettingsResponse(
            admin=AdminSettings(**result.get('admin', {})),
            ai=AISettings(**ai_result),
            updated_at=result.get('updated_at'),
            updated_by=result.get('updated_by')
        )
        
    except Exception as e:
        logger.error(f"[Settings] AI 설정 업데이트 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="설정 업데이트 중 오류가 발생했습니다"
        )


@router.post("/admin/emails/{email}")
async def add_admin_email(
    email: str = Path(..., description="추가할 관리자 이메일"),
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    관리자 이메일 추가 (관리자 전용)
    
    Args:
        email: 추가할 이메일 주소
        
    Returns:
        성공 메시지
    """
    try:
        admin_email = getattr(current_admin, 'email', 'unknown')
        user_id = getattr(current_admin, 'id', 'unknown')
        
        logger.info(f"[Settings] 관리자 이메일 추가: {email} by {admin_email}")
        
        await db_provider.add_admin_email(email, updated_by=str(user_id))
        
        return {
            "message": f"관리자 이메일 '{email}'이(가) 추가되었습니다",
            "email": email
        }
        
    except Exception as e:
        logger.error(f"[Settings] 관리자 이메일 추가 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="이메일 추가 중 오류가 발생했습니다"
        )


@router.delete("/admin/emails/{email}")
async def remove_admin_email(
    email: str = Path(..., description="제거할 관리자 이메일"),
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    관리자 이메일 제거 (관리자 전용)
    
    주의: 마지막 관리자를 제거하지 않도록 주의하세요!
    
    Args:
        email: 제거할 이메일 주소
        
    Returns:
        성공 메시지
    """
    try:
        admin_email = getattr(current_admin, 'email', 'unknown')
        user_id = getattr(current_admin, 'id', 'unknown')
        
        # Prevent removing self if last admin
        admin_emails = await db_provider.get_admin_emails()
        
        if email == admin_email and len(admin_emails) <= 1:
            raise HTTPException(
                status_code=400,
                detail="마지막 관리자는 제거할 수 없습니다"
            )
        
        logger.info(f"[Settings] 관리자 이메일 제거: {email} by {admin_email}")
        
        await db_provider.remove_admin_email(email, updated_by=str(user_id))
        
        return {
            "message": f"관리자 이메일 '{email}'이(가) 제거되었습니다",
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Settings] 관리자 이메일 제거 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="이메일 제거 중 오류가 발생했습니다"
        )


@router.post("/ai/providers", response_model=SettingsResponse)
async def add_provider(
    provider: LLMProviderConfig,
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    AI Provider 추가 (관리자 전용)
    
    Args:
        provider: Provider 설정 (name, api_key, model, enabled, timeout)
        
    Returns:
        SettingsResponse: 업데이트된 전체 설정
    """
    try:
        admin_email = getattr(current_admin, 'email', 'unknown')
        user_id = getattr(current_admin, 'id', 'unknown')
        
        logger.info(f"[Settings] Provider 추가: {provider.name} by {admin_email}")
        
        # Get current settings
        current_settings = await db_provider.get_app_settings() or {}
        current_ai = current_settings.get('ai', {})
        providers = current_ai.get('providers', [])
        
        # Check for duplicate provider name
        existing_names = [p.get('name') for p in providers]
        if provider.name in existing_names:
            raise HTTPException(
                status_code=400,
                detail=f"Provider '{provider.name}'은(는) 이미 존재합니다"
            )
        
        # Add new provider
        new_provider = provider.model_dump()
        providers.append(new_provider)
        
        # Update AI settings
        updated_ai = current_ai.copy()
        updated_ai['providers'] = providers
        
        # Add to priority list if not exists
        provider_priority = updated_ai.get('provider_priority', [])
        if provider.name not in provider_priority:
            provider_priority.append(provider.name)
            updated_ai['provider_priority'] = provider_priority
        
        # Save to database
        updated_settings = {
            **current_settings,
            'ai': updated_ai
        }
        
        result = await db_provider.update_app_settings(
            updated_settings,
            updated_by=str(user_id)
        )
        
        # Invalidate orchestrator cache to apply new provider
        from src.api.routes.readings import invalidate_orchestrator_cache as inv_readings
        from src.api.routes.readings_stream import invalidate_orchestrator_cache as inv_stream
        inv_readings()
        inv_stream()
        logger.info(f"[Settings] ✓ AI Orchestrator cache invalidated after adding provider '{provider.name}'")
        
        # Mask API keys in response
        ai_result = result.get('ai', {})
        masked_providers = []
        for p in ai_result.get('providers', []):
            masked_p = p.copy()
            api_key = masked_p.get('api_key', '')
            if api_key and len(api_key) > 10:
                masked_p['api_key'] = f"{api_key[:7]}***{api_key[-4:]}"
            masked_providers.append(masked_p)
        ai_result['providers'] = masked_providers
        
        logger.info(f"[Settings] Provider '{provider.name}' 추가 완료")
        
        return SettingsResponse(
            admin=AdminSettings(**result.get('admin', {})),
            ai=AISettings(**ai_result),
            updated_at=result.get('updated_at'),
            updated_by=result.get('updated_by')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Settings] Provider 추가 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="Provider 추가 중 오류가 발생했습니다"
        )


@router.delete("/ai/providers/{provider_name}", response_model=SettingsResponse)
async def delete_provider(
    provider_name: str = Path(..., description="삭제할 Provider 이름"),
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    AI Provider 삭제 (관리자 전용)
    
    Args:
        provider_name: 삭제할 Provider 이름
        
    Returns:
        SettingsResponse: 업데이트된 전체 설정
    """
    try:
        admin_email = getattr(current_admin, 'email', 'unknown')
        user_id = getattr(current_admin, 'id', 'unknown')
        
        logger.info(f"[Settings] Provider 삭제: {provider_name} by {admin_email}")
        
        # Get current settings
        current_settings = await db_provider.get_app_settings() or {}
        current_ai = current_settings.get('ai', {})
        providers = current_ai.get('providers', [])
        
        # Find and remove provider
        original_count = len(providers)
        providers = [p for p in providers if p.get('name') != provider_name]
        
        if len(providers) == original_count:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_name}'을(를) 찾을 수 없습니다"
            )
        
        # Update AI settings
        updated_ai = current_ai.copy()
        updated_ai['providers'] = providers
        
        # Remove from priority list
        provider_priority = updated_ai.get('provider_priority', [])
        if provider_name in provider_priority:
            provider_priority.remove(provider_name)
            updated_ai['provider_priority'] = provider_priority
        
        # Save to database
        updated_settings = {
            **current_settings,
            'ai': updated_ai
        }
        
        result = await db_provider.update_app_settings(
            updated_settings,
            updated_by=str(user_id)
        )
        
        # Invalidate orchestrator cache after deleting provider
        from src.api.routes.readings import invalidate_orchestrator_cache as inv_readings
        from src.api.routes.readings_stream import invalidate_orchestrator_cache as inv_stream
        inv_readings()
        inv_stream()
        logger.info(f"[Settings] ✓ AI Orchestrator cache invalidated after deleting provider '{provider_name}'")
        
        # Mask API keys in response
        ai_result = result.get('ai', {})
        masked_providers = []
        for p in ai_result.get('providers', []):
            masked_p = p.copy()
            api_key = masked_p.get('api_key', '')
            if api_key and len(api_key) > 10:
                masked_p['api_key'] = f"{api_key[:7]}***{api_key[-4:]}"
            masked_providers.append(masked_p)
        ai_result['providers'] = masked_providers
        
        logger.info(f"[Settings] Provider '{provider_name}' 삭제 완료")
        
        return SettingsResponse(
            admin=AdminSettings(**result.get('admin', {})),
            ai=AISettings(**ai_result),
            updated_at=result.get('updated_at'),
            updated_by=result.get('updated_by')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Settings] Provider 삭제 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="Provider 삭제 중 오류가 발생했습니다"
        )


@router.patch("/ai/providers/{provider_name}/toggle", response_model=SettingsResponse)
async def toggle_provider(
    provider_name: str = Path(..., description="토글할 Provider 이름"),
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    AI Provider 활성화/비활성화 토글 (관리자 전용)
    
    Args:
        provider_name: 토글할 Provider 이름
        
    Returns:
        SettingsResponse: 업데이트된 전체 설정
    """
    try:
        admin_email = getattr(current_admin, 'email', 'unknown')
        user_id = getattr(current_admin, 'id', 'unknown')
        
        logger.info(f"[Settings] Provider 토글: {provider_name} by {admin_email}")
        
        # Get current settings
        current_settings = await db_provider.get_app_settings() or {}
        current_ai = current_settings.get('ai', {})
        providers = current_ai.get('providers', [])
        
        # Find and toggle provider
        provider_found = False
        for provider in providers:
            if provider.get('name') == provider_name:
                provider['enabled'] = not provider.get('enabled', True)
                provider_found = True
                new_status = "활성화" if provider['enabled'] else "비활성화"
                logger.info(f"[Settings] Provider '{provider_name}' -> {new_status}")
                break
        
        if not provider_found:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_name}'을(를) 찾을 수 없습니다"
            )
        
        # Update AI settings
        updated_ai = current_ai.copy()
        updated_ai['providers'] = providers
        
        # Save to database
        updated_settings = {
            **current_settings,
            'ai': updated_ai
        }
        
        result = await db_provider.update_app_settings(
            updated_settings,
            updated_by=str(user_id)
        )
        
        # Invalidate orchestrator cache after toggling provider
        from src.api.routes.readings import invalidate_orchestrator_cache as inv_readings
        from src.api.routes.readings_stream import invalidate_orchestrator_cache as inv_stream
        inv_readings()
        inv_stream()
        logger.info(f"[Settings] ✓ AI Orchestrator cache invalidated after toggling provider '{provider_name}'")
        
        # Mask API keys in response
        ai_result = result.get('ai', {})
        masked_providers = []
        for p in ai_result.get('providers', []):
            masked_p = p.copy()
            api_key = masked_p.get('api_key', '')
            if api_key and len(api_key) > 10:
                masked_p['api_key'] = f"{api_key[:7]}***{api_key[-4:]}"
            masked_providers.append(masked_p)
        ai_result['providers'] = masked_providers
        
        return SettingsResponse(
            admin=AdminSettings(**result.get('admin', {})),
            ai=AISettings(**ai_result),
            updated_at=result.get('updated_at'),
            updated_by=result.get('updated_by')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Settings] Provider 토글 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="Provider 토글 중 오류가 발생했습니다"
        )


@router.patch("/ai/providers/priority", response_model=SettingsResponse)
async def update_provider_priority(
    provider_priority: List[str],
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    AI Provider 우선순위 변경 (관리자 전용)
    
    Args:
        provider_priority: 새로운 Provider 우선순위 리스트
        
    Returns:
        SettingsResponse: 업데이트된 전체 설정
        
    Example:
        PATCH /api/v1/settings/ai/providers/priority
        Body: ["anthropic", "openai"]
    """
    try:
        admin_email = getattr(current_admin, 'email', 'unknown')
        user_id = getattr(current_admin, 'id', 'unknown')
        
        logger.info(
            f"[Settings] Provider 우선순위 변경 by {admin_email}: {provider_priority}"
        )
        
        # Get current settings
        current_settings = await db_provider.get_app_settings() or {}
        current_ai = current_settings.get('ai', {})
        providers = current_ai.get('providers', [])
        
        # Validate: all providers in priority list must exist
        existing_provider_names = {p.get('name') for p in providers}
        for name in provider_priority:
            if name not in existing_provider_names:
                raise HTTPException(
                    status_code=400,
                    detail=f"Provider '{name}'이(가) 존재하지 않습니다"
                )
        
        # Check for duplicate names
        if len(provider_priority) != len(set(provider_priority)):
            raise HTTPException(
                status_code=400,
                detail="중복된 Provider 이름이 있습니다"
            )
        
        # Update AI settings
        updated_ai = current_ai.copy()
        updated_ai['provider_priority'] = provider_priority
        
        # Save to database
        updated_settings = {
            **current_settings,
            'ai': updated_ai
        }
        
        result = await db_provider.update_app_settings(
            updated_settings,
            updated_by=str(user_id)
        )
        
        # Invalidate orchestrator cache after priority change
        from src.api.routes.readings import invalidate_orchestrator_cache as inv_readings
        from src.api.routes.readings_stream import invalidate_orchestrator_cache as inv_stream
        inv_readings()
        inv_stream()
        logger.info(f"[Settings] ✓ AI Orchestrator cache invalidated after priority change")
        
        # Mask API keys in response
        ai_result = result.get('ai', {})
        masked_providers = []
        for p in ai_result.get('providers', []):
            masked_p = p.copy()
            api_key = masked_p.get('api_key', '')
            if api_key and len(api_key) > 10:
                masked_p['api_key'] = f"{api_key[:7]}***{api_key[-4:]}"
            masked_providers.append(masked_p)
        ai_result['providers'] = masked_providers
        
        logger.info(f"[Settings] Provider 우선순위 변경 완료: {provider_priority}")
        
        return SettingsResponse(
            admin=AdminSettings(**result.get('admin', {})),
            ai=AISettings(**ai_result),
            updated_at=result.get('updated_at'),
            updated_by=result.get('updated_by')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Settings] Provider 우선순위 변경 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="Provider 우선순위 변경 중 오류가 발생했습니다"
        )

