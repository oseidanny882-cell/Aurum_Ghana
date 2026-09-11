'''
Aurum Ghana - Flask extensions (initialised here, bound to app in app.py)
'''
import os
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
migrate = Migrate()

def _rate_limit_key():
    from flask import request
    if request.method == 'OPTIONS':
        return None
    return get_remote_address()

limiter = Limiter(key_func=_rate_limit_key, default_limits=['1000 per hour'])

logger = logging.getLogger(__name__)

_jwt_blacklist = set()
_redis_client = None

def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    redis_url = os.getenv('REDIS_URL', '')
    if not redis_url:
        return None
    try:
        import redis as redis_lib
        _redis_client = redis_lib.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        logger.info('JWT blacklist using Redis at %s', redis_url)
        return _redis_client
    except Exception as e:
        logger.warning('Redis unavailable for JWT blacklist, using in-memory: %s', e)
        _redis_client = None
        return None

def jwt_token_in_blacklist_callback(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    redis = _get_redis()
    if redis:
        return redis.sismember('jwt_blacklist', jti)
    return jti in _jwt_blacklist

def revoke_token(jti):
    redis = _get_redis()
    if redis:
        redis.sadd('jwt_blacklist', jti)
    else:
        _jwt_blacklist.add(jti)

def revoke_all_user_tokens(user_jtis):
    redis = _get_redis()
    if redis:
        redis.sadd('jwt_blacklist', *user_jtis)
    else:
        _jwt_blacklist.update(user_jtis)
