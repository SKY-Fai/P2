
import logging
import traceback
from functools import wraps
from flask import jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def log_error(error, context=""):
        """Log error with context information"""
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'request_url': request.url if request else None,
            'request_method': request.method if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr) if request else None
        }
        
        logger.error(f"Application Error: {error_info}")
        
        # In production, you might want to send this to an external monitoring service
        if current_app.config.get('FLASK_ENV') == 'production':
            # Example: send to external monitoring
            pass
    
    @staticmethod
    def handle_database_error(error):
        """Handle database-specific errors"""
        if isinstance(error, IntegrityError):
            return {
                'error': 'Data integrity violation',
                'message': 'The operation violates database constraints',
                'code': 'INTEGRITY_ERROR'
            }, 400
        elif isinstance(error, SQLAlchemyError):
            return {
                'error': 'Database operation failed',
                'message': 'Unable to complete database operation',
                'code': 'DATABASE_ERROR'
            }, 500
        else:
            return {
                'error': 'Unknown database error',
                'message': 'An unexpected database error occurred',
                'code': 'UNKNOWN_DB_ERROR'
            }, 500
    
    @staticmethod
    def handle_file_error(error):
        """Handle file operation errors"""
        if isinstance(error, RequestEntityTooLarge):
            return {
                'error': 'File too large',
                'message': 'The uploaded file exceeds the maximum allowed size',
                'code': 'FILE_TOO_LARGE'
            }, 413
        elif isinstance(error, PermissionError):
            return {
                'error': 'File permission denied',
                'message': 'Unable to access the requested file',
                'code': 'PERMISSION_DENIED'
            }, 403
        elif isinstance(error, FileNotFoundError):
            return {
                'error': 'File not found',
                'message': 'The requested file does not exist',
                'code': 'FILE_NOT_FOUND'
            }, 404
        else:
            return {
                'error': 'File operation failed',
                'message': 'An error occurred during file processing',
                'code': 'FILE_ERROR'
            }, 500

def handle_errors(f):
    """Decorator for comprehensive error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except SQLAlchemyError as e:
            ErrorHandler.log_error(e, f"Database error in {f.__name__}")
            response, status_code = ErrorHandler.handle_database_error(e)
            return jsonify(response), status_code
        except (FileNotFoundError, PermissionError, RequestEntityTooLarge) as e:
            ErrorHandler.log_error(e, f"File error in {f.__name__}")
            response, status_code = ErrorHandler.handle_file_error(e)
            return jsonify(response), status_code
        except ValueError as e:
            ErrorHandler.log_error(e, f"Validation error in {f.__name__}")
            return jsonify({
                'error': 'Invalid input',
                'message': str(e),
                'code': 'VALIDATION_ERROR'
            }), 400
        except Exception as e:
            ErrorHandler.log_error(e, f"Unexpected error in {f.__name__}")
            logger.error(f"Unexpected error in {f.__name__}: {traceback.format_exc()}")
            
            if current_app.config.get('FLASK_ENV') == 'production':
                return jsonify({
                    'error': 'Internal server error',
                    'message': 'An unexpected error occurred',
                    'code': 'INTERNAL_ERROR'
                }), 500
            else:
                return jsonify({
                    'error': 'Internal server error',
                    'message': str(e),
                    'code': 'INTERNAL_ERROR',
                    'traceback': traceback.format_exc()
                }), 500
    
    return decorated_function

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': 'The request could not be understood by the server',
            'code': 'BAD_REQUEST'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required',
            'code': 'UNAUTHORIZED'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'code': 'FORBIDDEN'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found',
            'code': 'NOT_FOUND'
        }), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'error': 'File too large',
            'message': 'The uploaded file exceeds the maximum allowed size',
            'code': 'FILE_TOO_LARGE'
        }), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'code': 'RATE_LIMIT_EXCEEDED'
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        ErrorHandler.log_error(error, "Global 500 handler")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500
