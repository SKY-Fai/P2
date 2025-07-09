
import re
from flask import request, jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class InputValidator:
    @staticmethod
    def sanitize_string(value, max_length=255):
        """Sanitize string input"""
        if not isinstance(value, str):
            return ""
        
        # Remove dangerous characters
        value = re.sub(r'[<>"\']', '', value)
        # Limit length
        return value[:max_length].strip()
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_number(value, min_val=None, max_val=None):
        """Validate numeric input"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False

def validate_input(schema):
    """Decorator for input validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() or {}
            errors = []
            
            for field, rules in schema.items():
                if field not in data and rules.get('required', False):
                    errors.append(f"{field} is required")
                    continue
                
                if field in data:
                    value = data[field]
                    
                    # Type validation
                    if 'type' in rules:
                        if rules['type'] == 'string' and not isinstance(value, str):
                            errors.append(f"{field} must be a string")
                        elif rules['type'] == 'number' and not isinstance(value, (int, float)):
                            errors.append(f"{field} must be a number")
                    
                    # Length validation
                    if 'max_length' in rules and isinstance(value, str):
                        if len(value) > rules['max_length']:
                            errors.append(f"{field} exceeds maximum length")
            
            if errors:
                return jsonify({'errors': errors}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
