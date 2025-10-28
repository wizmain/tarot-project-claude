"""
Auth Providers package

This module imports all provider implementations to trigger their auto-registration
with the AuthProviderFactory.
"""

# Import Custom JWT Provider (required)
from src.auth.providers.custom_jwt_provider import CustomJWTProvider

__all__ = ["CustomJWTProvider"]

# Import optional providers (Firebase, Auth0)
# These are optional and will not cause errors if dependencies are not installed
try:
    from src.auth.providers.firebase_provider import FirebaseAuthProvider
    __all__.append("FirebaseAuthProvider")
except ImportError:
    pass

try:
    from src.auth.providers.auth0_provider import Auth0Provider
    __all__.append("Auth0Provider")
except ImportError:
    pass
