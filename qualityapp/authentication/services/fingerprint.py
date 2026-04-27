import hashlib
import logging

logger = logging.getLogger(__name__)

def generate_device_fingerprint(request):
    """
    Генерирует уникальный fingerprint устройства на основе данных запроса.
    """
    # 1. Получаем IP-адрес клиента
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    # 2. Получаем User-Agent (информация о браузере и ОС)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    # 3. (Опционально, но настоятельно рекомендуется) Пробуем получить Accept-Language
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')

    # Собираем все в одну строку
    fingerprint_data = f"{ip}|{user_agent}|{accept_language}"

    # Создаем хеш (SHA256) для получения компактного и безопасного идентификатора
    fingerprint_hash = hashlib.sha256(fingerprint_data.encode('utf-8')).hexdigest()

    logger.debug(f"Generated fingerprint for IP {ip}: {fingerprint_hash[:8]}...")
    return fingerprint_hash