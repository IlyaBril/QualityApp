import logging
from .fingerprint import generate_device_fingerprint, get_client_ip

logger = logging.getLogger(__name__)


class TokenAnomalyDetector:
    """
    Service for detecting token theft and suspicious activity
    """

    def __init__(self, redis_service):
        self.redis = redis_service

    def validate_token_context(self, jti: str, request) -> tuple:
        """
        Validate if current request context matches stored token metadata
        Returns: (is_valid, anomaly_reason)
        """
        # Get stored metadata from whitelist
        stored_fingerprint = self.redis.get_token_metadata(jti, 'device_fingerprint')
        stored_ip = self.redis.get_token_metadata(jti, 'ip_address')
        stored_ua = self.redis.get_token_metadata(jti, 'user_agent')

        # Если метаданных нет - токен старый, пропускаем (или обновляем)
        if not stored_fingerprint:
            logger.warning(f"No metadata found for token {jti[:8]}, skipping validation")
            return True, None

        current_fingerprint = generate_device_fingerprint(request)
        current_ip = get_client_ip(request)
        current_ua = request.headers.get('User-Agent', '')

        anomalies = []

        # Check fingerprint (most reliable)
        if stored_fingerprint != current_fingerprint:
            anomalies.append('device_fingerprint_mismatch')
            logger.warning(f"Fingerprint mismatch for token {jti[:8]}")

        # Check IP (supplementary)
        if stored_ip and stored_ip != current_ip:
            anomalies.append('ip_address_changed')
            logger.warning(f"IP changed for token {jti[:8]}: {stored_ip} -> {current_ip}")

        # Check User-Agent (supplementary)
        if stored_ua and stored_ua != current_ua:
            anomalies.append('user_agent_changed')
            logger.warning(f"User-Agent changed for token {jti[:8]}")

        if anomalies:
            return False, anomalies

        return True, None

# Singleton instance
anomaly_detector = None

def get_anomaly_detection_service(redis_service):
    global anomaly_detector
    if anomaly_detector is None:
        anomaly_detector = TokenAnomalyDetector(redis_service)
    return anomaly_detector
