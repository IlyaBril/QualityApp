from os import access

from django.utils.deprecation import MiddlewareMixin
from authentication.services.redis_service import redis_token_service
from rest_framework_simplejwt.tokens import AccessToken
import logging

logger = logging.getLogger(__name__)


class TokenValidationMiddleware(MiddlewareMixin):
    """
    Middleware to validate tokens on every request
    """

    def process_request(self, request):
        # Skip for non-authenticated paths
        skip_paths = ['/api/login/', '/api/register/', '/api/token/refresh/', '/admin/']

        if any(request.path.startswith(path) for path in skip_paths):
            return None

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

            try:
                # Decode token without validation to get JTI
                access_token = AccessToken(token)

                jti = access_token['jti']

                # Check blacklist
                if redis_token_service.is_blacklisted(jti):
                    logger.warning(f"Blacklisted token detected for path: {request.path}")

            except Exception as e:
                logger.error(f"Token validation error in middleware: {e}")

        return None
