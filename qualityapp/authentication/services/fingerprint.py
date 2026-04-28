import hashlib
import logging
import json

logger = logging.getLogger(__name__)


def generate_device_fingerprint(request) -> str:
    """
    Generate secure device fingerprint from request data
    """

    fingerprint_data = {
        'ip': get_client_ip(request),
        'user_agent': request.headers.get('User-Agent', ''),
        'accept_language': request.headers.get('Accept-Language', ''),
        'accept_encoding': request.headers.get('Accept-Encoding', ''),
        'sec_ch_ua': request.headers.get('Sec-CH-UA', ''),
        'sec_ch_ua_platform': request.headers.get('Sec-CH-UA-Platform', ''),
    }

    fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()


def get_client_ip(request) -> str:
    """Extract client IP from request"""
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR', '')
