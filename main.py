
#!/usr/bin/env python3
"""
F-AI Accountant - Main Application Entry Point
Production-ready Flask application with comprehensive error handling
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging before importing app modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fai_accountant.log')
    ]
)

logger = logging.getLogger(__name__)

try:
    from app import create_app
    from utils.error_handlers import register_error_handlers
    
    # Create Flask application
    app = create_app()
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add startup logging
    with app.app_context():
        logger.info("F-AI Accountant application started")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        logger.info(f"Database URL configured: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
        logger.info(f"Redis configured: {'Yes' if hasattr(app, 'redis') and app.redis else 'No'}")
    
    if __name__ == '__main__':
        # Development server configuration
        debug_mode = os.environ.get('FLASK_ENV') != 'production'
        port = int(os.environ.get('PORT', 8080))
        host = '0.0.0.0'  # Required for Replit
        
        logger.info(f"Starting F-AI Accountant on {host}:{port}")
        logger.info(f"Debug mode: {debug_mode}")
        
        try:
            app.run(
                host=host,
                port=port,
                debug=debug_mode,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            sys.exit(1)

except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    logger.error(f"Application startup failed: {e}")
    sys.exit(1)
