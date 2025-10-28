"""
Auth0 Authentication Provider

Auth0를 사용한 인증 구현
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import httpx

from src.auth.provider import AuthProvider
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


class Auth0Provider(AuthProvider):
    """
    Auth0 Authentication Provider

    Auth0를 사용한 사용자 인증 및 관리

    Configuration:
        {
            "domain": "your-tenant.auth0.com",
            "client_id": "your-client-id",
            "client_secret": "your-client-secret",
            "audience": "your-api-identifier",
            "connection": "Username-Password-Authentication"  # Optional
        }
    """

    def __init__(
        self,
        config: Dict[str, Any],
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Auth0 Provider

        Args:
            config: Auth0 configuration
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(config, timeout, max_retries)
        self.domain = config.get("domain")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.audience = config.get("audience")
        self.connection = config.get("connection", "Username-Password-Authentication")

        if not all([self.domain, self.client_id, self.client_secret]):
            raise AuthProviderError(
                "Auth0 configuration requires: domain, client_id, client_secret",
                provider=self.provider_name,
                error_type="INVALID_CONFIG"
            )

        self.base_url = f"https://{self.domain}"
        self.management_token: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "auth0"

    @property
    def supported_features(self) -> List[str]:
        return [
            "email_password",
            "oauth",
            "social_login",
            "multifactor_auth",
            "user_management",
            "password_reset"
        ]

    async def _get_management_token(self) -> str:
        """
        Get Auth0 Management API token

        Returns:
            Management API access token
        """
        if self.management_token:
            return self.management_token

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": f"{self.base_url}/api/v2/",
                    "grant_type": "client_credentials"
                }
            )

            if response.status_code != 200:
                raise AuthProviderError(
                    "Failed to get management token",
                    provider=self.provider_name,
                    error_type="AUTH_ERROR"
                )

            data = response.json()
            self.management_token = data["access_token"]
            return self.management_token

    async def sign_up(
        self,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        **kwargs
    ) -> AuthResponse:
        """
        Create a new user with email and password

        Args:
            email: Email address
            password: Password
            display_name: Display name (optional)
            **kwargs: Additional Auth0 user metadata

        Returns:
            AuthResponse with user profile and tokens
        """
        try:
            self._validate_email(email)
            self._validate_password(password, min_length=8)

            # Create user via Auth0 Management API
            token = await self._get_management_token()

            user_data = {
                "email": email,
                "password": password,
                "connection": self.connection,
                "email_verified": False
            }

            if display_name:
                user_data["name"] = display_name
                user_data["nickname"] = display_name

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v2/users",
                    json=user_data,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 409:
                    raise AuthEmailAlreadyExistsError(
                        f"Email already exists: {email}",
                        provider=self.provider_name
                    )

                if response.status_code != 201:
                    error_data = response.json()
                    if "PasswordStrengthError" in str(error_data):
                        raise AuthWeakPasswordError(
                            "Password does not meet requirements",
                            provider=self.provider_name
                        )
                    raise AuthProviderError(
                        f"Failed to create user: {error_data}",
                        provider=self.provider_name,
                        error_type="SIGN_UP_ERROR"
                    )

                auth0_user = response.json()

            # Authenticate to get tokens
            auth_response = await self.sign_in(email, password)
            auth_response.is_new_user = True

            logger.info(f"[Auth0] Created new user: {email}")
            return auth_response

        except (AuthEmailAlreadyExistsError, AuthWeakPasswordError):
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Sign up failed: {str(e)}",
                provider=self.provider_name,
                error_type="SIGN_UP_ERROR",
                original_error=e
            )

    async def sign_in(
        self,
        email: str,
        password: str,
        **kwargs
    ) -> AuthResponse:
        """
        Sign in with email and password

        Args:
            email: Email address
            password: Password
            **kwargs: Additional parameters

        Returns:
            AuthResponse with user profile and tokens
        """
        try:
            # Resource Owner Password Grant
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/oauth/token",
                    json={
                        "grant_type": "password",
                        "username": email,
                        "password": password,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "audience": self.audience,
                        "scope": "openid profile email"
                    }
                )

                if response.status_code == 403:
                    raise AuthInvalidCredentialsError(
                        "Invalid email or password",
                        provider=self.provider_name
                    )

                if response.status_code != 200:
                    error_data = response.json()
                    raise AuthProviderError(
                        f"Authentication failed: {error_data}",
                        provider=self.provider_name,
                        error_type="SIGN_IN_ERROR"
                    )

                token_data = response.json()

            # Get user info
            user_info_response = await client.get(
                f"{self.base_url}/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )

            if user_info_response.status_code != 200:
                raise AuthProviderError(
                    "Failed to get user info",
                    provider=self.provider_name,
                    error_type="USER_INFO_ERROR"
                )

            user_info = user_info_response.json()

            # Convert to UserProfile
            user_profile = UserProfile(
                uid=f"auth0_{user_info['sub']}",
                email=user_info.get('email', email),
                email_verified=user_info.get('email_verified', False),
                display_name=user_info.get('name'),
                photo_url=user_info.get('picture'),
                provider_id=self.provider_name,
                metadata=user_info
            )

            # Create tokens
            tokens = AuthTokens(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_type=token_data.get('token_type', 'Bearer'),
                expires_in=token_data.get('expires_in', 3600)
            )

            logger.info(f"[Auth0] User signed in: {email}")

            return AuthResponse(
                user=user_profile,
                tokens=tokens,
                is_new_user=False,
                provider=self.provider_name
            )

        except (AuthInvalidCredentialsError, AuthProviderError):
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Sign in failed: {str(e)}",
                provider=self.provider_name,
                error_type="SIGN_IN_ERROR",
                original_error=e
            )

    async def sign_out(self, token: str, **kwargs) -> bool:
        """
        Sign out user (invalidate session)

        Note: Auth0 doesn't have a built-in token revocation for access tokens.
        Implement logout on client side or use refresh token revocation.

        Args:
            token: Access token
            **kwargs: Additional parameters

        Returns:
            bool: Success status
        """
        logger.info("[Auth0] Sign out called (no server-side action)")
        return True

    async def verify_token(self, token: str, **kwargs) -> TokenVerificationResult:
        """
        Verify Auth0 access token

        Args:
            token: Access token
            **kwargs: Additional parameters

        Returns:
            TokenVerificationResult
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 401:
                    raise AuthInvalidTokenError(
                        "Invalid or expired token",
                        provider=self.provider_name
                    )

                if response.status_code != 200:
                    raise AuthProviderError(
                        "Token verification failed",
                        provider=self.provider_name,
                        error_type="VERIFICATION_ERROR"
                    )

                user_info = response.json()

                return TokenVerificationResult(
                    valid=True,
                    user_id=user_info['sub'],
                    email=user_info.get('email'),
                    claims=user_info
                )

        except (AuthInvalidTokenError, AuthProviderError):
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Token verification failed: {str(e)}",
                provider=self.provider_name,
                error_type="VERIFICATION_ERROR",
                original_error=e
            )

    async def refresh_token(self, refresh_token: str, **kwargs) -> AuthTokens:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token
            **kwargs: Additional parameters

        Returns:
            New AuthTokens
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/oauth/token",
                    json={
                        "grant_type": "refresh_token",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token
                    }
                )

                if response.status_code != 200:
                    raise AuthInvalidTokenError(
                        "Invalid or expired refresh token",
                        provider=self.provider_name
                    )

                token_data = response.json()

                return AuthTokens(
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token', refresh_token),
                    token_type=token_data.get('token_type', 'Bearer'),
                    expires_in=token_data.get('expires_in', 3600)
                )

        except AuthInvalidTokenError:
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Token refresh failed: {str(e)}",
                provider=self.provider_name,
                error_type="REFRESH_ERROR",
                original_error=e
            )

    async def get_user(self, user_id: str, **kwargs) -> UserProfile:
        """
        Get user by ID

        Args:
            user_id: Auth0 user ID
            **kwargs: Additional parameters

        Returns:
            UserProfile
        """
        try:
            token = await self._get_management_token()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v2/users/{user_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 404:
                    raise AuthUserNotFoundError(
                        f"User not found: {user_id}",
                        provider=self.provider_name
                    )

                if response.status_code != 200:
                    raise AuthProviderError(
                        "Failed to get user",
                        provider=self.provider_name,
                        error_type="GET_USER_ERROR"
                    )

                auth0_user = response.json()

                return self._auth0_user_to_profile(auth0_user)

        except (AuthUserNotFoundError, AuthProviderError):
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Get user failed: {str(e)}",
                provider=self.provider_name,
                error_type="GET_USER_ERROR",
                original_error=e
            )

    async def update_user(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """
        Update user information

        Args:
            user_id: Auth0 user ID
            display_name: New display name (optional)
            photo_url: New photo URL (optional)
            **kwargs: Additional Auth0 user metadata

        Returns:
            Updated UserProfile
        """
        try:
            token = await self._get_management_token()

            update_data = {}
            if display_name is not None:
                update_data["name"] = display_name
                update_data["nickname"] = display_name
            if photo_url is not None:
                update_data["picture"] = photo_url

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self.base_url}/api/v2/users/{user_id}",
                    json=update_data,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 404:
                    raise AuthUserNotFoundError(
                        f"User not found: {user_id}",
                        provider=self.provider_name
                    )

                if response.status_code != 200:
                    raise AuthProviderError(
                        "Failed to update user",
                        provider=self.provider_name,
                        error_type="UPDATE_USER_ERROR"
                    )

                auth0_user = response.json()
                logger.info(f"[Auth0] Updated user: {user_id}")

                return self._auth0_user_to_profile(auth0_user)

        except (AuthUserNotFoundError, AuthProviderError):
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Update user failed: {str(e)}",
                provider=self.provider_name,
                error_type="UPDATE_USER_ERROR",
                original_error=e
            )

    async def delete_user(self, user_id: str, **kwargs) -> bool:
        """
        Delete user

        Args:
            user_id: Auth0 user ID
            **kwargs: Additional parameters

        Returns:
            bool: Success status
        """
        try:
            token = await self._get_management_token()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/v2/users/{user_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 404:
                    raise AuthUserNotFoundError(
                        f"User not found: {user_id}",
                        provider=self.provider_name
                    )

                if response.status_code != 204:
                    raise AuthProviderError(
                        "Failed to delete user",
                        provider=self.provider_name,
                        error_type="DELETE_USER_ERROR"
                    )

                logger.info(f"[Auth0] Deleted user: {user_id}")
                return True

        except (AuthUserNotFoundError, AuthProviderError):
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Delete user failed: {str(e)}",
                provider=self.provider_name,
                error_type="DELETE_USER_ERROR",
                original_error=e
            )

    async def reset_password(self, email: str, **kwargs) -> bool:
        """
        Send password reset email

        Args:
            email: Email address
            **kwargs: Additional parameters

        Returns:
            bool: Success status
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/dbconnections/change_password",
                    json={
                        "client_id": self.client_id,
                        "email": email,
                        "connection": self.connection
                    }
                )

                if response.status_code != 200:
                    error_data = response.json()
                    raise AuthProviderError(
                        f"Failed to send password reset email: {error_data}",
                        provider=self.provider_name,
                        error_type="RESET_PASSWORD_ERROR"
                    )

                logger.info(f"[Auth0] Password reset email sent to: {email}")
                return True

        except AuthProviderError:
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Reset password failed: {str(e)}",
                provider=self.provider_name,
                error_type="RESET_PASSWORD_ERROR",
                original_error=e
            )

    async def confirm_password_reset(
        self,
        reset_code: str,
        new_password: str,
        **kwargs
    ) -> bool:
        """
        Confirm password reset - Not supported by Auth0 backend

        Auth0 handles password reset through their Universal Login page.
        Users receive an email with a link that redirects to Auth0's hosted page
        where they can reset their password directly.

        This method is not needed for Auth0's password reset flow.

        Args:
            reset_code: Not used
            new_password: Not used
            **kwargs: Not used

        Raises:
            NotImplementedError: Auth0 handles this through Universal Login
        """
        raise NotImplementedError(
            "Auth0 handles password reset through Universal Login page. "
            "The password reset email contains a link to Auth0's hosted page "
            "where users can change their password directly. "
            "No backend confirmation endpoint is needed."
        )

    def _auth0_user_to_profile(self, auth0_user: Dict[str, Any]) -> UserProfile:
        """
        Convert Auth0 user to UserProfile

        Args:
            auth0_user: Auth0 user object

        Returns:
            UserProfile
        """
        return UserProfile(
            uid=f"auth0_{auth0_user['user_id']}",
            email=auth0_user.get('email'),
            email_verified=auth0_user.get('email_verified', False),
            display_name=auth0_user.get('name'),
            photo_url=auth0_user.get('picture'),
            phone_number=auth0_user.get('phone_number'),
            provider_id=self.provider_name,
            created_at=datetime.fromisoformat(auth0_user['created_at'].replace('Z', '+00:00')) if auth0_user.get('created_at') else None,
            last_login_at=datetime.fromisoformat(auth0_user['last_login'].replace('Z', '+00:00')) if auth0_user.get('last_login') else None,
            metadata=auth0_user
        )
