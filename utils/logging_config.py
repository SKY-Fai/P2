
import logging
import logging.handlers
import json
import os
from datetime import datetime
from flask import request, g
import traceback

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        if request:
            log_data.update({
                'request_id': getattr(g, 'request_id', None),
                'url': request.url,
                'method': request.method,
                'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                'user_agent': request.headers.get('User-Agent')
            })
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)

def setup_logging(app):
    """Configure structured logging for the application"""
    
    # Create logs directory
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if app.config.get('FLASK_ENV') == 'production' else logging.DEBUG)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with structured format
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler for application logs
    app_log_file = os.path.join(log_dir, 'app.log')
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    app_handler.setFormatter(StructuredFormatter())
    app_handler.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)
    
    # Error log file
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setFormatter(StructuredFormatter())
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # API access log
    api_log_file = os.path.join(log_dir, 'api_access.log')
    api_handler = logging.handlers.RotatingFileHandler(
        api_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    api_handler.setFormatter(StructuredFormatter())
    
    # Create API logger
    api_logger = logging.getLogger('api_access')
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = False
    
    # Performance log
    perf_log_file = os.path.join(log_dir, 'performance.log')
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    perf_handler.setFormatter(StructuredFormatter())
    
    perf_logger = logging.getLogger('performance')
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)
    perf_logger.propagate = False
    
    app.logger.info("Structured logging configured successfully")

class APILogger:
    """Structured API logging utility"""
    
    @staticmethod
    def log_request(endpoint, method, user_id=None, extra_data=None):
        """Log API request"""
        logger = logging.getLogger('api_access')
        log_data = {
            'event_type': 'api_request',
            'endpoint': endpoint,
            'method': method,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        if extra_data:
            log_data.update(extra_data)
        
        logger.info("API Request", extra={'extra_data': log_data})
    
    @staticmethod
    def log_response(endpoint, method, status_code, response_time, user_id=None):
        """Log API response"""
        logger = logging.getLogger('api_access')
        log_data = {
            'event_type': 'api_response',
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time_ms': response_time,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("API Response", extra={'extra_data': log_data})
    
    @staticmethod
    def log_performance(operation, duration, success=True, extra_data=None):
        """Log performance metrics"""
        logger = logging.getLogger('performance')
        log_data = {
            'event_type': 'performance_metric',
            'operation': operation,
            'duration_ms': duration,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        if extra_data:
            log_data.update(extra_data)
        
        logger.info("Performance Metric", extra={'extra_data': log_data})
