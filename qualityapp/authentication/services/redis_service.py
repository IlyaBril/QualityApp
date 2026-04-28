import redis
from django.conf import settings
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RedisTokenService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        self.prefix_blacklist = "token:blacklist"
        self.prefix_whitelist = "token:whitelist"
        self.prefix_user_tokens = "token:users:"
        self.metadata_lifetime = getattr(settings, 'TOKEN_METADATA_TTL', 604800)

    def add_to_blacklist(self, jti, user_id, expires_at):
        """
        Add token to blacklist
        :param jti:
        :param user_id:
        :param expires_at:
        :return:
        """
        try:
            key = f"{self.prefix_blacklist}{jti}"
            ttl = (expires_at - datetime.now()).total_seconds()
            if ttl > 0:
                self.redis_client.setex(
                    key,
                    int(ttl),
                    json.dumps({
                        'user_id': user_id,
                        'expires_at': expires_at.isoformat()
                    })
                )
                logger.info(f"Token {jti} added to blacklist for user_id {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding token to blacklist {e}")
        return False

    def is_blacklisted(self, jti):
        """
        Check if token is blacklisted
        :param jti:
        :return:
        """
        try:
            key = f"{self.prefix_blacklist}{jti}"
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
        return False

    def add_to_whitelist(self, jti, user_id, expires_at, token_data=None):
        """
        Add token to whitelist with metadata
        :param jti: JWT ID
        :param user_id: User ID
        :param expires_at: Expiration datetime
        :param token_data: Dictionary with metadata (device_fingerprint, ip, etc.)
        """
        try:
            key = f"{self.prefix_whitelist}{jti}"
            ttl = (expires_at - datetime.now()).total_seconds()
            if ttl > 0:
                data = {
                    'user_id': user_id,
                    'expires_at': expires_at.isoformat(),
                    'token_data': token_data or {},
                }
                self.redis_client.setex(key, int(ttl), json.dumps(data))

                #Track user's active tokens
                user_key = f"{self.prefix_user_tokens}{user_id}"
                self.redis_client.sadd(user_key, jti)
                self.redis_client.expire(user_key, int(ttl))

                logger.info(f"Token {jti} add to whitelist for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding token to whitelist: {e}")
        return False

    def is_whitelisted(self, jti):
        """
        Check if token is whitelisted
        :param jti: JWT ID
        :return: True or False
        """
        try:
            key = f"{self.prefix_whitelist}{jti}"
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking whitelist: {e}")
        return False

    def remove_from_whitelist(self, jti):
        """
        Remove token from whitelist
        :param jti: JWT ID
        :return: True or False
        """
        try:
            # Get token data first to know user_id
            key = f"{self.prefix_whitelist}{jti}"
            token_data = self.redis_client.get(key)

            if token_data:
                data = json.loads(token_data)
                user_id = data.get('user_id')

                # Remove from whitelist
                self.redis_client.delete(key)

                # Remove from user's active tokens
                if user_id:
                    user_key = f"{self.prefix_user_tokens}{user_id}"
                    self.redis_client.srem(user_key, jti)

                logger.info(f"Token {jti} removed from whitelist")
                return True

        except Exception as e:
            logger.error(f"Error removing from whitelist {e}")
        return False

    def get_user_active_tokens(self, user_id):
        """
        Get all active tokens for user
        :param user_id: User ID
        :return: list or tokens or []
        """
        try:
            user_key = f"{self.prefix_user_tokens}{user_id}"
            tokens = self.redis_client.smembers(user_key)
            return list(tokens)
        except Exception as e:
            logger.error(f"Error getting user tokens: {e}")
        return []

    def revoke_all_tokens(self, user_id):
        """
        Revoke all tokens for user
        :param user_id: User ID
        :return:
        """
        try:
            tokens = self.get_user_active_tokens(user_id)
            for jti in tokens:
                # Add to blacklist
                whitelist_key = f"{self.prefix_whitelist}{jti}"
                token_data = self.redis_client.get(whitelist_key)

                if token_data:
                    data = json.loads(token_data)
                    expires_at = datetime.fromisoformat(data['expires_at'])
                    self.add_to_blacklist(jti, user_id, expires_at)

                # Remove from whitelist
                self.redis_client.delete(whitelist_key)

                logger.info(f"All tokens revoked for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error revoking users tokens: {e}")
        return False

    def update_token_metadata(self, jti: str, metadata_key: str, metadata_value: str):
        """
        Update metadata for existing token in whitelist
        :param jti: JWT ID
        :param metadata_key: Key to update (e.g., 'device_fingerprint')
        :param metadata_value: Value to store
        """
        try:
            key = f"{self.prefix_whitelist}{jti}"
            token_data_json = self.redis_client.get(key)

            if token_data_json:
                data = json.loads(token_data_json)

                # Initialize token_data if not exists
                if 'token_data' not in data:
                    data['token_data'] = {}

                # Update metadata
                data['token_data'][metadata_key] = metadata_value

                # Get remaining TTL
                ttl = self.redis_client.ttl(key)
                if ttl > 0:
                    # Save back with same TTL
                    self.redis_client.setex(key, ttl, json.dumps(data))
                    logger.debug(f"Updated metadata {metadata_key} for token {jti[:8]}")
                    return True

            return False
        except Exception as e:
            logger.error(f"Error updating token metadata: {e}")
            return False

    def get_token_metadata(self, jti: str, metadata_key: str = None):
        """
        Get metadata from token in whitelist
        :param jti: JWT ID
        :param metadata_key: Specific key to get, or None to get all metadata
        :return: Metadata value or None
        """
        try:
            key = f"{self.prefix_whitelist}{jti}"
            token_data_json = self.redis_client.get(key)

            if token_data_json:
                data = json.loads(token_data_json)
                token_data = data.get('token_data', {})

                if metadata_key:
                    return token_data.get(metadata_key)
                return token_data

            return None
        except Exception as e:
            logger.error(f"Error getting token metadata: {e}")
            return None

    def set_token_fingerprint(self, jti: str, fingerprint: str):
        """Store device fingerprint in token metadata"""
        return self.update_token_metadata(jti, 'device_fingerprint', fingerprint)

    def get_token_fingerprint(self, jti: str):
        """Get device fingerprint from token metadata"""
        return self.get_token_metadata(jti, 'device_fingerprint')

    def set_token_ip(self, jti: str, ip_address: str):
        """Store IP address in token metadata"""
        return self.update_token_metadata(jti, 'ip_address', ip_address)

    def get_token_ip(self, jti: str):
        """Get IP address from token metadata"""
        return self.get_token_metadata(jti, 'ip_address')

    def set_token_user_agent(self, jti: str, user_agent: str):
        """Store User-Agent in token metadata"""
        return self.update_token_metadata(jti, 'user_agent', user_agent)

    def get_token_user_agent(self, jti: str):
        """Get User-Agent from token metadata"""
        return self.get_token_metadata(jti, 'user_agent')


# Singleton instance
redis_token_service = RedisTokenService()
