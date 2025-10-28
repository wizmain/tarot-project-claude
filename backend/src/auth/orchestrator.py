"""
Auth Orchestrator

멀티 Auth Provider 관리 및 fallback 처리
"""
from typing import Optional, Dict, Any, List
import logging

from src.auth.provider import AuthProvider, AuthProviderFactory
from src.auth.models import (
    AuthResponse,
    UserProfile,
    AuthTokens,
    TokenVerificationResult,
    AuthProviderError,
    AuthServiceUnavailableError,
    AuthInvalidTokenError,
    AuthTokenExpiredError
)

logger = logging.getLogger(__name__)


class AuthOrchestrator:
    """
    Auth Provider 오케스트레이터

    여러 Auth Provider를 관리하고 fallback 기능 제공

    Example:
        orchestrator = AuthOrchestrator(
            primary_provider="custom_jwt",
            fallback_providers=["firebase", "auth0"],
            configs={
                "custom_jwt": {"secret_key": "..."},
                "firebase": {"credentials_path": "..."},
                "auth0": {"domain": "...", "client_id": "...", "client_secret": "..."}
            }
        )

        # Sign up
        response = await orchestrator.sign_up(
            email="user@example.com",
            password="password123",
            display_name="User"
        )

        # Sign in
        response = await orchestrator.sign_in(
            email="user@example.com",
            password="password123"
        )

        # Verify token
        result = await orchestrator.verify_token(token)
    """

    def __init__(
        self,
        primary_provider: str,
        fallback_providers: Optional[List[str]] = None,
        configs: Optional[Dict[str, Dict[str, Any]]] = None,
        enable_fallback: bool = True
    ):
        """
        Initialize Auth Orchestrator

        Args:
            primary_provider: Primary auth provider name
            fallback_providers: List of fallback provider names
            configs: Provider configurations {provider_name: config_dict}
            enable_fallback: Enable fallback to other providers on failure
        """
        self.primary_provider_name = primary_provider
        self.fallback_provider_names = fallback_providers or []
        self.configs = configs or {}
        self.enable_fallback = enable_fallback

        # Initialize providers
        self.providers: Dict[str, AuthProvider] = {}
        self._initialize_providers()

        logger.info(
            f"[AuthOrchestrator] Initialized with primary: {primary_provider}, "
            f"fallbacks: {fallback_providers}"
        )

    def _initialize_providers(self) -> None:
        """
        Initialize all configured providers

        Raises:
            ValueError: If primary provider cannot be initialized
        """
        all_providers = [self.primary_provider_name] + self.fallback_provider_names

        for provider_name in all_providers:
            try:
                config = self.configs.get(provider_name, {})
                provider = AuthProviderFactory.create(provider_name, config)
                self.providers[provider_name] = provider
                logger.info(f"[AuthOrchestrator] Initialized provider: {provider_name}")

            except Exception as e:
                error_msg = f"Failed to initialize provider '{provider_name}': {str(e)}"

                # Primary provider failure is critical
                if provider_name == self.primary_provider_name:
                    logger.error(f"[AuthOrchestrator] {error_msg}")
                    raise ValueError(error_msg)

                # Fallback provider failure is just a warning
                logger.warning(f"[AuthOrchestrator] {error_msg}")

    def get_primary_provider(self) -> AuthProvider:
        """
        Get primary auth provider

        Returns:
            Primary AuthProvider instance

        Raises:
            ValueError: If primary provider not initialized
        """
        if self.primary_provider_name not in self.providers:
            raise ValueError(f"Primary provider '{self.primary_provider_name}' not initialized")

        return self.providers[self.primary_provider_name]

    def get_provider(self, provider_name: str) -> Optional[AuthProvider]:
        """
        Get specific auth provider

        Args:
            provider_name: Provider name

        Returns:
            AuthProvider instance or None if not initialized
        """
        return self.providers.get(provider_name)

    def list_available_providers(self) -> List[str]:
        """
        Get list of available providers

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    async def sign_up(
        self,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> AuthResponse:
        """
        Sign up with email and password

        Args:
            email: Email address
            password: Password
            display_name: Display name (optional)
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            AuthResponse with user profile and tokens

        Raises:
            AuthProviderError: If sign up fails
        """
        # Use specific provider if requested
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].sign_up(
                email=email,
                password=password,
                display_name=display_name,
                **kwargs
            )

        # Try primary provider
        try:
            primary_provider = self.get_primary_provider()
            return await primary_provider.sign_up(
                email=email,
                password=password,
                display_name=display_name,
                **kwargs
            )

        except AuthServiceUnavailableError as e:
            if not self.enable_fallback:
                raise

            logger.warning(
                f"[AuthOrchestrator] Primary provider unavailable, trying fallbacks: {e}"
            )

            # Try fallback providers
            for fallback_name in self.fallback_provider_names:
                if fallback_name not in self.providers:
                    continue

                try:
                    fallback_provider = self.providers[fallback_name]
                    logger.info(f"[AuthOrchestrator] Trying fallback: {fallback_name}")

                    return await fallback_provider.sign_up(
                        email=email,
                        password=password,
                        display_name=display_name,
                        **kwargs
                    )

                except AuthServiceUnavailableError:
                    continue
                except Exception as fallback_error:
                    logger.error(
                        f"[AuthOrchestrator] Fallback {fallback_name} failed: {fallback_error}"
                    )
                    continue

            # All providers failed
            raise AuthProviderError(
                "All auth providers unavailable",
                provider="orchestrator",
                error_type="ALL_PROVIDERS_FAILED"
            )

    async def sign_in(
        self,
        email: str,
        password: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> AuthResponse:
        """
        Sign in with email and password

        Args:
            email: Email address
            password: Password
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            AuthResponse with user profile and tokens

        Raises:
            AuthProviderError: If sign in fails
        """
        # Use specific provider if requested
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].sign_in(
                email=email,
                password=password,
                **kwargs
            )

        # Try primary provider
        try:
            primary_provider = self.get_primary_provider()
            return await primary_provider.sign_in(
                email=email,
                password=password,
                **kwargs
            )

        except AuthServiceUnavailableError as e:
            if not self.enable_fallback:
                raise

            logger.warning(
                f"[AuthOrchestrator] Primary provider unavailable, trying fallbacks: {e}"
            )

            # Try fallback providers
            for fallback_name in self.fallback_provider_names:
                if fallback_name not in self.providers:
                    continue

                try:
                    fallback_provider = self.providers[fallback_name]
                    logger.info(f"[AuthOrchestrator] Trying fallback: {fallback_name}")

                    return await fallback_provider.sign_in(
                        email=email,
                        password=password,
                        **kwargs
                    )

                except AuthServiceUnavailableError:
                    continue
                except Exception as fallback_error:
                    logger.error(
                        f"[AuthOrchestrator] Fallback {fallback_name} failed: {fallback_error}"
                    )
                    continue

            # All providers failed
            raise AuthProviderError(
                "All auth providers unavailable",
                provider="orchestrator",
                error_type="ALL_PROVIDERS_FAILED"
            )

    async def sign_out(
        self,
        token: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Sign out user

        Args:
            token: Access token
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            bool: Success status
        """
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].sign_out(token, **kwargs)

        primary_provider = self.get_primary_provider()
        return await primary_provider.sign_out(token, **kwargs)

    async def verify_token(
        self,
        token: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> TokenVerificationResult:
        """
        Verify token with automatic fallback support

        Args:
            token: Token to verify
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            TokenVerificationResult with provider info
        """
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            result = await self.providers[provider].verify_token(token, **kwargs)
            result.provider = provider
            return result

        # Try primary provider first
        try:
            primary_provider = self.get_primary_provider()
            result = await primary_provider.verify_token(token, **kwargs)
            result.provider = self.primary_provider_name
            return result
        except (AuthInvalidTokenError, AuthTokenExpiredError) as e:
            # If primary fails with invalid/expired token, try fallbacks
            if not self.enable_fallback:
                raise

            logger.info(
                f"[AuthOrchestrator] Primary token verification failed, trying fallbacks: {e}"
            )

            # Try fallback providers
            for fallback_name in self.fallback_provider_names:
                if fallback_name not in self.providers:
                    continue

                try:
                    fallback_provider = self.providers[fallback_name]
                    logger.info(f"[AuthOrchestrator] Trying fallback verification: {fallback_name}")

                    result = await fallback_provider.verify_token(token, **kwargs)
                    result.provider = fallback_name
                    logger.info(f"[AuthOrchestrator] Token verified with fallback: {fallback_name}")
                    return result

                except (AuthInvalidTokenError, AuthTokenExpiredError):
                    continue
                except Exception as fallback_error:
                    logger.error(
                        f"[AuthOrchestrator] Fallback {fallback_name} verification error: {fallback_error}"
                    )
                    continue

            # All providers failed - re-raise original exception
            raise

    async def refresh_token(
        self,
        refresh_token: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> AuthTokens:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            New AuthTokens
        """
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].refresh_token(refresh_token, **kwargs)

        primary_provider = self.get_primary_provider()
        return await primary_provider.refresh_token(refresh_token, **kwargs)

    async def get_user(
        self,
        user_id: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """
        Get user by ID

        Args:
            user_id: User ID
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            UserProfile
        """
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].get_user(user_id, **kwargs)

        primary_provider = self.get_primary_provider()
        return await primary_provider.get_user(user_id, **kwargs)

    async def update_user(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """
        Update user information

        Args:
            user_id: User ID
            display_name: New display name (optional)
            photo_url: New photo URL (optional)
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            Updated UserProfile
        """
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].update_user(
                user_id=user_id,
                display_name=display_name,
                photo_url=photo_url,
                **kwargs
            )

        primary_provider = self.get_primary_provider()
        return await primary_provider.update_user(
            user_id=user_id,
            display_name=display_name,
            photo_url=photo_url,
            **kwargs
        )

    async def delete_user(
        self,
        user_id: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Delete user

        Args:
            user_id: User ID
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            bool: Success status
        """
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].delete_user(user_id, **kwargs)

        primary_provider = self.get_primary_provider()
        return await primary_provider.delete_user(user_id, **kwargs)

    async def reset_password(
        self,
        email: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send password reset email

        Args:
            email: Email address
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            bool: Success status
        """
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].reset_password(email, **kwargs)

        primary_provider = self.get_primary_provider()
        return await primary_provider.reset_password(email, **kwargs)

    async def confirm_password_reset(
        self,
        reset_code: str,
        new_password: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Confirm password reset and change password

        Args:
            reset_code: Password reset code/token from provider
            new_password: New password
            provider: Specific provider to use (optional, defaults to primary)
            **kwargs: Additional provider-specific parameters

        Returns:
            bool: Success status

        Raises:
            AuthInvalidTokenError: Invalid reset code
            AuthTokenExpiredError: Expired reset code
        """
        if provider:
            if provider not in self.providers:
                raise ValueError(f"Provider '{provider}' not available")
            return await self.providers[provider].confirm_password_reset(
                reset_code=reset_code,
                new_password=new_password,
                **kwargs
            )

        primary_provider = self.get_primary_provider()
        return await primary_provider.confirm_password_reset(
            reset_code=reset_code,
            new_password=new_password,
            **kwargs
        )

    def get_provider_metadata(self) -> Dict[str, Any]:
        """
        Get metadata for all providers

        Returns:
            Dictionary with provider metadata
        """
        metadata = {
            "primary_provider": self.primary_provider_name,
            "fallback_providers": self.fallback_provider_names,
            "enable_fallback": self.enable_fallback,
            "providers": {}
        }

        for provider_name, provider in self.providers.items():
            metadata["providers"][provider_name] = provider.get_metadata()

        return metadata
