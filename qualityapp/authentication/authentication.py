import logging

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import exceptions
from django.conf import settings
from .services.redis_service import redis_token_service
from .services.anomaly_detector import get_anomaly_detection_service


logger = logging.getLogger(__name__)

class CustomJWTAuthentication(JWTAuthentication):
    """
        Get token from request, checks if whitelisted and blacklisted
    """

    def __init__(self):
        super().__init__()
        self.anomaly_detector = get_anomaly_detection_service(redis_token_service)

    def authenticate(self, request):
        """
        :param request:
        :return: User, Validated Token
        """
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
            user_id = validated_token.get('user_id')

            # Check blacklist
            if settings.BLACKLIST_ENABLED and redis_token_service.is_blacklisted(jti):
                logger.warning(f"Blacklisted token used: {jti}")
                raise InvalidToken('Token is blacklisted', code='token_blacklisted')

            # Check whitelist is enabled
            if settings.WHITELIST_ENABLED:
                if not redis_token_service.is_whitelisted(jti):
                    # If whitelist is enabled and token not found, reject
                    logger.warning(f"Token not in whitelist: {jti}")
                    raise InvalidToken('Token is not authorized', code='token_not_whitelisted')

            # Check if metadata exists (first use or old token)
            metadata_exists = redis_token_service.get_token_metadata(jti, 'device_fingerprint')

            # If no metadata - pass
            if metadata_exists:
                # Validate context for token theft
                is_valid, anomaly_reason = self.anomaly_detector.validate_token_context(jti, request)

                if not is_valid:
                    logger.warning(f"Context validation failed for token {jti[:8]}: {anomaly_reason}")
                    raise InvalidToken(f'Suspicious activity detected {", ".join(anomaly_reason)}. Please login again.')

            # Get user from token
            user = self.get_user(validated_token)

            return (user, validated_token)

        except InvalidToken as e:
            raise exceptions.AuthenticationFailed(str(e))
        except TokenError as e:
            raise exceptions.AuthenticationFailed(str(e))
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise exceptions.AuthenticationFailed('Authentication failed')
