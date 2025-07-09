
import json
import pickle
import hashlib
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import current_app, request
import redis

logger = logging.getLogger(__name__)

class CacheManager:
    """Comprehensive caching layer with Redis and fallback"""
    
    def __init__(self, redis_client=None, default_ttl=300):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.memory_cache = {}  # Fallback cache
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def _get_cache_key(self, key_parts):
        """Generate cache key from parts"""
        key_string = ':'.join(str(part) for part in key_parts)
        return f"fai_cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get(self, key_parts, default=None):
        """Get value from cache"""
        cache_key = self._get_cache_key(key_parts)
        
        try:
            # Try Redis first
            if self.redis:
                value = self.redis.get(cache_key)
                if value is not None:
                    self.cache_stats['hits'] += 1
                    return json.loads(value) if isinstance(value, (str, bytes)) else value
            
            # Fallback to memory cache
            if cache_key in self.memory_cache:
                cache_entry = self.memory_cache[cache_key]
                if cache_entry['expires'] > datetime.utcnow():
                    self.cache_stats['hits'] += 1
                    return cache_entry['value']
                else:
                    # Expired entry
                    del self.memory_cache[cache_key]
            
            self.cache_stats['misses'] += 1
            return default
            
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            self.cache_stats['misses'] += 1
            return default
    
    def set(self, key_parts, value, ttl=None):
        """Set value in cache"""
        cache_key = self._get_cache_key(key_parts)
        ttl = ttl or self.default_ttl
        
        try:
            # Try Redis first
            if self.redis:
                serialized_value = json.dumps(value) if not isinstance(value, (str, bytes)) else value
                self.redis.setex(cache_key, ttl, serialized_value)
                self.cache_stats['sets'] += 1
                return True
            
            # Fallback to memory cache
            self.memory_cache[cache_key] = {
                'value': value,
                'expires': datetime.utcnow() + timedelta(seconds=ttl)
            }
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def delete(self, key_parts):
        """Delete value from cache"""
        cache_key = self._get_cache_key(key_parts)
        
        try:
            # Try Redis first
            if self.redis:
                self.redis.delete(cache_key)
            
            # Remove from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            self.cache_stats['deletes'] += 1
            return True
            
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern):
        """Clear cache entries matching pattern"""
        try:
            if self.redis:
                keys = self.redis.keys(f"fai_cache:*{pattern}*")
                if keys:
                    self.redis.delete(*keys)
            
            # Clear matching memory cache entries
            keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.memory_cache[key]
            
            return True
            
        except Exception as e:
            logger.warning(f"Cache clear pattern error: {e}")
            return False
    
    def get_stats(self):
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            **self.cache_stats
        }

# Cache decorators
def cached(ttl=300, key_func=None):
    """Cache decorator for functions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_manager = getattr(current_app, 'cache_manager', None)
            if not cache_manager:
                return f(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key_parts = key_func(*args, **kwargs)
            else:
                cache_key_parts = [f.__name__, str(args), str(sorted(kwargs.items()))]
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key_parts)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache_manager.set(cache_key_parts, result, ttl)
            
            return result
        return decorated_function
    return decorator

def cache_api_response(ttl=300):
    """Cache API response decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_manager = getattr(current_app, 'cache_manager', None)
            if not cache_manager:
                return f(*args, **kwargs)
            
            # Generate cache key from request
            cache_key_parts = [
                'api_response',
                f.__name__,
                request.method,
                request.path,
                str(sorted(request.args.items())),
                getattr(request, 'user_id', 'anonymous')
            ]
            
            # Try to get from cache
            cached_response = cache_manager.get(cache_key_parts)
            if cached_response is not None:
                return cached_response
            
            # Execute function and cache result
            response = f(*args, **kwargs)
            
            # Only cache successful responses
            if hasattr(response, 'status_code') and response.status_code == 200:
                cache_manager.set(cache_key_parts, response.get_json(), ttl)
            
            return response
        return decorated_function
    return decorator

def setup_caching(app):
    """Initialize caching layer"""
    try:
        redis_client = getattr(app, 'redis', None)
        cache_manager = CacheManager(redis_client)
        app.cache_manager = cache_manager
        
        logger.info("Caching layer initialized successfully")
        return cache_manager
        
    except Exception as e:
        logger.error(f"Failed to initialize caching layer: {e}")
        return None
