from flask import request, jsonify
from functools import wraps
import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_requests = 100  # requests per minute
        self.window = 60  # 60 seconds
        self.use_redis = False # Use in-memory fallback

    def is_allowed(self, key):
        now = time.time()
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] 
                             if now - req_time < self.window]

        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        return False

rate_limiter = RateLimiter()

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get client identifier
        client_id = request.remote_addr
        if hasattr(request, 'headers') and 'X-Forwarded-For' in request.headers:
            client_id = request.headers['X-Forwarded-For'].split(',')[0]

        if not rate_limiter.is_allowed(client_id):
            logger.warning(f"Rate limit exceeded for {client_id}")
            return jsonify({'error': 'Rate limit exceeded'}), 429

        return f(*args, **kwargs)
    return decorated_function