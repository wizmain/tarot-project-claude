"""
AI Provider Loader

데이터베이스의 app_settings에서 AI Provider 설정을 로드하고
AIOrchestrator에 사용할 Provider 인스턴스를 생성합니다.
"""
from typing import List, Optional, Dict, Any
from src.core.logging import get_logger
from src.ai import ProviderFactory
from src.ai.provider import AIProvider

logger = get_logger(__name__)


async def load_providers_from_settings(
    db_provider,
    fallback_to_env: bool = True
) -> List[AIProvider]:
    """
    데이터베이스에서 AI Provider 설정을 로드하여 Provider 인스턴스 리스트 반환
    
    Args:
        db_provider: DatabaseProvider 인스턴스
        fallback_to_env: DB 설정이 없을 때 환경 변수로 폴백할지 여부
        
    Returns:
        List[AIProvider]: 활성화된 Provider 인스턴스 리스트 (우선순위대로 정렬)
        
    Raises:
        ValueError: Provider가 하나도 설정되지 않은 경우
    """
    providers = []
    
    try:
        # 1. DB에서 app_settings 로드
        logger.info("[ProviderLoader] Loading AI providers from database...")
        app_settings = await db_provider.get_app_settings()
        
        if app_settings and app_settings.get('ai'):
            ai_settings = app_settings['ai']
            provider_priority = ai_settings.get('provider_priority', [])
            provider_configs = ai_settings.get('providers', [])
            default_timeout = ai_settings.get('default_timeout', 30)
            
            logger.info(
                f"[ProviderLoader] Found {len(provider_configs)} provider configs, "
                f"priority: {provider_priority}"
            )
            
            # 2. Provider 설정을 딕셔너리로 변환 (이름으로 빠른 조회)
            provider_map = {
                config['name']: config 
                for config in provider_configs 
                if config.get('enabled', False)
            }
            
            # 3. 우선순위대로 Provider 인스턴스 생성
            for provider_name in provider_priority:
                config = provider_map.get(provider_name)
                
                if not config:
                    logger.warning(
                        f"[ProviderLoader] Provider '{provider_name}' is in priority "
                        f"list but not configured or disabled"
                    )
                    continue
                
                api_key = config.get('api_key')
                if not api_key:
                    logger.warning(
                        f"[ProviderLoader] Provider '{provider_name}' has no API key, "
                        f"skipping"
                    )
                    continue
                
                try:
                    provider = ProviderFactory.create(
                        provider_name=provider_name,
                        api_key=api_key,
                        default_model=config.get('model'),
                        timeout=config.get('timeout', default_timeout),
                    )
                    providers.append(provider)
                    
                    logger.info(
                        f"[ProviderLoader] ✓ {provider_name.upper()} provider loaded "
                        f"(model: {config.get('model')}, "
                        f"timeout: {config.get('timeout', default_timeout)}s)"
                    )
                except Exception as e:
                    logger.error(
                        f"[ProviderLoader] Failed to create {provider_name} provider: {e}",
                        exc_info=True
                    )
            
            # 4. 우선순위에 없지만 활성화된 Provider도 추가 (우선순위 낮음)
            for provider_name, config in provider_map.items():
                if provider_name not in provider_priority:
                    api_key = config.get('api_key')
                    if api_key:
                        try:
                            provider = ProviderFactory.create(
                                provider_name=provider_name,
                                api_key=api_key,
                                default_model=config.get('model'),
                                timeout=config.get('timeout', default_timeout),
                            )
                            providers.append(provider)
                            
                            logger.info(
                                f"[ProviderLoader] ✓ {provider_name.upper()} provider loaded "
                                f"(not in priority list, added at end)"
                            )
                        except Exception as e:
                            logger.error(
                                f"[ProviderLoader] Failed to create {provider_name} "
                                f"provider: {e}",
                                exc_info=True
                            )
        else:
            logger.warning("[ProviderLoader] No AI settings found in database")
            
    except Exception as e:
        logger.error(
            f"[ProviderLoader] Error loading providers from database: {e}",
            exc_info=True
        )
    
    # 5. Fallback to environment variables if enabled and no providers loaded
    if not providers and fallback_to_env:
        logger.warning(
            "[ProviderLoader] No providers loaded from DB, falling back to "
            "environment variables"
        )
        providers = _load_providers_from_env()
    
    # 6. Validation
    if not providers:
        raise ValueError(
            "No AI providers are configured. Please configure providers in "
            "database settings or environment variables."
        )
    
    logger.info(
        f"[ProviderLoader] Successfully loaded {len(providers)} provider(s): "
        f"{[p.provider_name for p in providers]}"
    )
    
    return providers


def _load_providers_from_env() -> List[AIProvider]:
    """
    환경 변수에서 Provider 설정 로드 (폴백용)
    
    Returns:
        List[AIProvider]: Provider 인스턴스 리스트
    """
    from src.core.config import settings
    
    providers = []
    
    # OpenAI Provider
    if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        try:
            openai_provider = ProviderFactory.create(
                provider_name="openai",
                api_key=settings.OPENAI_API_KEY,
                default_model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
            )
            providers.append(openai_provider)
            logger.info("[ProviderLoader] ✓ OpenAI provider loaded from env")
        except Exception as e:
            logger.error(f"[ProviderLoader] Failed to create OpenAI provider: {e}")
    
    # Anthropic Provider
    if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
        try:
            anthropic_provider = ProviderFactory.create(
                provider_name="anthropic",
                api_key=settings.ANTHROPIC_API_KEY,
                default_model=getattr(
                    settings, 
                    'ANTHROPIC_MODEL', 
                    'claude-3-5-sonnet-20241022'
                ),
            )
            providers.append(anthropic_provider)
            logger.info("[ProviderLoader] ✓ Anthropic provider loaded from env")
        except Exception as e:
            logger.error(f"[ProviderLoader] Failed to create Anthropic provider: {e}")
    
    # Gemini Provider
    if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
        try:
            gemini_provider = ProviderFactory.create(
                provider_name="gemini",
                api_key=settings.GEMINI_API_KEY,
                default_model=getattr(
                    settings, 
                    'GEMINI_MODEL', 
                    'gemini-2.0-flash-exp'
                ),
            )
            providers.append(gemini_provider)
            logger.info("[ProviderLoader] ✓ Gemini provider loaded from env")
        except Exception as e:
            logger.error(f"[ProviderLoader] Failed to create Gemini provider: {e}")
    
    return providers


async def get_default_timeout_from_settings(db_provider) -> int:
    """
    데이터베이스에서 기본 타임아웃 값을 가져옵니다.
    
    Args:
        db_provider: DatabaseProvider 인스턴스
        
    Returns:
        int: 기본 타임아웃 (초)
    """
    try:
        app_settings = await db_provider.get_app_settings()
        if app_settings and app_settings.get('ai'):
            return app_settings['ai'].get('default_timeout', 30)
    except Exception as e:
        logger.warning(f"[ProviderLoader] Failed to get default timeout: {e}")
    
    return 30  # Default fallback

