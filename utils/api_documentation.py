
"""
F-AI Accountant API Documentation Generator
Generates comprehensive API documentation for all endpoints
"""

import json
from flask import Blueprint, jsonify, render_template_string

docs_bp = Blueprint('docs', __name__)

API_DOCUMENTATION = {
    "title": "F-AI Accountant Enterprise API",
    "version": "2.0.0",
    "description": "Complete Enterprise Accounting SaaS Platform API",
    "endpoints": {
        "/api/health": {
            "method": "GET",
            "description": "Health check endpoint",
            "parameters": {},
            "responses": {
                "200": {
                    "description": "Service health status",
                    "example": {
                        "status": "healthy",
                        "database": "healthy",
                        "timestamp": "2025-07-09T12:00:00Z"
                    }
                }
            }
        },
        "/api/upload": {
            "method": "POST",
            "description": "Upload accounting files",
            "parameters": {
                "file": {
                    "type": "file",
                    "required": True,
                    "description": "Excel or CSV file"
                }
            },
            "responses": {
                "200": {
                    "description": "File uploaded successfully",
                    "example": {
                        "status": "success",
                        "message": "File uploaded successfully",
                        "filename": "20250709_120000_data.xlsx"
                    }
                },
                "400": {
                    "description": "Invalid file or missing file",
                    "example": {
                        "error": "Invalid file type"
                    }
                }
            }
        },
        "/api/validation/status": {
            "method": "GET",
            "description": "Get validation system status",
            "parameters": {},
            "responses": {
                "200": {
                    "description": "Validation system status",
                    "example": {
                        "status": "ready",
                        "message": "Validation system ready",
                        "timestamp": "2025-07-09T12:00:00Z"
                    }
                }
            }
        },
        "/api/log-error": {
            "method": "POST",
            "description": "Log frontend errors",
            "parameters": {
                "message": {
                    "type": "string",
                    "required": True,
                    "description": "Error message"
                },
                "details": {
                    "type": "object",
                    "required": False,
                    "description": "Additional error details"
                }
            },
            "responses": {
                "200": {
                    "description": "Error logged successfully",
                    "example": {
                        "status": "success",
                        "message": "Error logged successfully"
                    }
                }
            }
        }
    }
}

@docs_bp.route('/api/docs')
def api_docs():
    """Return API documentation as JSON"""
    return jsonify(API_DOCUMENTATION)

@docs_bp.route('/docs')
def docs_page():
    """Return API documentation as HTML page"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>F-AI Accountant API Documentation</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
            .method { background: #007bff; color: white; padding: 5px 10px; border-radius: 3px; }
            .example { background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; }
            pre { background: #f1f1f1; padding: 10px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>{{ docs.title }}</h1>
        <p>{{ docs.description }}</p>
        <p>Version: {{ docs.version }}</p>
        
        {% for endpoint, details in docs.endpoints.items() %}
        <div class="endpoint">
            <h3><span class="method">{{ details.method }}</span> {{ endpoint }}</h3>
            <p>{{ details.description }}</p>
            
            {% if details.parameters %}
            <h4>Parameters:</h4>
            <ul>
                {% for param, info in details.parameters.items() %}
                <li><strong>{{ param }}</strong> ({{ info.type }}){% if info.required %} - Required{% endif %}: {{ info.description }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            
            <h4>Responses:</h4>
            {% for code, response in details.responses.items() %}
            <div class="example">
                <strong>{{ code }}:</strong> {{ response.description }}
                {% if response.example %}
                <pre>{{ response.example | tojson(indent=2) }}</pre>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </body>
    </html>
    """
    
    return render_template_string(html_template, docs=API_DOCUMENTATION)
