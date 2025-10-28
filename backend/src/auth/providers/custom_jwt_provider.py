"""
Custom JWT Authentication Provider

데이터베이스 기반 JWT 인증 구현
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import uuid

import jwt
import bcrypt
from sqlalchemy.orm import Session

from src.auth.provider import AuthProvider, AuthProviderFactory
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
)
from src.core.email_service import email_service
from src.core.config import settings
from src.core.database import SessionLocal
from src.models import User

logger = logging.getLogger(__name__)


class CustomJWTProvider(AuthProvider):
    """
    Custom JWT Authentication Provider

    데이터베이스를 사용한 사용자 인증 및 JWT 토큰 발급

    Configuration:
        {
            "secret_key": "your-secret-key",
            "algorithm": "HS256",  # Optional, default: HS256
            "access_token_expire_minutes": 60,  # Optional, default: 60
            "refresh_token_expire_days": 7  # Optional, default: 7
        }
    """

    def __init__(
        self,
        config: Dict[str, Any],
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Custom JWT Provider

        Args:
            config: JWT configuration
            timeout: Request timeout in seconds (not used for DB operations)
            max_retries: Maximum number of retry attempts
        """
        super().__init__(config, timeout, max_retries)

        self.secret_key = config.get("secret_key")
        if not self.secret_key:
            raise AuthProviderError(
                "Secret key is required for JWT provider",
                provider=self.provider_name,
                error_type="INVALID_CONFIG"
            )

        self.algorithm = config.get("algorithm", "HS256")
        self.access_token_expire_minutes = config.get("access_token_expire_minutes", 60)
        self.refresh_token_expire_days = config.get("refresh_token_expire_days", 7)

    @property
    def provider_name(self) -> str:
        return "custom_jwt"

    @property
    def supported_features(self) -> List[str]:
        return [
            "email_password",
            "jwt_tokens",
            "refresh_tokens",
            "user_management",
            "password_reset"
        ]

    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            bool: True if password matches
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def _create_token(
        self,
        data: Dict[str, Any],
        expires_delta: timedelta
    ) -> str:
        """
        Create JWT token

        Args:
            data: Payload data
            expires_delta: Token expiration time

        Returns:
            JWT token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        return encoded_jwt

    async def sign_up(
        self,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        **kwargs
    ) -> AuthResponse:
        """
        Create a new user

        Args:
            email: Email address
            password: Password
            display_name: Display name (optional)
            **kwargs: Additional user metadata

        Returns:
            AuthResponse with user profile and tokens
        """
        db = SessionLocal()
        try:
            self._validate_email(email)
            self._validate_password(password)

            # Check if user already exists in DB
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise AuthEmailAlreadyExistsError(
                    f"Email already exists: {email}",
                    provider=self.provider_name
                )

            # Create user in DB
            user_id = str(uuid.uuid4())
            password_hash = self._hash_password(password)
            now = datetime.utcnow()

            # Create user profile
            user_profile = UserProfile(
                uid=f"jwt_{user_id}",
                email=email,
                email_verified=False,
                display_name=display_name,
                photo_url=None,
                phone_number=None,
                provider_id=self.provider_name,
                created_at=now,
                last_login_at=now,
                metadata={"password_hash": password_hash, **kwargs}  # Include password_hash for auth.py
            )

            # Generate tokens
            access_token = self._create_token(
                data={"sub": user_id, "email": email, "type": "access"},
                expires_delta=timedelta(minutes=self.access_token_expire_minutes)
            )

            refresh_token = self._create_token(
                data={"sub": user_id, "email": email, "type": "refresh"},
                expires_delta=timedelta(days=self.refresh_token_expire_days)
            )

            tokens = AuthTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=self.access_token_expire_minutes * 60
            )

            logger.info(f"[CustomJWT] Created new user: {email}")

            return AuthResponse(
                user=user_profile,
                tokens=tokens,
                is_new_user=True,
                provider=self.provider_name
            )

        except (AuthEmailAlreadyExistsError, AuthWeakPasswordError, AuthProviderError):
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Sign up failed: {str(e)}",
                provider=self.provider_name,
                error_type="SIGN_UP_ERROR",
                original_error=e
            )
        finally:
            db.close()

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
        db = SessionLocal()
        try:
            # Get user from DB
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise AuthUserNotFoundError(
                    f"User not found: {email}",
                    provider=self.provider_name
                )

            # Verify password
            if not user.password_hash:
                raise AuthInvalidCredentialsError(
                    "Password not set for this user",
                    provider=self.provider_name
                )

            if not self._verify_password(password, user.password_hash):
                raise AuthInvalidCredentialsError(
                    "Invalid email or password",
                    provider=self.provider_name
                )

            # Extract user_id from provider_user_id (format: jwt_<uuid>)
            user_id = user.provider_user_id.replace("jwt_", "")

            # Create user profile
            user_profile = UserProfile(
                uid=user.provider_user_id,
                email=user.email,
                email_verified=user.email_verified,
                display_name=user.display_name,
                photo_url=user.photo_url,
                phone_number=user.phone_number,
                provider_id=self.provider_name,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                metadata=user.user_metadata or {}
            )

            # Generate tokens
            access_token = self._create_token(
                data={"sub": user_id, "email": email, "type": "access"},
                expires_delta=timedelta(minutes=self.access_token_expire_minutes)
            )

            refresh_token = self._create_token(
                data={"sub": user_id, "email": email, "type": "refresh"},
                expires_delta=timedelta(days=self.refresh_token_expire_days)
            )

            tokens = AuthTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=self.access_token_expire_minutes * 60
            )

            logger.info(f"[CustomJWT] User signed in: {email}")

            return AuthResponse(
                user=user_profile,
                tokens=tokens,
                is_new_user=False,
                provider=self.provider_name
            )

        except (AuthUserNotFoundError, AuthInvalidCredentialsError, AuthProviderError):
            raise
        except Exception as e:
            raise AuthProviderError(
                f"Sign in failed: {str(e)}",
                provider=self.provider_name,
                error_type="SIGN_IN_ERROR",
                original_error=e
            )
        finally:
            db.close()

    async def sign_out(self, token: str, **kwargs) -> bool:
        """
        Sign out user

        Note: For stateless JWT, this is a no-op.
        In production, implement token blacklist.

        Args:
            token: Access token
            **kwargs: Additional parameters

        Returns:
            bool: Success status
        """
        logger.info("[CustomJWT] Sign out called (stateless JWT)")
        # In production, add token to blacklist in Redis/DB
        return True

    async def verify_token(self, token: str, **kwargs) -> TokenVerificationResult:
        """
        Verify JWT token

        Args:
            token: JWT token
            **kwargs: Additional parameters

        Returns:
            TokenVerificationResult
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check token type
            if payload.get("type") != "access":
                raise AuthInvalidTokenError(
                    "Invalid token type",
                    provider=self.provider_name
                )

            return TokenVerificationResult(
                valid=True,
                user_id=payload.get("sub"),
                email=payload.get("email"),
                claims=payload
            )

        except jwt.ExpiredSignatureError as e:
            raise AuthTokenExpiredError(
                "Token has expired",
                provider=self.provider_name,
                original_error=e
            )
        except jwt.InvalidTokenError as e:
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

        Args:
            refresh_token: Refresh token
            **kwargs: Additional parameters

        Returns:
            New AuthTokens
        """
        try:
            # Verify refresh token
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check token type
            if payload.get("type") != "refresh":
                raise AuthInvalidTokenError(
                    "Invalid token type for refresh",
                    provider=self.provider_name
                )

            user_id = payload.get("sub")
            email = payload.get("email")

            # Generate new access token
            new_access_token = self._create_token(
                data={"sub": user_id, "email": email, "type": "access"},
                expires_delta=timedelta(minutes=self.access_token_expire_minutes)
            )

            return AuthTokens(
                access_token=new_access_token,
                refresh_token=refresh_token,  # Keep same refresh token
                token_type="Bearer",
                expires_in=self.access_token_expire_minutes * 60
            )

        except jwt.ExpiredSignatureError as e:
            raise AuthTokenExpiredError(
                "Refresh token has expired",
                provider=self.provider_name,
                original_error=e
            )
        except jwt.InvalidTokenError as e:
            raise AuthInvalidTokenError(
                "Invalid refresh token",
                provider=self.provider_name,
                original_error=e
            )
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
            user_id: User ID
            **kwargs: Additional parameters

        Returns:
            UserProfile
        """
        try:
            if user_id not in self._users_by_id:
                raise AuthUserNotFoundError(
                    f"User not found: {user_id}",
                    provider=self.provider_name
                )

            user_data = self._users_by_id[user_id]

            return UserProfile(
                uid=f"jwt_{user_data['user_id']}",
                email=user_data["email"],
                email_verified=user_data.get("email_verified", False),
                display_name=user_data.get("display_name"),
                photo_url=user_data.get("photo_url"),
                phone_number=user_data.get("phone_number"),
                provider_id=self.provider_name,
                created_at=user_data.get("created_at"),
                last_login_at=user_data.get("last_login_at"),
                metadata=user_data.get("metadata", {})
            )

        except AuthUserNotFoundError:
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
            user_id: User ID
            display_name: New display name (optional)
            photo_url: New photo URL (optional)
            **kwargs: Additional user metadata

        Returns:
            Updated UserProfile
        """
        try:
            if user_id not in self._users_by_id:
                raise AuthUserNotFoundError(
                    f"User not found: {user_id}",
                    provider=self.provider_name
                )

            user_data = self._users_by_id[user_id]

            if display_name is not None:
                user_data["display_name"] = display_name
            if photo_url is not None:
                user_data["photo_url"] = photo_url

            # Update metadata
            if kwargs:
                user_data["metadata"].update(kwargs)

            logger.info(f"[CustomJWT] Updated user: {user_id}")

            return await self.get_user(user_id)

        except AuthUserNotFoundError:
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
            user_id: User ID
            **kwargs: Additional parameters

        Returns:
            bool: Success status
        """
        try:
            if user_id not in self._users_by_id:
                raise AuthUserNotFoundError(
                    f"User not found: {user_id}",
                    provider=self.provider_name
                )

            user_data = self._users_by_id[user_id]
            email = user_data["email"]

            # Delete from both storages
            del self._users[email]
            del self._users_by_id[user_id]

            logger.info(f"[CustomJWT] Deleted user: {user_id}")
            return True

        except AuthUserNotFoundError:
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

        Generates a reset token and sends it via email using EmailService.

        Args:
            email: Email address
            **kwargs: Additional parameters

        Returns:
            bool: Success status

        Raises:
            AuthUserNotFoundError: User not found
            AuthProviderError: Email sending failed
        """
        try:
            if email not in self._users:
                raise AuthUserNotFoundError(
                    f"User not found: {email}",
                    provider=self.provider_name
                )

            user_data = self._users[email]
            user_id = user_data["user_id"]

            # Get expiration time from settings
            expires_minutes = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

            # Generate password reset token
            reset_token = self._create_token(
                data={"sub": user_id, "email": email, "type": "password_reset"},
                expires_delta=timedelta(minutes=expires_minutes)
            )

            # Store reset token in user metadata (in production, use separate table/cache)
            user_data["reset_token"] = reset_token

            # Send email with reset token
            email_sent = await email_service.send_password_reset_email(
                email=email,
                reset_token=reset_token,
                expires_in_minutes=expires_minutes
            )

            if not email_sent:
                logger.error(f"[CustomJWT] Failed to send password reset email to: {email}")
                raise AuthProviderError(
                    "Failed to send password reset email",
                    provider=self.provider_name,
                    error_type="EMAIL_SEND_ERROR"
                )

            logger.info(f"[CustomJWT] Password reset email sent to: {email}")
            return True

        except AuthUserNotFoundError:
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
        reset_token: str,
        new_password: str
    ) -> bool:
        """
        Confirm password reset with token

        Args:
            reset_token: Password reset token
            new_password: New password

        Returns:
            bool: Success status
        """
        try:
            # Verify reset token
            payload = jwt.decode(
                reset_token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check token type
            if payload.get("type") != "password_reset":
                raise AuthInvalidTokenError(
                    "Invalid token type for password reset",
                    provider=self.provider_name
                )

            user_id = payload.get("sub")
            email = payload.get("email")

            if user_id not in self._users_by_id:
                raise AuthUserNotFoundError(
                    f"User not found: {user_id}",
                    provider=self.provider_name
                )

            # Validate new password
            self._validate_password(new_password)

            # Update password
            user_data = self._users_by_id[user_id]
            user_data["password_hash"] = self._hash_password(new_password)

            # Clear reset token
            if "reset_token" in user_data:
                del user_data["reset_token"]

            logger.info(f"[CustomJWT] Password reset confirmed for: {email}")
            return True

        except (AuthInvalidTokenError, AuthUserNotFoundError, AuthWeakPasswordError):
            raise
        except jwt.ExpiredSignatureError as e:
            raise AuthTokenExpiredError(
                "Password reset token has expired",
                provider=self.provider_name,
                original_error=e
            )
        except jwt.InvalidTokenError as e:
            raise AuthInvalidTokenError(
                "Invalid password reset token",
                provider=self.provider_name,
                original_error=e
            )
        except Exception as e:
            raise AuthProviderError(
                f"Password reset confirmation failed: {str(e)}",
                provider=self.provider_name,
                error_type="RESET_PASSWORD_ERROR",
                original_error=e
            )


# Register the provider with the factory
AuthProviderFactory.register("custom_jwt", CustomJWTProvider)
