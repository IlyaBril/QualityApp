from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import exceptions
from django.conf import settings
from .services.redis_service import redis_token_service
import logging

logger = logging.getLogger(__name__)

class CustomJWTAuthentication(JWTAuthentication):
    """
        Custom JWT authentication that checks whitelist and blacklist
    """

    def authenticate(self, request):
        try:
            # Get the token from request
            header = self.get_header(request)
            if header is None:
                return None

            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

            # Validate token and get validated token
            validated_token = self.get_validated_token(raw_token)

            # Get JTI (JWT ID) from token
            jti = validated_token.get('jti')

            # Сheck blacklist
            if settings.BLACKLIST_ENABLED and redis_token_service.is_blacklisted(jti):
                logger.warning(f"Blacklisted token used: {jti}")
                raise InvalidToken('Token is blacklisted', code='token_blacklisted')

            #Check whitelist is enabled
            if settings.WHITELIST_ENABLED:
                if not redis_token_service.is_whitelisted(jti):
                    #If whitelist is enabled and token not found, reject
                    logger.warning(f"Token not in whitelist: {jti}")
                    raise InvalidToken('Token is not authorized', code='token_not_whitelisted')

            #Get user from token
            user = self.get_user(validated_token)

            return (user, validated_token)

        except InvalidToken as e:
            raise exceptions.AuthenticationFailed(str(e))
        except TokenError as e:
            raise exceptions.AuthenticationFailed(str(e))
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise exceptions.AuthenticationFailed('Authentication failed')

class OptionalJWTAuthentication(CustomJWTAuthentication):
    """
    Optional JWT authentication - doesn't fail if token is not provided
    """
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except exceptions.AuthenticationFailed:
            return None
