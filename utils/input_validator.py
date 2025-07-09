
import re
import html
import json
import logging
from functools import wraps
from flask import request, jsonify
from datetime import datetime
import bleach

logger = logging.getLogger(__name__)

class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # Validation patterns
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^\+?[1-9]\d{1,14}$',
        'username': r'^[a-zA-Z0-9_]{3,20}$',
        'amount': r'^\d+(\.\d{1,2})?$',
        'date': r'^\d{4}-\d{2}-\d{2}$',
        'account_code': r'^[A-Z0-9]{2,10}$',
        'invoice_number': r'^[A-Za-z0-9\-/_]{1,50}$',
        'safe_text': r'^[a-zA-Z0-9\s\-_.,()]{1,200}$'
    }
    
    # Allowed HTML tags for rich text
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def sanitize_string(value, max_length=1000):
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value) if value is not None else ""
        
        # HTML escape
        sanitized = html.escape(value.strip())
        
        # Remove control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        # Truncate to max length
        return sanitized[:max_length]
    
    @staticmethod
    def sanitize_html(value):
        """Sanitize HTML content"""
        if not isinstance(value, str):
            return ""
        
        return bleach.clean(
            value,
            tags=InputValidator.ALLOWED_TAGS,
            attributes=InputValidator.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def validate_pattern(value, pattern_name):
        """Validate value against pattern"""
        if pattern_name not in InputValidator.PATTERNS:
            return False
        
        pattern = InputValidator.PATTERNS[pattern_name]
        return bool(re.match(pattern, str(value))) if value else False
    
    @staticmethod
    def validate_email(email):
        """Validate email address"""
        return InputValidator.validate_pattern(email, 'email')
    
    @staticmethod
    def validate_amount(amount):
        """Validate monetary amount"""
        try:
            if isinstance(amount, str):
                # Remove common currency symbols and spaces
                cleaned = re.sub(r'[₹$€£,\s]', '', amount)
                amount = float(cleaned)
            else:
                amount = float(amount)
            
            # Check reasonable range
            if 0 <= amount <= 999999999.99:
                return round(amount, 2)
            return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_date(date_string):
        """Validate date format"""
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_json(json_string):
        """Validate JSON string"""
        try:
            json.loads(json_string)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize uploaded filename"""
        if not filename:
            return None
        
        # Remove path separators and dangerous characters
        safe_chars = re.compile(r'[^a-zA-Z0-9._-]')
        sanitized = safe_chars.sub('_', filename)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:240] + ('.' + ext if ext else '')
        
        return sanitized
    
    @staticmethod
    def validate_file_extension(filename, allowed_extensions):
        """Validate file extension"""
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        return extension in allowed_extensions

class ValidationSchema:
    """Schema-based validation"""
    
    def __init__(self, schema):
        self.schema = schema
    
    def validate(self, data):
        """Validate data against schema"""
        errors = []
        validated_data = {}
        
        for field, rules in self.schema.items():
            value = data.get(field)
            
            # Check required fields
            if rules.get('required', False) and (value is None or value == ''):
                errors.append(f"Field '{field}' is required")
                continue
            
            # Skip validation if field is optional and empty
            if value is None or value == '':
                validated_data[field] = None
                continue
            
            # Type validation
            field_type = rules.get('type', 'string')
            if field_type == 'string':
                value = InputValidator.sanitize_string(value, rules.get('max_length', 1000))
            elif field_type == 'email':
                if not InputValidator.validate_email(value):
                    errors.append(f"Field '{field}' must be a valid email")
                    continue
                value = InputValidator.sanitize_string(value)
            elif field_type == 'amount':
                value = InputValidator.validate_amount(value)
                if value is None:
                    errors.append(f"Field '{field}' must be a valid amount")
                    continue
            elif field_type == 'date':
                if not InputValidator.validate_date(value):
                    errors.append(f"Field '{field}' must be a valid date (YYYY-MM-DD)")
                    continue
            elif field_type == 'integer':
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' must be an integer")
                    continue
            elif field_type == 'float':
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' must be a number")
                    continue
            
            # Pattern validation
            if 'pattern' in rules:
                if not InputValidator.validate_pattern(value, rules['pattern']):
                    errors.append(f"Field '{field}' format is invalid")
                    continue
            
            # Custom validation
            if 'validator' in rules:
                if not rules['validator'](value):
                    errors.append(f"Field '{field}' validation failed")
                    continue
            
            validated_data[field] = value
        
        return validated_data, errors

def validate_input(schema):
    """Decorator for input validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get request data
            if request.is_json:
                data = request.get_json() or {}
            else:
                data = request.form.to_dict()
            
            # Validate input
            validator = ValidationSchema(schema)
            validated_data, errors = validator.validate(data)
            
            if errors:
                return jsonify({
                    'success': False,
                    'error': 'Validation Error',
                    'message': 'Input validation failed',
                    'validation_errors': errors,
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
            
            # Add validated data to request
            request.validated_data = validated_data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_request_data():
    """Middleware to sanitize all request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Sanitize form data
            if request.form:
                sanitized_form = {}
                for key, value in request.form.items():
                    sanitized_form[key] = InputValidator.sanitize_string(value)
                request.sanitized_form = sanitized_form
            
            # Sanitize JSON data
            if request.is_json:
                data = request.get_json()
                if isinstance(data, dict):
                    sanitized_json = {}
                    for key, value in data.items():
                        if isinstance(value, str):
                            sanitized_json[key] = InputValidator.sanitize_string(value)
                        else:
                            sanitized_json[key] = value
                    request.sanitized_json = sanitized_json
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Common validation schemas
COMMON_SCHEMAS = {
    'user_registration': {
        'username': {'required': True, 'type': 'string', 'pattern': 'username'},
        'email': {'required': True, 'type': 'email'},
        'password': {'required': True, 'type': 'string', 'min_length': 8},
        'full_name': {'required': True, 'type': 'string', 'max_length': 100}
    },
    'manual_journal_entry': {
        'date': {'required': True, 'type': 'date'},
        'description': {'required': True, 'type': 'string', 'max_length': 200},
        'reference': {'required': False, 'type': 'string', 'max_length': 50},
        'entries': {'required': True, 'type': 'array'}
    },
    'file_upload': {
        'description': {'required': False, 'type': 'string', 'max_length': 500},
        'template_type': {'required': False, 'type': 'string', 'max_length': 50}
    },
    'bank_transaction': {
        'transaction_date': {'required': True, 'type': 'date'},
        'description': {'required': True, 'type': 'string', 'max_length': 200},
        'amount': {'required': True, 'type': 'amount'},
        'account_code': {'required': True, 'type': 'string', 'pattern': 'account_code'}
    }
}
