"""
Auth Provider 기본 클래스 및 인터페이스 모듈

이 모듈의 목적:
- 모든 Auth Provider의 공통 인터페이스 정의
- Firebase, Auth0, Custom JWT 등 다양한 인증 서비스 통합 지원
- 일관된 에러 핸들링 및 재시도 로직
- 사용자 인증, 회원가입, 토큰 검증 등의 기능 제공

구현해야 하는 주요 메서드:
- sign_up(): 사용자 회원가입
- sign_in(): 사용자 로그인
- sign_out(): 로그아웃
- verify_token(): 토큰 검증
- refresh_token(): 토큰 갱신
- get_user(): 사용자 정보 조회
- update_user(): 사용자 정보 수정
- delete_user(): 사용자 삭제
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging

from src.auth.models import (
    AuthResponse,
    UserProfile,
    AuthTokens,
    TokenVerificationResult,
    AuthProviderError,
    AuthInvalidCredentialsError,
    AuthUserNotFoundError,
    AuthEmailAlreadyExistsError,
    AuthWeakPasswordError,
    AuthInvalidTokenError,
    AuthTokenExpiredError,
    AuthServiceUnavailableError
)

logger = logging.getLogger(__name__)


class AuthProvider(ABC):
    """
    Auth Provider 추상 베이스 클래스

    모든 Auth Provider(Firebase, Auth0, Custom JWT 등)가 상속받아야 하는 인터페이스입니다.
    이를 통해 Provider 간 일관된 API를 제공하고 교체 가능성을 보장합니다.

    구현 예시:
        class MyAuthProvider(AuthProvider):
            async def sign_up(self, email, password, **kwargs):
                # 구현
                pass

            async def sign_in(self, email, password, **kwargs):
                # 구현
                pass
    """

    def __init__(
        self,
        config: Dict[str, Any],
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Auth provider

        Args:
            config: Provider-specific configuration
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries
        self._validate_config()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Provider name (e.g., 'firebase', 'auth0', 'custom_jwt')

        Returns:
            Provider identifier string
        """
        pass

    @property
    @abstractmethod
    def supported_features(self) -> List[str]:
        """
        List of supported authentication features

        Returns:
            List of feature names (e.g., ['email_password', 'oauth', 'phone'])
        """
        pass

    @abstractmethod
    async def sign_up(
        self,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        **kwargs
    ) -> AuthResponse:
        """
        회원가입

        Args:
            email: 이메일 주소
            password: 비밀번호
            display_name: 표시 이름 (선택)
            **kwargs: Provider별 추가 파라미터

        Returns:
            AuthResponse: 인증 응답 (사용자 정보 + 토큰)

        Raises:
            AuthEmailAlreadyExistsError: 이메일이 이미 존재
            AuthWeakPasswordError: 비밀번호가 너무 약함
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def sign_in(
        self,
        email: str,
        password: str,
        **kwargs
    ) -> AuthResponse:
        """
        로그인

        Args:
            email: 이메일 주소
            password: 비밀번호
            **kwargs: Provider별 추가 파라미터

        Returns:
            AuthResponse: 인증 응답 (사용자 정보 + 토큰)

        Raises:
            AuthInvalidCredentialsError: 잘못된 인증 정보
            AuthUserNotFoundError: 사용자를 찾을 수 없음
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def sign_out(self, token: str, **kwargs) -> bool:
        """
        로그아웃

        Args:
            token: 액세스 토큰
            **kwargs: Provider별 추가 파라미터

        Returns:
            bool: 성공 여부

        Raises:
            AuthInvalidTokenError: 유효하지 않은 토큰
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def verify_token(self, token: str, **kwargs) -> TokenVerificationResult:
        """
        토큰 검증

        Args:
            token: 검증할 토큰
            **kwargs: Provider별 추가 파라미터

        Returns:
            TokenVerificationResult: 검증 결과

        Raises:
            AuthInvalidTokenError: 유효하지 않은 토큰
            AuthTokenExpiredError: 만료된 토큰
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str, **kwargs) -> AuthTokens:
        """
        토큰 갱신

        Args:
            refresh_token: 리프레시 토큰
            **kwargs: Provider별 추가 파라미터

        Returns:
            AuthTokens: 새로운 토큰

        Raises:
            AuthInvalidTokenError: 유효하지 않은 리프레시 토큰
            AuthTokenExpiredError: 만료된 리프레시 토큰
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def get_user(self, user_id: str, **kwargs) -> UserProfile:
        """
        사용자 정보 조회

        Args:
            user_id: 사용자 ID
            **kwargs: Provider별 추가 파라미터

        Returns:
            UserProfile: 사용자 프로필

        Raises:
            AuthUserNotFoundError: 사용자를 찾을 수 없음
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def update_user(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """
        사용자 정보 수정

        Args:
            user_id: 사용자 ID
            display_name: 새 표시 이름 (선택)
            photo_url: 새 프로필 사진 URL (선택)
            **kwargs: Provider별 추가 파라미터

        Returns:
            UserProfile: 업데이트된 사용자 프로필

        Raises:
            AuthUserNotFoundError: 사용자를 찾을 수 없음
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def delete_user(self, user_id: str, **kwargs) -> bool:
        """
        사용자 삭제

        Args:
            user_id: 사용자 ID
            **kwargs: Provider별 추가 파라미터

        Returns:
            bool: 성공 여부

        Raises:
            AuthUserNotFoundError: 사용자를 찾을 수 없음
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def reset_password(self, email: str, **kwargs) -> bool:
        """
        비밀번호 재설정 이메일 발송

        Args:
            email: 이메일 주소
            **kwargs: Provider별 추가 파라미터

        Returns:
            bool: 성공 여부

        Raises:
            AuthUserNotFoundError: 사용자를 찾을 수 없음
            AuthProviderError: 기타 에러
        """
        pass

    @abstractmethod
    async def confirm_password_reset(
        self,
        reset_code: str,
        new_password: str,
        **kwargs
    ) -> bool:
        """
        비밀번호 재설정 확인 및 변경

        Provider가 발급한 재설정 코드를 검증하고 비밀번호를 변경합니다.

        Args:
            reset_code: Provider가 발급한 재설정 코드/토큰
            new_password: 새 비밀번호
            **kwargs: Provider별 추가 파라미터

        Returns:
            bool: 성공 여부

        Raises:
            AuthInvalidTokenError: 유효하지 않은 코드
            AuthTokenExpiredError: 만료된 코드
            AuthProviderError: 기타 에러
        """
        pass

    def _validate_config(self) -> None:
        """
        설정 검증

        Raises:
            AuthProviderError: 설정이 유효하지 않음
        """
        if not self.config:
            raise AuthProviderError(
                "Configuration is empty",
                provider=self.provider_name,
                error_type="INVALID_CONFIG"
            )

    def _validate_email(self, email: str) -> None:
        """
        이메일 형식 검증

        Args:
            email: 이메일 주소

        Raises:
            AuthProviderError: 이메일 형식이 유효하지 않음
        """
        if not email or '@' not in email:
            raise AuthProviderError(
                "Invalid email format",
                provider=self.provider_name,
                error_type="INVALID_EMAIL"
            )

    def _validate_password(self, password: str, min_length: int = 6) -> None:
        """
        비밀번호 강도 검증

        Args:
            password: 비밀번호
            min_length: 최소 길이

        Raises:
            AuthWeakPasswordError: 비밀번호가 너무 약함
        """
        if not password or len(password) < min_length:
            raise AuthWeakPasswordError(
                f"Password must be at least {min_length} characters long",
                provider=self.provider_name
            )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name})"

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get provider metadata

        Returns:
            Dictionary with provider information
        """
        return {
            "provider": self.provider_name,
            "supported_features": self.supported_features,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }


class AuthProviderFactory:
    """
    Factory for creating Auth provider instances
    """

    _providers: Dict[str, type] = {}

    @classmethod
    def register(cls, provider_name: str, provider_class: type):
        """
        Register a provider class

        Args:
            provider_name: Provider identifier
            provider_class: Provider class (must inherit from AuthProvider)
        """
        if not issubclass(provider_class, AuthProvider):
            raise TypeError(f"{provider_class} must inherit from AuthProvider")

        cls._providers[provider_name] = provider_class
        logger.info(f"Registered Auth provider: {provider_name}")

    @classmethod
    def create(
        cls,
        provider_name: str,
        config: Dict[str, Any],
        **kwargs
    ) -> AuthProvider:
        """
        Create a provider instance

        Args:
            provider_name: Provider identifier (e.g., 'firebase', 'auth0')
            config: Provider-specific configuration
            **kwargs: Additional provider-specific arguments

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is not registered
        """
        if provider_name not in cls._providers:
            available = ', '.join(cls._providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not registered. "
                f"Available providers: {available}"
            )

        provider_class = cls._providers[provider_name]
        return provider_class(config=config, **kwargs)

    @classmethod
    def list_providers(cls) -> List[str]:
        """
        Get list of registered providers

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())
