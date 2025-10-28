"""
Auth API Routes - 인증 및 회원가입 API 엔드포인트

이 모듈의 목적:
- 사용자 인증 및 회원가입 API 엔드포인트 제공
- Auth Provider를 통한 다양한 인증 방식 지원
- JWT 토큰 기반 인증 구현
- 사용자 프로필 관리

주요 엔드포인트:
- POST /api/v1/auth/signup: 회원가입
- POST /api/v1/auth/login: 로그인
- POST /api/v1/auth/logout: 로그아웃
- POST /api/v1/auth/refresh: 토큰 갱신
- GET /api/v1/auth/me: 현재 사용자 정보 조회
- PUT /api/v1/auth/me: 사용자 정보 수정
- POST /api/v1/auth/password-reset: 비밀번호 재설정 요청
- POST /api/v1/auth/password-reset/confirm: 비밀번호 재설정 확인

인증 플로우:
1. 회원가입/로그인: SignUpRequest/LoginRequest 검증
2. Auth Provider를 통한 인증 처리
3. User 데이터베이스에 저장/조회
4. JWT 토큰 발급 (access_token, refresh_token)
5. TokenResponse 반환

구현 사항:
- FastAPI의 Depends를 사용한 의존성 주입
- 상세한 에러 핸들링 및 로깅
- HTTP 상태 코드 적절히 사용 (200, 201, 400, 401, 403, 404, 500)
- Swagger UI용 상세한 docstring

사용 예시:
    # 회원가입
    POST /api/v1/auth/signup
    {
        "email": "user@example.com",
        "password": "securePassword123!",
        "display_name": "홍길동"
    }

    # 로그인
    POST /api/v1/auth/login
    {
        "email": "user@example.com",
        "password": "securePassword123!"
    }
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.logging import get_logger
from src.auth import AuthOrchestrator
from src.auth.models import (
    AuthProviderError,
    AuthInvalidCredentialsError,
    AuthEmailAlreadyExistsError,
    AuthUserNotFoundError,
    AuthInvalidTokenError,
    AuthTokenExpiredError,
    AuthWeakPasswordError,
)
from src.api.dependencies.auth import (
    get_auth_orchestrator,
    get_current_user,
    get_current_active_user,
)
from src.api.repositories.user_repository import UserRepository
from src.models import User
from src.schemas.user import (
    SignUpRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
    UserWithStats,
    PasswordResetRequest,
    PasswordResetConfirm,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(
    request: SignUpRequest,
    db: Session = Depends(get_db),
    orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)
):
    """
    회원가입

    새로운 사용자 계정을 생성하고 인증 토큰을 발급합니다.
    Auth Provider를 통해 인증 정보를 생성하고, 데이터베이스에 사용자를 저장합니다.

    Args:
        request: 회원가입 요청 데이터
            - email: 이메일 주소 (필수)
            - password: 비밀번호 (6자 이상, 필수)
            - display_name: 표시 이름 (선택)
            - provider: 특정 Provider 지정 (선택, 기본값: custom_jwt)
        db: 데이터베이스 세션
        orchestrator: Auth Orchestrator

    Returns:
        TokenResponse: 토큰 및 사용자 정보

    Raises:
        HTTPException 400: 이미 존재하는 이메일
        HTTPException 500: 서버 에러
    """
    logger.info(f"[Signup] 회원가입 요청: email={request.email}")

    try:
        # 이메일 중복 확인
        existing_user = UserRepository.get_by_email(db, request.email)
        if existing_user:
            logger.warning(f"[Signup] 이미 존재하는 이메일: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 이메일입니다"
            )

        # Auth Provider를 통한 회원가입
        auth_response = await orchestrator.sign_up(
            email=request.email,
            password=request.password,
            display_name=request.display_name,
            provider=request.provider
        )

        logger.info(
            f"[Signup] Auth Provider 회원가입 성공: "
            f"email={request.email}, provider={auth_response.provider}"
        )

        # 데이터베이스에 사용자 저장 (password_hash 포함)
        password_hash = auth_response.user.metadata.get("password_hash") if auth_response.user.metadata else None
        user = UserRepository.create(
            db=db,
            email=auth_response.user.email,
            provider_id=auth_response.provider,
            provider_user_id=auth_response.user.uid,
            display_name=auth_response.user.display_name,
            photo_url=auth_response.user.photo_url,
            phone_number=auth_response.user.phone_number,
            email_verified=auth_response.user.email_verified,
            user_metadata=auth_response.user.metadata,
            password_hash=password_hash
        )
        db.commit()
        db.refresh(user)

        logger.info(f"[Signup] 사용자 생성 완료: user_id={user.id}, email={user.email}")

        # 응답 생성
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            phone_number=user.phone_number,
            provider_id=user.provider_id,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        return TokenResponse(
            access_token=auth_response.tokens.access_token,
            refresh_token=auth_response.tokens.refresh_token,
            token_type=auth_response.tokens.token_type,
            expires_in=auth_response.tokens.expires_in,
            user=user_response
        )

    except HTTPException:
        db.rollback()
        raise

    except AuthEmailAlreadyExistsError as e:
        logger.warning(f"[Signup] Auth Provider에서 중복 사용자 감지: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자입니다"
        )

    except AuthProviderError as e:
        logger.error(f"[Signup] Auth Provider 에러: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
        )

    except Exception as e:
        logger.error(f"[Signup] 회원가입 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)
):
    """
    로그인

    이메일과 비밀번호로 로그인하고 인증 토큰을 발급합니다.

    Args:
        request: 로그인 요청 데이터
            - email: 이메일 주소 (필수)
            - password: 비밀번호 (필수)
            - provider: 특정 Provider 지정 (선택, 기본값: custom_jwt)
        db: 데이터베이스 세션
        orchestrator: Auth Orchestrator

    Returns:
        TokenResponse: 토큰 및 사용자 정보

    Raises:
        HTTPException 401: 잘못된 이메일 또는 비밀번호
        HTTPException 500: 서버 에러
    """
    logger.info(f"[Login] 로그인 요청: email={request.email}")

    try:
        # Auth Provider를 통한 로그인
        auth_response = await orchestrator.sign_in(
            email=request.email,
            password=request.password,
            provider=request.provider
        )

        logger.info(
            f"[Login] Auth Provider 로그인 성공: "
            f"email={request.email}, provider={auth_response.provider}"
        )

        # 데이터베이스에서 사용자 조회 또는 생성
        user = UserRepository.get_by_provider(
            db=db,
            provider_id=auth_response.provider,
            provider_user_id=auth_response.user.uid
        )

        if not user:
            # Provider에는 존재하지만 DB에 없는 경우 (신규 사용자)
            logger.info(
                f"[Login] DB에 사용자 없음, 생성: "
                f"email={request.email}, provider={auth_response.provider}"
            )
            user = UserRepository.create(
                db=db,
                email=auth_response.user.email,
                provider_id=auth_response.provider,
                provider_user_id=auth_response.user.uid,
                display_name=auth_response.user.display_name,
                photo_url=auth_response.user.photo_url,
                phone_number=auth_response.user.phone_number,
                email_verified=auth_response.user.email_verified,
                user_metadata=auth_response.user.metadata
            )

        # 마지막 로그인 시간 업데이트
        UserRepository.update_last_login(db, user.id)
        db.commit()
        db.refresh(user)

        logger.info(f"[Login] 로그인 완료: user_id={user.id}, email={user.email}")

        # 응답 생성
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            phone_number=user.phone_number,
            provider_id=user.provider_id,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        return TokenResponse(
            access_token=auth_response.tokens.access_token,
            refresh_token=auth_response.tokens.refresh_token,
            token_type=auth_response.tokens.token_type,
            expires_in=auth_response.tokens.expires_in,
            user=user_response
        )

    except AuthInvalidCredentialsError as e:
        logger.warning(f"[Login] 잘못된 인증 정보: email={request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )

    except AuthUserNotFoundError as e:
        logger.warning(f"[Login] 사용자를 찾을 수 없음: email={request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )

    except AuthProviderError as e:
        logger.error(f"[Login] Auth Provider 에러: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 처리 중 오류가 발생했습니다: {str(e)}"
        )

    except Exception as e:
        logger.error(f"[Login] 로그인 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)
):
    """
    로그아웃

    현재 사용자를 로그아웃합니다.
    Auth Provider에 따라 토큰 무효화 또는 세션 종료를 수행합니다.

    Args:
        current_user: 현재 로그인한 사용자
        orchestrator: Auth Orchestrator

    Returns:
        dict: 로그아웃 성공 메시지

    Raises:
        HTTPException 500: 서버 에러
    """
    logger.info(f"[Logout] 로그아웃 요청: user_id={current_user.id}")

    try:
        # Auth Provider를 통한 로그아웃
        await orchestrator.sign_out(
            user_id=current_user.provider_user_id,
            provider=current_user.provider_id
        )

        logger.info(f"[Logout] 로그아웃 완료: user_id={current_user.id}")

        return {"message": "로그아웃되었습니다"}

    except Exception as e:
        logger.error(f"[Logout] 로그아웃 실패: {e}", exc_info=True)
        # 로그아웃 실패해도 클라이언트에서 토큰 삭제하면 되므로 200 반환
        return {"message": "로그아웃되었습니다"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)
):
    """
    토큰 갱신

    Refresh Token을 사용하여 새로운 Access Token을 발급받습니다.

    Args:
        refresh_token: Refresh Token (필수)
        db: 데이터베이스 세션
        orchestrator: Auth Orchestrator

    Returns:
        TokenResponse: 새로운 토큰 및 사용자 정보

    Raises:
        HTTPException 401: 유효하지 않은 Refresh Token
        HTTPException 500: 서버 에러
    """
    logger.info("[RefreshToken] 토큰 갱신 요청")

    try:
        # Auth Provider를 통한 토큰 갱신
        auth_response = await orchestrator.refresh_token(refresh_token)

        logger.info(
            f"[RefreshToken] 토큰 갱신 성공: provider={auth_response.provider}"
        )

        # 데이터베이스에서 사용자 조회
        user = UserRepository.get_by_provider(
            db=db,
            provider_id=auth_response.provider,
            provider_user_id=auth_response.user.uid
        )

        if not user:
            logger.error(
                f"[RefreshToken] 사용자를 찾을 수 없음: "
                f"provider={auth_response.provider}, uid={auth_response.user.uid}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다"
            )

        # 응답 생성
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            phone_number=user.phone_number,
            provider_id=user.provider_id,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        return TokenResponse(
            access_token=auth_response.tokens.access_token,
            refresh_token=auth_response.tokens.refresh_token,
            token_type=auth_response.tokens.token_type,
            expires_in=auth_response.tokens.expires_in,
            user=user_response
        )

    except AuthInvalidTokenError as e:
        logger.warning(f"[RefreshToken] 유효하지 않은 Refresh Token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Refresh Token입니다"
        )

    except AuthProviderError as e:
        logger.error(f"[RefreshToken] Auth Provider 에러: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"토큰 갱신 중 오류가 발생했습니다: {str(e)}"
        )

    except Exception as e:
        logger.error(f"[RefreshToken] 토큰 갱신 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다. 다시 로그인해주세요."
        )


@router.get("/me", response_model=UserWithStats)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    현재 사용자 정보 조회

    로그인한 사용자의 프로필 정보와 리딩 통계를 조회합니다.

    Args:
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션

    Returns:
        UserWithStats: 사용자 정보 및 통계

    Raises:
        HTTPException 500: 서버 에러
    """
    logger.info(f"[GetMe] 사용자 정보 조회: user_id={current_user.id}")

    try:
        # 사용자 정보 및 통계 조회
        user_with_stats = UserRepository.get_user_with_stats(db, current_user.id)

        if not user_with_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 정보를 찾을 수 없습니다"
            )

        return UserWithStats(**user_with_stats)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[GetMe] 사용자 정보 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 조회 중 오류가 발생했습니다"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    사용자 정보 수정

    로그인한 사용자의 프로필 정보를 수정합니다.

    Args:
        update_data: 수정할 데이터
            - display_name: 표시 이름 (선택)
            - photo_url: 프로필 사진 URL (선택)
            - phone_number: 전화번호 (선택)
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션

    Returns:
        UserResponse: 수정된 사용자 정보

    Raises:
        HTTPException 500: 서버 에러
    """
    logger.info(f"[UpdateMe] 사용자 정보 수정 요청: user_id={current_user.id}")

    try:
        # 수정할 데이터 추출 (None이 아닌 값만)
        update_dict = update_data.model_dump(exclude_unset=True)

        # 사용자 정보 업데이트
        updated_user = UserRepository.update(
            db=db,
            user_id=current_user.id,
            **update_dict
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 정보를 찾을 수 없습니다"
            )

        db.commit()
        db.refresh(updated_user)

        logger.info(f"[UpdateMe] 사용자 정보 수정 완료: user_id={current_user.id}")

        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            display_name=updated_user.display_name,
            photo_url=updated_user.photo_url,
            phone_number=updated_user.phone_number,
            provider_id=updated_user.provider_id,
            email_verified=updated_user.email_verified,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            last_login_at=updated_user.last_login_at
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        logger.error(f"[UpdateMe] 사용자 정보 수정 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 수정 중 오류가 발생했습니다"
        )


@router.post("/password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)
):
    """
    비밀번호 재설정 요청

    이메일 주소로 비밀번호 재설정 링크를 전송합니다.

    Args:
        request: 비밀번호 재설정 요청 데이터
            - email: 이메일 주소 (필수)
        orchestrator: Auth Orchestrator

    Returns:
        dict: 성공 메시지

    Raises:
        HTTPException 500: 서버 에러
    """
    logger.info(f"[PasswordReset] 비밀번호 재설정 요청: email={request.email}")

    try:
        # Auth Provider를 통한 비밀번호 재설정 요청
        await orchestrator.reset_password(email=request.email)

        logger.info(f"[PasswordReset] 비밀번호 재설정 이메일 전송: email={request.email}")

        # 보안상 이유로 이메일 존재 여부와 무관하게 동일한 메시지 반환
        return {
            "message": "비밀번호 재설정 링크가 이메일로 전송되었습니다"
        }

    except Exception as e:
        logger.error(f"[PasswordReset] 비밀번호 재설정 요청 실패: {e}", exc_info=True)
        # 에러가 발생해도 보안상 동일한 메시지 반환
        return {
            "message": "비밀번호 재설정 링크가 이메일로 전송되었습니다"
        }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db),
    orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)
):
    """
    비밀번호 재설정 확인

    재설정 토큰을 사용하여 새 비밀번호로 변경합니다.

    Args:
        request: 비밀번호 재설정 확인 데이터
            - reset_token: 비밀번호 재설정 토큰 (필수)
            - new_password: 새 비밀번호 (6자 이상, 필수)
        db: 데이터베이스 세션
        orchestrator: Auth Orchestrator

    Returns:
        dict: 성공 메시지

    Raises:
        HTTPException 400: 유효하지 않은 토큰 또는 약한 비밀번호
        HTTPException 501: Provider가 지원하지 않는 기능
        HTTPException 500: 서버 에러
    """
    logger.info("[PasswordResetConfirm] 비밀번호 재설정 확인 요청")

    try:
        # Auth Provider를 통한 비밀번호 재설정
        success = await orchestrator.confirm_password_reset(
            reset_code=request.reset_token,
            new_password=request.new_password
        )

        if not success:
            logger.error("[PasswordResetConfirm] 비밀번호 재설정 실패")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="비밀번호 재설정 중 오류가 발생했습니다"
            )

        logger.info("[PasswordResetConfirm] 비밀번호 재설정 완료")
        return {
            "message": "비밀번호가 성공적으로 변경되었습니다"
        }

    except NotImplementedError as e:
        logger.warning(f"[PasswordResetConfirm] Provider가 지원하지 않는 기능: {e}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="현재 인증 Provider는 백엔드 비밀번호 재설정을 지원하지 않습니다. "
                   "이메일의 링크를 통해 비밀번호를 재설정하세요."
        )

    except AuthTokenExpiredError as e:
        logger.warning(f"[PasswordResetConfirm] 만료된 토큰: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호 재설정 링크가 만료되었습니다. 새로운 재설정 링크를 요청하세요."
        )

    except AuthWeakPasswordError as e:
        logger.warning(f"[PasswordResetConfirm] 약한 비밀번호: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 너무 약합니다. 더 강력한 비밀번호를 사용하세요."
        )

    except AuthInvalidTokenError as e:
        logger.warning(f"[PasswordResetConfirm] 유효하지 않은 토큰: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 재설정 토큰입니다"
        )

    except Exception as e:
        logger.error(f"[PasswordResetConfirm] 비밀번호 재설정 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 재설정 중 오류가 발생했습니다"
        )
