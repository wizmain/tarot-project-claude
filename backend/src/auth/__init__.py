"""
Auth Module

Authentication and authorization package for the Tarot AI application.

Features:
- Multi-provider authentication (Firebase, Auth0, Custom JWT)
- Provider abstraction for easy switching
- Automatic fallback to backup providers
- JWT token management
- User profile management
- Password reset functionality

Usage:
    # Import provider factory
    from src.auth.provider import AuthProviderFactory

    # Create a provider
    provider = AuthProviderFactory.create(
        "custom_jwt",
        config={"secret_key": "..."}
    )

    # Or use the orchestrator for multi-provider support
    from src.auth.orchestrator import AuthOrchestrator

    orchestrator = AuthOrchestrator(
        primary_provider="custom_jwt",
        fallback_providers=["firebase"],
        configs={
            "custom_jwt": {"secret_key": "..."},
            "firebase": {"credentials_path": "..."}
        }
    )

    # Sign up
    response = await orchestrator.sign_up(
        email="user@example.com",
        password="password123",
        display_name="User Name"
    )

    # Sign in
    response = await orchestrator.sign_in(
        email="user@example.com",
        password="password123"
    )

    # Verify token
    result = await orchestrator.verify_token(token)
"""

from src.auth.provider import AuthProvider, AuthProviderFactory
from src.auth.orchestrator import AuthOrchestrator
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
    AuthServiceUnavailableError,
)

# Import providers to trigger auto-registration
import src.auth.providers

__all__ = [
    # Core classes
    "AuthProvider",
    "AuthProviderFactory",
    "AuthOrchestrator",
    # Models
    "AuthResponse",
    "UserProfile",
    "AuthTokens",
    "TokenVerificationResult",
    # Exceptions
    "AuthProviderError",
    "AuthInvalidCredentialsError",
    "AuthUserNotFoundError",
    "AuthEmailAlreadyExistsError",
    "AuthWeakPasswordError",
    "AuthInvalidTokenError",
    "AuthTokenExpiredError",
    "AuthServiceUnavailableError",
]
