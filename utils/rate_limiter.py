
import time
import logging
from functools import wraps
from collections import defaultdict, deque
from flask import request, jsonify, current_app, g
from datetime import datetime, timedelta
import redis

logger = logging.getLogger(__name__)

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.memory_store = defaultdict(deque)  # Fallback storage
        self.blocked_ips = set()
        
    def _get_client_id(self):
        """Get client identifier for rate limiting"""
        # Try to get user ID first
        if hasattr(g, 'current_user') and g.current_user:
            return f"user:{g.current_user.id}"
        
        # Fall back to IP address
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        return f"ip:{ip}"
    
    def _is_rate_limited_redis(self, key, limit, window):
        """Redis-based rate limiting using sliding window"""
        try:
            current_time = time.time()
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, current_time - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, int(window) + 1)
            
            results = pipe.execute()
            current_requests = results[1]
            
            return current_requests >= limit
            
        except Exception as e:
            logger.warning(f"Redis rate limiting failed: {e}")
            return False
    
    def _is_rate_limited_memory(self, key, limit, window):
        """Memory-based rate limiting (fallback)"""
        current_time = time.time()
        cutoff_time = current_time - window
        
        # Clean old entries
        while self.memory_store[key] and self.memory_store[key][0] < cutoff_time:
            self.memory_store[key].popleft()
        
        # Check limit
        if len(self.memory_store[key]) >= limit:
            return True
        
        # Add current request
        self.memory_store[key].append(current_time)
        return False
    
    def is_rate_limited(self, endpoint, limit, window, client_id=None):
        """Check if request should be rate limited"""
        if not client_id:
            client_id = self._get_client_id()
        
        # Check if IP is blocked
        if client_id.startswith('ip:') and client_id in self.blocked_ips:
            return True
        
        rate_key = f"rate_limit:{endpoint}:{client_id}"
        
        # Try Redis first
        if self.redis:
            return self._is_rate_limited_redis(rate_key, limit, window)
        else:
            return self._is_rate_limited_memory(rate_key, limit, window)
    
    def block_ip(self, ip_address, duration=3600):
        """Temporarily block an IP address"""
        client_id = f"ip:{ip_address}"
        self.blocked_ips.add(client_id)
        
        # Set expiration using Redis if available
        if self.redis:
            try:
                self.redis.setex(f"blocked_ip:{ip_address}", duration, "1")
            except Exception as e:
                logger.warning(f"Failed to store IP block in Redis: {e}")
        
        # Remove from memory after duration (simplified)
        logger.info(f"IP {ip_address} blocked for {duration} seconds")
    
    def get_rate_limit_info(self, endpoint, client_id=None):
        """Get current rate limit status"""
        if not client_id:
            client_id = self._get_client_id()
        
        rate_key = f"rate_limit:{endpoint}:{client_id}"
        
        try:
            if self.redis:
                current_time = time.time()
                # Count requests in last minute
                count = self.redis.zcount(rate_key, current_time - 60, current_time)
                return {'requests_in_window': count, 'client_id': client_id}
            else:
                count = len(self.memory_store.get(rate_key, []))
                return {'requests_in_window': count, 'client_id': client_id}
        except Exception:
            return {'requests_in_window': 0, 'client_id': client_id}

# Rate limiting configurations
RATE_LIMITS = {
    'default': {'limit': 100, 'window': 3600},  # 100 requests per hour
    'api_upload': {'limit': 10, 'window': 300},  # 10 uploads per 5 minutes
    'api_login': {'limit': 5, 'window': 300},    # 5 login attempts per 5 minutes
    'api_register': {'limit': 3, 'window': 3600}, # 3 registrations per hour
    'api_password_reset': {'limit': 3, 'window': 3600},
    'api_financial_reports': {'limit': 20, 'window': 300},
    'api_bank_reconciliation': {'limit': 15, 'window': 300},
    'api_manual_journal': {'limit': 30, 'window': 300},
    'api_search': {'limit': 50, 'window': 300}
}

def rate_limit(endpoint=None, limit=None, window=None):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rate_limiter = getattr(current_app, 'rate_limiter', None)
            if not rate_limiter:
                return f(*args, **kwargs)
            
            # Determine rate limit configuration
            endpoint_name = endpoint or f.__name__
            config = RATE_LIMITS.get(endpoint_name, RATE_LIMITS['default'])
            
            actual_limit = limit or config['limit']
            actual_window = window or config['window']
            
            # Check rate limit
            if rate_limiter.is_rate_limited(endpoint_name, actual_limit, actual_window):
                # Log rate limit violation
                client_id = rate_limiter._get_client_id()
                logger.warning(f"Rate limit exceeded for {client_id} on {endpoint_name}")
                
                # Return rate limit error
                return jsonify({
                    'success': False,
                    'error': 'Rate Limit Exceeded',
                    'message': f'Too many requests. Limit: {actual_limit} per {actual_window} seconds',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'retry_after': actual_window,
                    'timestamp': datetime.utcnow().isoformat()
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            
            # Get current rate limit info
            rate_info = rate_limiter.get_rate_limit_info(endpoint_name)
            
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(actual_limit)
                response.headers['X-RateLimit-Remaining'] = str(max(0, actual_limit - rate_info['requests_in_window']))
                response.headers['X-RateLimit-Reset'] = str(int(time.time() + actual_window))
            
            return response
        return decorated_function
    return decorator

def adaptive_rate_limit(base_limit=100, base_window=3600):
    """Adaptive rate limiting based on system load"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rate_limiter = getattr(current_app, 'rate_limiter', None)
            if not rate_limiter:
                return f(*args, **kwargs)
            
            # Adjust limits based on system metrics (simplified)
            # In production, you might check CPU usage, memory, etc.
            system_load = 1.0  # Placeholder for actual system load
            
            adjusted_limit = int(base_limit * (2.0 - system_load))
            adjusted_window = base_window
            
            endpoint_name = f.__name__
            
            if rate_limiter.is_rate_limited(endpoint_name, adjusted_limit, adjusted_window):
                return jsonify({
                    'success': False,
                    'error': 'Rate Limit Exceeded',
                    'message': f'System under high load. Limit: {adjusted_limit} per {adjusted_window} seconds',
                    'code': 'ADAPTIVE_RATE_LIMIT_EXCEEDED',
                    'retry_after': adjusted_window,
                    'timestamp': datetime.utcnow().isoformat()
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def setup_rate_limiting(app):
    """Initialize rate limiting"""
    try:
        redis_client = getattr(app, 'redis', None)
        rate_limiter = RateLimiter(redis_client)
        app.rate_limiter = rate_limiter
        
        logger.info("Rate limiting initialized successfully")
        return rate_limiter
        
    except Exception as e:
        logger.error(f"Failed to initialize rate limiting: {e}")
        return None

class SecurityMiddleware:
    """Security middleware for additional protection"""
    
    @staticmethod
    def detect_suspicious_activity(client_id, endpoint):
        """Detect suspicious activity patterns"""
        # This is a simplified implementation
        # In production, you might use ML models or more sophisticated detection
        
        suspicious_patterns = [
            'sql injection keywords',
            'xss attempts',
            'path traversal',
            'rapid consecutive requests'
        ]
        
        # Log suspicious activity
        logger.warning(f"Potential suspicious activity from {client_id} on {endpoint}")
        
        return False  # Return True if activity is suspicious
    
    @staticmethod
    def apply_security_headers(response):
        """Apply security headers to response"""
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
