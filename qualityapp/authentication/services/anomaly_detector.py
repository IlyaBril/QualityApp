import hashlib
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TokenAnomalyDetector:
    def __init__(self):
        self.fingerprint_keys = ['ip', 'user_agent', 'device_id']

    def check_token_anomaly(self, request, user_id, token_jti):
        # Создание отпечатка устройства
        current_fingerprint = self.create_fingerprint(request)

        # Получение последнего отпечатка для этого токена
        cache_key = f"token_fingerprint:{token_jti}"
        stored_fingerprint = cache.get(cache_key)

        if stored_fingerprint and stored_fingerprint != current_fingerprint:
            # Отправка оповещения
            self.alert_token_theft(user_id, token_jti, stored_fingerprint, current_fingerprint)
            return True  # Обнаружена аномалия

        cache.set(cache_key, current_fingerprint, timeout=3600)
        return False

    def create_fingerprint(self, request):
        data = f"{request.META.get('REMOTE_ADDR')}|{request.META.get('HTTP_USER_AGENT')}"
        return hashlib.sha256(data.encode()).hexdigest()

    def alert_token_theft(self, user_id, token_jti, old_fp, new_fp):
        # Реализация оповещения администратора и пользователя
        # Пример: отправка email, WebSocket уведомление, запись в alert лог
        logger.critical(f"TOKEN THEFT DETECTED! User {user_id}, Token {token_jti}")