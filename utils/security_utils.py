
import re
import hashlib
import secrets
from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_filename(filename):
        """Validate uploaded filename"""
        # Remove dangerous characters
        safe_chars = re.compile(r'[^a-zA-Z0-9._-]')
        safe_filename = safe_chars.sub('_', filename)
        
        # Check file extension
        allowed_extensions = {'.xlsx', '.xls', '.csv', '.pdf', '.docx'}
        extension = '.' + safe_filename.rsplit('.', 1)[-1].lower() if '.' in safe_filename else ''
        
        if extension not in allowed_extensions:
            return None, "Invalid file type"
        
        return safe_filename, None
    
    @staticmethod
    def sanitize_input(input_string):
        """Sanitize user input"""
        if not input_string:
            return ""
        
        # Remove potential script tags and dangerous characters
        cleaned = re.sub(r'<script.*?</script>', '', input_string, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r'[<>"\']', '', cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def validate_amount(amount_str):
        """Validate monetary amount"""
        try:
            amount = float(amount_str)
            if amount < 0 or amount > 999999999.99:
                return None, "Amount out of valid range"
            return round(amount, 2), None
        except (ValueError, TypeError):
            return None, "Invalid amount format"
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)

class RateLimiter:
    """Rate limiting utility"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.memory_store = {}  # Fallback when Redis unavailable
    
    def is_rate_limited(self, key, limit=100, window=3600):
        """Check if request is rate limited"""
        current_time = datetime.utcnow()
        
        if self.redis:
            try:
                # Use Redis for distributed rate limiting
                pipe = self.redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, window)
                result = pipe.execute()
                
                if result[0] > limit:
                    return True
                return False
            except Exception as e:
                logger.warning(f"Redis rate limiting failed: {e}")
                # Fall back to memory store
        
        # Memory-based rate limiting (single instance)
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Clean old entries
        cutoff_time = current_time - timedelta(seconds=window)
        self.memory_store[key] = [
            timestamp for timestamp in self.memory_store[key] 
            if timestamp > cutoff_time
        ]
        
        # Check limit
        if len(self.memory_store[key]) >= limit:
            return True
        
        # Add current request
        self.memory_store[key].append(current_time)
        return False

def rate_limit(limit=100, per=3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            key = f"rate_limit:{client_ip}:{f.__name__}"
            
            # Check rate limit
            rate_limiter = RateLimiter(getattr(current_app, 'redis', None))
            if rate_limiter.is_rate_limited(key, limit, per):
                logger.warning(f"Rate limit exceeded for {client_ip} on {f.__name__}")
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_request_data(required_fields=None, optional_fields=None):
    """Request data validation decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() or {}
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        "error": "Missing required fields",
                        "missing_fields": missing_fields
                    }), 400
            
            # Sanitize all string inputs
            sanitized_data = {}
            allowed_fields = (required_fields or []) + (optional_fields or [])
            
            for field in allowed_fields:
                if field in data:
                    value = data[field]
                    if isinstance(value, str):
                        sanitized_data[field] = SecurityValidator.sanitize_input(value)
                    else:
                        sanitized_data[field] = value
            
            # Add sanitized data to request context
            request.validated_data = sanitized_data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
