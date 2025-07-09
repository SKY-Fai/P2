
import logging
import traceback
from functools import wraps
from flask import jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import RequestEntityTooLarge, BadRequest
from datetime import datetime
import redis

logger = logging.getLogger(__name__)

class APIErrorHandler:
    """Centralized API error handling with structured logging"""
    
    ERROR_CODES = {
        'VALIDATION_ERROR': 400,
        'AUTHENTICATION_ERROR': 401,
        'AUTHORIZATION_ERROR': 403,
        'RESOURCE_NOT_FOUND': 404,
        'METHOD_NOT_ALLOWED': 405,
        'REQUEST_TIMEOUT': 408,
        'CONFLICT': 409,
        'PAYLOAD_TOO_LARGE': 413,
        'RATE_LIMIT_EXCEEDED': 429,
        'INTERNAL_SERVER_ERROR': 500,
        'SERVICE_UNAVAILABLE': 503
    }
    
    @staticmethod
    def log_structured_error(error, context="", user_id=None, request_id=None):
        """Log error with structured information"""
        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'user_id': user_id,
            'request_id': request_id,
            'request_url': request.url if request else None,
            'request_method': request.method if request else None,
            'request_args': dict(request.args) if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr) if request else None,
            'stack_trace': traceback.format_exc() if current_app.debug else None
        }
        
        logger.error(f"API Error: {error_data}")
        
        # Store in Redis for monitoring (if available)
        try:
            if hasattr(current_app, 'redis') and current_app.redis:
                error_key = f"error_log:{datetime.utcnow().strftime('%Y-%m-%d')}"
                current_app.redis.lpush(error_key, str(error_data))
                current_app.redis.expire(error_key, 86400 * 7)  # Keep for 7 days
        except Exception:
            pass
    
    @staticmethod
    def handle_api_error(error, context=""):
        """Handle API errors with proper status codes and responses"""
        error_response = {
            'success': False,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': getattr(request, 'request_id', None)
        }
        
        if isinstance(error, ValueError):
            error_response.update({
                'error': 'Validation Error',
                'message': str(error),
                'code': 'VALIDATION_ERROR'
            })
            status_code = 400
            
        elif isinstance(error, IntegrityError):
            error_response.update({
                'error': 'Data Integrity Violation',
                'message': 'The operation violates database constraints',
                'code': 'INTEGRITY_VIOLATION'
            })
            status_code = 409
            
        elif isinstance(error, SQLAlchemyError):
            error_response.update({
                'error': 'Database Error',
                'message': 'Database operation failed',
                'code': 'DATABASE_ERROR'
            })
            status_code = 500
            
        elif isinstance(error, RequestEntityTooLarge):
            error_response.update({
                'error': 'File Too Large',
                'message': 'The uploaded file exceeds the maximum allowed size',
                'code': 'PAYLOAD_TOO_LARGE'
            })
            status_code = 413
            
        elif isinstance(error, PermissionError):
            error_response.update({
                'error': 'Access Denied',
                'message': 'You do not have permission to perform this action',
                'code': 'AUTHORIZATION_ERROR'
            })
            status_code = 403
            
        elif isinstance(error, FileNotFoundError):
            error_response.update({
                'error': 'Resource Not Found',
                'message': 'The requested resource does not exist',
                'code': 'RESOURCE_NOT_FOUND'
            })
            status_code = 404
            
        else:
            error_response.update({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred' if not current_app.debug else str(error),
                'code': 'INTERNAL_SERVER_ERROR'
            })
            status_code = 500
        
        APIErrorHandler.log_structured_error(error, context)
        return jsonify(error_response), status_code

def api_error_handler(context=""):
    """Decorator for API error handling"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                return APIErrorHandler.handle_api_error(e, f"{context} - {f.__name__}")
        return decorated_function
    return decorator

def register_api_error_handlers(app):
    """Register global API error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'code': 'BAD_REQUEST',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication is required',
            'code': 'AUTHENTICATION_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'code': 'AUTHORIZATION_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'code': 'RESOURCE_NOT_FOUND',
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'success': False,
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'code': 'RATE_LIMIT_EXCEEDED',
            'timestamp': datetime.utcnow().isoformat()
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        APIErrorHandler.log_structured_error(error, "Global 500 handler")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_SERVER_ERROR',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
