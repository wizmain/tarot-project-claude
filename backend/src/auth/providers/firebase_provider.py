"""
Firebase Authentication Provider

Firebase Authentication을 사용한 인증 구현
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import httpx

try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

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


class FirebaseAuthProvider(AuthProvider):
    """
    Firebase Authentication Provider

    Firebase를 사용한 사용자 인증 및 관리

    Configuration:
        {
            "credentials_path": "path/to/serviceAccountKey.json",
            "project_id": "your-project-id"
        }
    """

    def __init__(
        self,
        config: Dict[str, Any],
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Firebase Auth Provider

        Args:
            config: Firebase configuration
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        if not FIREBASE_AVAILABLE:
            raise AuthProviderError(
                "Firebase Admin SDK not installed. Install with: pip install firebase-admin",
                provider="firebase",
                error_type="DEPENDENCY_MISSING"
            )

        super().__init__(config, timeout, max_retries)
        self.api_key = config.get("api_key")  # Firebase Web API Key for REST API
        self._initialize_firebase()

    @property
    def provider_name(self) -> str:
        return "firebase"

    @property
    def supported_features(self) -> List[str]:
        return [
            "email_password",
            "email_verification",
            "password_reset",
            "custom_tokens",
            "user_management"
        ]

    def _initialize_firebase(self) -> None:
        """
        Initialize Firebase Admin SDK

        Raises:
            AuthProviderError: If initialization fails
        """
        try:
            # Check if already initialized
            try:
                firebase_admin.get_app()
                logger.info("[Firebase] Using existing Firebase app")
                return
            except ValueError:
                pass

            # Initialize new app
            if "credentials_path" in self.config:
                cred = credentials.Certificate(self.config["credentials_path"])
                firebase_admin.initialize_app(cred)
                logger.info("[Firebase] Initialized with service account")
            else:
                # Use default credentials (for Cloud Run, etc.)
                firebase_admin.initialize_app()
                logger.info("[Firebase] Initialized with default credentials")

        except Exception as e:
            raise AuthProviderError(
                f"Failed to initialize Firebase: {str(e)}",
                provider=self.provider_name,
                error_type="INITIALIZATION_ERROR",
                original_error=e
            )

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
            **kwargs: Additional Firebase user properties

        Returns:
            AuthResponse with user profile and tokens

        Raises:
            AuthEmailAlreadyExistsError: Email already exists
            AuthWeakPasswordError: Password is too weak
        """
        try:
            self._validate_email(email)
            self._validate_password(password)

            # Create user in Firebase
            user_args = {
                "email": email,
                "password": password,
                "email_verified": False
            }

            if display_name:
                user_args["display_name"] = display_name

            firebase_user = firebase_auth.create_user(**user_args)

            # Create custom token for immediate login
            custom_token = firebase_auth.create_custom_token(firebase_user.uid)

            # Get user profile
            user_profile = await self._firebase_user_to_profile(firebase_user)

            # Create tokens
            tokens = AuthTokens(
                access_token=custom_token.decode('utf-8'),
                refresh_token=None,  # Firebase handles refresh internally
                token_type="Bearer",
                expires_in=3600  # 1 hour
            )

            logger.info(f"[Firebase] Created new user: {email}")

            return AuthResponse(
                user=user_profile,
                tokens=tokens,
                is_new_user=True,
                provider=self.provider_name
            )

        except firebase_auth.EmailAlreadyExistsError as e:
            raise AuthEmailAlreadyExistsError(
                f"Email already exists: {email}",
                provider=self.provider_name,
                original_error=e
            )
        except Exception as e:
            if "WEAK_PASSWORD" in str(e):
                raise AuthWeakPasswordError(
                    "Password is too weak",
                    provider=self.provider_name,
                    original_error=e
                )
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

        Note: Firebase Admin SDK doesn't support direct password verification.
        This method returns a custom token for client-side authentication.

        Args:
            email: Email address
            password: Password (not verified server-side)
            **kwargs: Additional parameters

        Returns:
            AuthResponse with user profile and tokens
        """
        try:
            # Get user by email
            firebase_user = firebase_auth.get_user_by_email(email)

            # Create custom token
            custom_token = firebase_auth.create_custom_token(firebase_user.uid)

            # Get user profile
            user_profile = await self._firebase_user_to_profile(firebase_user)

            # Create tokens
            tokens = AuthTokens(
                access_token=custom_token.decode('utf-8'),
                refresh_token=None,
                token_type="Bearer",
                expires_in=3600
            )

            logger.info(f"[Firebase] User signed in: {email}")

            return AuthResponse(
                user=user_profile,
                tokens=tokens,
                is_new_user=False,
                provider=self.provider_name
            )

        except firebase_auth.UserNotFoundError as e:
            raise AuthUserNotFoundError(
                f"User not found: {email}",
                provider=self.provider_name,
                original_error=e
            )
        except Exception as e:
            raise AuthProviderError(
                f"Sign in failed: {str(e)}",
                provider=self.provider_name,
                error_type="SIGN_IN_ERROR",
                original_error=e
            )

    async def sign_out(self, token: str, **kwargs) -> bool:
        """
        Sign out user (revoke refresh tokens)

        Args:
            token: Access token (should contain user ID)
            **kwargs: Additional parameters

        Returns:
            bool: Success status
        """
        try:
            # Verify token and get user ID
            decoded_token = firebase_auth.verify_id_token(token)
            user_id = decoded_token['uid']

            # Revoke all refresh tokens for the user
            firebase_auth.revoke_refresh_tokens(user_id)

            logger.info(f"[Firebase] Revoked refresh tokens for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"[Firebase] Sign out failed: {str(e)}")
            return False

    async def verify_token(self, token: str, **kwargs) -> TokenVerificationResult:
        """
        Verify Firebase ID token

        Args:
            token: Firebase ID token
            **kwargs: Additional parameters

        Returns:
            TokenVerificationResult with user info
        """
        try:
            decoded_token = firebase_auth.verify_id_token(token)

            return TokenVerificationResult(
                valid=True,
                user_id=decoded_token.get('uid'),
                email=decoded_token.get('email'),
                claims=decoded_token
            )

        except firebase_auth.ExpiredIdTokenError as e:
            raise AuthTokenExpiredError(
                "Token has expired",
                provider=self.provider_name,
                original_error=e
            )
        except firebase_auth.InvalidIdTokenError as e:
            raise AuthInvalidTokenError(
                "Invalid token",
                provider=self.provider_name,
                original_error=e
            )
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

        Note: Firebase handles token refresh on the client side.
        This method is for compatibility.

        Args:
            refresh_token: Refresh token
            **kwargs: Additional parameters

        Returns:
            New AuthTokens

        Raises:
            NotImplementedError: Firebase handles refresh client-side
        """
        raise NotImplementedError(
            "Firebase handles token refresh on the client side. "
            "Use the Firebase client SDK to refresh tokens."
        )

    async def get_user(self, user_id: str, **kwargs) -> UserProfile:
        """
        Get user by ID

        Args:
            user_id: Firebase user ID
            **kwargs: Additional parameters

        Returns:
            UserProfile
        """
        try:
            firebase_user = firebase_auth.get_user(user_id)
            return await self._firebase_user_to_profile(firebase_user)

        except firebase_auth.UserNotFoundError as e:
            raise AuthUserNotFoundError(
                f"User not found: {user_id}",
                provider=self.provider_name,
                original_error=e
            )
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
            user_id: Firebase user ID
            display_name: New display name (optional)
            photo_url: New photo URL (optional)
            **kwargs: Additional Firebase user properties

        Returns:
            Updated UserProfile
        """
        try:
            update_args = {}

            if display_name is not None:
                update_args["display_name"] = display_name
            if photo_url is not None:
                update_args["photo_url"] = photo_url

            firebase_user = firebase_auth.update_user(user_id, **update_args)
            logger.info(f"[Firebase] Updated user: {user_id}")

            return await self._firebase_user_to_profile(firebase_user)

        except firebase_auth.UserNotFoundError as e:
            raise AuthUserNotFoundError(
                f"User not found: {user_id}",
                provider=self.provider_name,
                original_error=e
            )
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
            user_id: Firebase user ID
            **kwargs: Additional parameters

        Returns:
            bool: Success status
        """
        try:
            firebase_auth.delete_user(user_id)
            logger.info(f"[Firebase] Deleted user: {user_id}")
            return True

        except firebase_auth.UserNotFoundError as e:
            raise AuthUserNotFoundError(
                f"User not found: {user_id}",
                provider=self.provider_name,
                original_error=e
            )
        except Exception as e:
            raise AuthProviderError(
                f"Delete user failed: {str(e)}",
                provider=self.provider_name,
                error_type="DELETE_USER_ERROR",
                original_error=e
            )

    async def reset_password(self, email: str, **kwargs) -> bool:
        """
        Send password reset email using Firebase REST API

        Uses Firebase Identity Toolkit REST API to send password reset email.

        Args:
            email: Email address
            **kwargs: Additional parameters

        Returns:
            bool: Success status

        Raises:
            AuthProviderError: If API key is not configured or request fails
        """
        if not self.api_key:
            raise AuthProviderError(
                "Firebase API key not configured. Set 'api_key' in provider config.",
                provider=self.provider_name,
                error_type="MISSING_API_KEY"
            )

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={self.api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={
                        "requestType": "PASSWORD_RESET",
                        "email": email
                    }
                )

                if response.status_code == 200:
                    logger.info(f"[Firebase] Password reset email sent to: {email}")
                    return True
                else:
                    error_data = response.json()
                    logger.error(f"[Firebase] Password reset failed: {error_data}")
                    raise AuthProviderError(
                        f"Password reset failed: {error_data.get('error', {}).get('message', 'Unknown error')}",
                        provider=self.provider_name,
                        error_type="PASSWORD_RESET_FAILED"
                    )

        except httpx.HTTPError as e:
            logger.error(f"[Firebase] HTTP error during password reset: {e}")
            raise AuthProviderError(
                f"Network error during password reset: {str(e)}",
                provider=self.provider_name,
                error_type="NETWORK_ERROR",
                original_error=e
            )
        except Exception as e:
            logger.error(f"[Firebase] Password reset failed: {e}")
            raise AuthProviderError(
                f"Password reset failed: {str(e)}",
                provider=self.provider_name,
                error_type="PASSWORD_RESET_ERROR",
                original_error=e
            )

    async def confirm_password_reset(
        self,
        reset_code: str,
        new_password: str,
        **kwargs
    ) -> bool:
        """
        Confirm password reset using Firebase REST API

        Uses Firebase Identity Toolkit REST API to verify reset code and change password.

        Args:
            reset_code: Firebase OOB code from reset email
            new_password: New password
            **kwargs: Additional parameters

        Returns:
            bool: Success status

        Raises:
            AuthInvalidTokenError: Invalid or expired reset code
            AuthProviderError: If API key is not configured or request fails
        """
        if not self.api_key:
            raise AuthProviderError(
                "Firebase API key not configured. Set 'api_key' in provider config.",
                provider=self.provider_name,
                error_type="MISSING_API_KEY"
            )

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={self.api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={
                        "oobCode": reset_code,
                        "newPassword": new_password
                    }
                )

                if response.status_code == 200:
                    logger.info("[Firebase] Password reset confirmed successfully")
                    return True
                else:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Unknown error')

                    logger.error(f"[Firebase] Password reset confirmation failed: {error_message}")

                    # Firebase specific error codes
                    if 'EXPIRED_OOB_CODE' in error_message or 'INVALID_OOB_CODE' in error_message:
                        raise AuthTokenExpiredError(
                            "Password reset link has expired or is invalid",
                            provider=self.provider_name
                        )
                    elif 'WEAK_PASSWORD' in error_message:
                        raise AuthWeakPasswordError(
                            "Password is too weak",
                            provider=self.provider_name
                        )
                    else:
                        raise AuthInvalidTokenError(
                            f"Password reset failed: {error_message}",
                            provider=self.provider_name
                        )

        except (AuthTokenExpiredError, AuthWeakPasswordError, AuthInvalidTokenError):
            raise
        except httpx.HTTPError as e:
            logger.error(f"[Firebase] HTTP error during password reset confirmation: {e}")
            raise AuthProviderError(
                f"Network error during password reset confirmation: {str(e)}",
                provider=self.provider_name,
                error_type="NETWORK_ERROR",
                original_error=e
            )
        except Exception as e:
            logger.error(f"[Firebase] Password reset confirmation failed: {e}")
            raise AuthProviderError(
                f"Password reset confirmation failed: {str(e)}",
                provider=self.provider_name,
                error_type="PASSWORD_RESET_CONFIRM_ERROR",
                original_error=e
            )

    async def _firebase_user_to_profile(
        self,
        firebase_user: Any
    ) -> UserProfile:
        """
        Convert Firebase UserRecord to UserProfile

        Args:
            firebase_user: Firebase UserRecord

        Returns:
            UserProfile
        """
        return UserProfile(
            uid=f"firebase_{firebase_user.uid}",
            email=firebase_user.email,
            email_verified=firebase_user.email_verified,
            display_name=firebase_user.display_name,
            photo_url=firebase_user.photo_url,
            phone_number=firebase_user.phone_number,
            provider_id=self.provider_name,
            created_at=datetime.fromtimestamp(firebase_user.user_metadata.creation_timestamp / 1000) if firebase_user.user_metadata.creation_timestamp else None,
            last_login_at=datetime.fromtimestamp(firebase_user.user_metadata.last_sign_in_timestamp / 1000) if firebase_user.user_metadata.last_sign_in_timestamp else None,
            metadata={
                "disabled": firebase_user.disabled,
                "custom_claims": firebase_user.custom_claims or {}
            }
        )


# Register the provider with the factory
if FIREBASE_AVAILABLE:
    from src.auth.provider import AuthProviderFactory
    AuthProviderFactory.register("firebase", FirebaseAuthProvider)
