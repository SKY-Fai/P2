
"""
F-AI Accountant - Comprehensive API Documentation Generator
Automatically generates OpenAPI/Swagger documentation for all endpoints
"""

import json
import os
from datetime import datetime
from flask import Blueprint, jsonify, render_template_string

api_docs_bp = Blueprint('api_docs', __name__)

class APIDocumentationGenerator:
    """Generate comprehensive API documentation"""
    
    def __init__(self, app=None):
        self.app = app
        self.endpoints = {}
        self.schemas = {}
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self.collect_endpoints()
        
    def collect_endpoints(self):
        """Collect all API endpoints and their metadata"""
        if not self.app:
            return
            
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.startswith('api') or '/api/' in rule.rule:
                endpoint_info = {
                    'path': rule.rule,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                    'endpoint': rule.endpoint,
                    'description': self._get_endpoint_description(rule.endpoint),
                    'parameters': self._extract_parameters(rule.rule),
                    'request_schema': self._get_request_schema(rule.endpoint),
                    'response_schema': self._get_response_schema(rule.endpoint),
                    'examples': self._get_examples(rule.endpoint)
                }
                self.endpoints[rule.endpoint] = endpoint_info
    
    def _get_endpoint_description(self, endpoint):
        """Get endpoint description from docstring or endpoint name"""
        descriptions = {
            'api_upload': 'Upload and process accounting files',
            'api_manual_journal': 'Create manual journal entries',
            'api_bank_reconciliation': 'Bank reconciliation operations',
            'api_financial_reports': 'Generate financial reports',
            'api_ai_insights': 'Get AI-powered financial insights',
            'api_validation': 'Data validation operations',
            'api_dashboard_stats': 'Get dashboard statistics',
            'api_chart_of_accounts': 'Chart of accounts operations',
            'api_professional_codes': 'Professional user codes management',
            'api_audit_trail': 'Audit trail and logging',
            'api_templates': 'Template management operations'
        }
        
        return descriptions.get(endpoint, f"API endpoint: {endpoint}")
    
    def _extract_parameters(self, path):
        """Extract path and query parameters"""
        import re
        path_params = re.findall(r'<([^>]+)>', path)
        
        parameters = []
        for param in path_params:
            param_type = 'string'
            param_name = param
            
            if ':' in param:
                param_type, param_name = param.split(':', 1)
            
            parameters.append({
                'name': param_name,
                'in': 'path',
                'required': True,
                'type': param_type,
                'description': f'Path parameter: {param_name}'
            })
        
        return parameters
    
    def _get_request_schema(self, endpoint):
        """Get request schema for endpoint"""
        schemas = {
            'api_manual_journal': {
                'type': 'object',
                'required': ['date', 'description', 'entries'],
                'properties': {
                    'date': {'type': 'string', 'format': 'date', 'example': '2024-01-15'},
                    'description': {'type': 'string', 'example': 'Office supplies purchase'},
                    'reference': {'type': 'string', 'example': 'REF-001'},
                    'entries': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'account_code': {'type': 'string', 'example': '5001'},
                                'description': {'type': 'string', 'example': 'Office expenses'},
                                'debit_amount': {'type': 'number', 'example': 1000.00},
                                'credit_amount': {'type': 'number', 'example': 0.00}
                            }
                        }
                    }
                }
            },
            'api_bank_reconciliation': {
                'type': 'object',
                'required': ['transaction_id', 'account_code'],
                'properties': {
                    'transaction_id': {'type': 'string', 'example': 'TXN-001'},
                    'account_code': {'type': 'string', 'example': '1100'},
                    'notes': {'type': 'string', 'example': 'Manual mapping'}
                }
            }
        }
        
        return schemas.get(endpoint, {})
    
    def _get_response_schema(self, endpoint):
        """Get response schema for endpoint"""
        return {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean', 'example': True},
                'message': {'type': 'string', 'example': 'Operation completed successfully'},
                'data': {'type': 'object', 'description': 'Response data'},
                'timestamp': {'type': 'string', 'format': 'date-time'}
            }
        }
    
    def _get_examples(self, endpoint):
        """Get request/response examples"""
        examples = {
            'api_manual_journal': {
                'request': {
                    'date': '2024-01-15',
                    'description': 'Office supplies purchase',
                    'reference': 'REF-001',
                    'entries': [
                        {
                            'account_code': '5001',
                            'description': 'Office expenses',
                            'debit_amount': 1000.00,
                            'credit_amount': 0.00
                        },
                        {
                            'account_code': '1100',
                            'description': 'Cash payment',
                            'debit_amount': 0.00,
                            'credit_amount': 1000.00
                        }
                    ]
                },
                'response': {
                    'success': True,
                    'message': 'Journal entry created successfully',
                    'data': {
                        'journal_id': 'JE-001',
                        'status': 'pending_review'
                    }
                }
            }
        }
        
        return examples.get(endpoint, {})
    
    def generate_openapi_spec(self):
        """Generate OpenAPI 3.0 specification"""
        spec = {
            'openapi': '3.0.0',
            'info': {
                'title': 'F-AI Accountant API',
                'version': '2.0.0',
                'description': 'Comprehensive API for F-AI Accountant - AI-powered accounting automation platform',
                'contact': {
                    'name': 'F-AI Support',
                    'email': 'support@f-ai.com'
                }
            },
            'servers': [
                {
                    'url': '/api',
                    'description': 'API Server'
                }
            ],
            'paths': {},
            'components': {
                'schemas': self._generate_schemas(),
                'securitySchemes': {
                    'sessionAuth': {
                        'type': 'apiKey',
                        'in': 'cookie',
                        'name': 'session'
                    }
                }
            }
        }
        
        # Generate paths
        for endpoint, info in self.endpoints.items():
            path = info['path'].replace('/api', '')
            if path not in spec['paths']:
                spec['paths'][path] = {}
            
            for method in info['methods']:
                spec['paths'][path][method.lower()] = {
                    'summary': info['description'],
                    'description': info['description'],
                    'parameters': info['parameters'],
                    'responses': {
                        '200': {
                            'description': 'Successful response',
                            'content': {
                                'application/json': {
                                    'schema': info['response_schema']
                                }
                            }
                        },
                        '400': {'description': 'Bad request'},
                        '401': {'description': 'Unauthorized'},
                        '429': {'description': 'Rate limit exceeded'},
                        '500': {'description': 'Internal server error'}
                    }
                }
                
                # Add request body for POST/PUT methods
                if method in ['POST', 'PUT'] and info['request_schema']:
                    spec['paths'][path][method.lower()]['requestBody'] = {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': info['request_schema']
                            }
                        }
                    }
        
        return spec
    
    def _generate_schemas(self):
        """Generate common data schemas"""
        return {
            'ErrorResponse': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string'},
                    'message': {'type': 'string'},
                    'code': {'type': 'string'},
                    'timestamp': {'type': 'string', 'format': 'date-time'}
                }
            },
            'SuccessResponse': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'message': {'type': 'string'},
                    'data': {'type': 'object'},
                    'timestamp': {'type': 'string', 'format': 'date-time'}
                }
            },
            'JournalEntry': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'date': {'type': 'string', 'format': 'date'},
                    'description': {'type': 'string'},
                    'reference': {'type': 'string'},
                    'total_debit': {'type': 'number'},
                    'total_credit': {'type': 'number'},
                    'status': {'type': 'string', 'enum': ['draft', 'pending_review', 'approved', 'posted']}
                }
            },
            'Account': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'string'},
                    'name': {'type': 'string'},
                    'type': {'type': 'string', 'enum': ['assets', 'liabilities', 'equity', 'revenue', 'expenses']},
                    'balance': {'type': 'number'}
                }
            }
        }
    
    def save_documentation(self, output_dir='docs/api'):
        """Save documentation to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save OpenAPI spec
        spec = self.generate_openapi_spec()
        with open(os.path.join(output_dir, 'openapi.json'), 'w') as f:
            json.dump(spec, f, indent=2)
        
        # Generate HTML documentation
        html_doc = self.generate_html_documentation()
        with open(os.path.join(output_dir, 'index.html'), 'w') as f:
            f.write(html_doc)
        
        # Generate markdown documentation
        md_doc = self.generate_markdown_documentation()
        with open(os.path.join(output_dir, 'README.md'), 'w') as f:
            f.write(md_doc)
        
        print(f"API documentation saved to {output_dir}")
    
    def generate_html_documentation(self):
        """Generate HTML documentation"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>F-AI Accountant API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .endpoint { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
        .method { font-weight: bold; color: #007bff; }
        .path { font-family: monospace; background: #f8f9fa; padding: 5px; }
        pre { background: #f8f9fa; padding: 10px; overflow-x: auto; }
        .parameter { margin: 10px 0; }
    </style>
</head>
<body>
    <h1>F-AI Accountant API Documentation</h1>
    <p>Generated on: {{ timestamp }}</p>
    
    <h2>Overview</h2>
    <p>This documentation covers all API endpoints for the F-AI Accountant platform.</p>
    
    <h2>Authentication</h2>
    <p>Most endpoints require session-based authentication. Include session cookie in requests.</p>
    
    <h2>Rate Limiting</h2>
    <p>API requests are rate limited. Check response headers for current limits.</p>
    
    <h2>Endpoints</h2>
    {% for endpoint, info in endpoints.items() %}
    <div class="endpoint">
        <h3>{{ info.description }}</h3>
        {% for method in info.methods %}
        <p><span class="method">{{ method }}</span> <span class="path">{{ info.path }}</span></p>
        {% endfor %}
        
        {% if info.parameters %}
        <h4>Parameters</h4>
        {% for param in info.parameters %}
        <div class="parameter">
            <strong>{{ param.name }}</strong> ({{ param.type }}) - {{ param.description }}
        </div>
        {% endfor %}
        {% endif %}
        
        {% if info.examples %}
        <h4>Example Request</h4>
        <pre>{{ info.examples.request | tojson(indent=2) }}</pre>
        
        <h4>Example Response</h4>
        <pre>{{ info.examples.response | tojson(indent=2) }}</pre>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
        """
        
        from jinja2 import Template
        template = Template(template)
        
        return template.render(
            endpoints=self.endpoints,
            timestamp=datetime.now().isoformat()
        )
    
    def generate_markdown_documentation(self):
        """Generate Markdown documentation"""
        md_content = f"""# F-AI Accountant API Documentation

Generated on: {datetime.now().isoformat()}

## Overview

The F-AI Accountant API provides comprehensive endpoints for accounting automation, including:

- Manual journal entry management
- Bank reconciliation
- Financial report generation
- AI-powered insights
- File upload and processing
- Audit trail management

## Base URL

All API endpoints are prefixed with `/api`

## Authentication

Most endpoints require session-based authentication. Include the session cookie in your requests.

## Rate Limiting

API requests are rate limited based on endpoint and user type:

- Default: 100 requests per hour
- File uploads: 10 requests per 5 minutes  
- Login attempts: 5 requests per 5 minutes
- Report generation: 20 requests per 5 minutes

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Time when limit resets

## Error Handling

All endpoints return consistent error responses:

```json
{{
    "success": false,
    "error": "Error Type",
    "message": "Human readable error message",
    "code": "ERROR_CODE",
    "timestamp": "2024-01-15T10:30:00Z"
}}
```

Common error codes:
- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_ERROR`: Authentication required
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `INTERNAL_SERVER_ERROR`: Unexpected server error

## Endpoints

"""
        
        for endpoint, info in self.endpoints.items():
            md_content += f"""### {info['description']}

**Methods:** {', '.join(info['methods'])}  
**Path:** `{info['path']}`

"""
            
            if info['parameters']:
                md_content += "**Parameters:**\n\n"
                for param in info['parameters']:
                    md_content += f"- `{param['name']}` ({param['type']}) - {param['description']}\n"
                md_content += "\n"
            
            if info['examples']:
                if 'request' in info['examples']:
                    md_content += "**Example Request:**\n\n```json\n"
                    md_content += json.dumps(info['examples']['request'], indent=2)
                    md_content += "\n```\n\n"
                
                if 'response' in info['examples']:
                    md_content += "**Example Response:**\n\n```json\n"
                    md_content += json.dumps(info['examples']['response'], indent=2)
                    md_content += "\n```\n\n"
            
            md_content += "---\n\n"
        
        return md_content

@api_docs_bp.route('/api/docs')
def api_documentation():
    """Serve API documentation"""
    doc_generator = APIDocumentationGenerator()
    doc_generator.init_app(current_app)
    
    return jsonify({
        'success': True,
        'documentation': {
            'openapi_spec': doc_generator.generate_openapi_spec(),
            'endpoints_count': len(doc_generator.endpoints),
            'generated_at': datetime.now().isoformat()
        }
    })

@api_docs_bp.route('/api/docs/swagger')
def swagger_ui():
    """Serve Swagger UI for interactive documentation"""
    swagger_template = """
<!DOCTYPE html>
<html>
<head>
    <title>F-AI Accountant API</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({
            url: '/api/docs/openapi.json',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ]
        });
    </script>
</body>
</html>
    """
    return swagger_template

@api_docs_bp.route('/api/docs/openapi.json')
def openapi_spec():
    """Serve OpenAPI specification"""
    doc_generator = APIDocumentationGenerator()
    doc_generator.init_app(current_app)
    
    return jsonify(doc_generator.generate_openapi_spec())
