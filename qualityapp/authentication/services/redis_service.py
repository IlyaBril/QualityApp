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
                        'expires_at': expires_at.iso_format()
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
        Add token to whitelist
        :param jti:
        :param user_id:
        :param expires_at:
        :param token_data:
        :return:
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
        :param jti:
        :return:
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
        :param jti:
        :return:
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
                    user_key = f"{self.prefix_user_tokens}{jti}"
                    self.redis_client.srem(user_key, jti)

                logger.info(f"Token {jti} removed from whitelist")
                return True

        except Exception as e:
            logger.error(f"Error removing from whitelist {e}")
        return False

    def get_user_active_tokens(self, user_id):
        """
        Get all active tokens for user
        :param user_id:
        :return:
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
        :param user_id:
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
                self.redis_client.delete(user_id)

                logger.info(f"All tokens revoked for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error revoking users tokens: {e}")
        return False

# Singleton instance
redis_token_service = RedisTokenService()
