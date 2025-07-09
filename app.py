
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.pool import QueuePool
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging for production
logging.basicConfig(
    level=logging.INFO if os.environ.get('FLASK_ENV') == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Production Configuration
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get("WTF_CSRF_SECRET_KEY", "dev-csrf-key")
    
    # Database Configuration for Neon DB
    database_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
    
    if database_url and database_url.startswith('postgresql'):
        # Production Neon DB configuration
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "poolclass": QueuePool,
            "pool_size": 10,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
            "connect_args": {
                "sslmode": os.environ.get("PGSSLMODE", "require"),
                "options": "-c timezone=utc"
            }
        }
    else:
        # Fallback to SQLite for development
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///accufin360.db"
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  
    
    # File upload directories
    upload_folder = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads")
    reports_folder = os.environ.get("REPORTS_FOLDER", "/tmp/reports")
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["REPORTS_FOLDER"] = reports_folder

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(reports_folder, exist_ok=True)
    
    # Redis configuration for caching
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        app.redis = redis.from_url(redis_url, decode_responses=True)
        app.redis.ping()
        logging.info("Redis connection established")
    except Exception as e:
        logging.warning(f"Redis connection failed: {e}. Proceeding without caching.")
        app.redis = None
    
    # Initialize enhanced error handling, logging, caching, and rate limiting
    from utils.api_error_handler import register_api_error_handlers
    from utils.logging_config import setup_logging
    from utils.caching_layer import setup_caching
    from utils.rate_limiter import setup_rate_limiting
    
    # Setup structured logging
    setup_logging(app)
    
    # Setup caching layer
    setup_caching(app)
    
    # Setup rate limiting
    setup_rate_limiting(app)
    
    # Register enhanced error handlers
    register_api_error_handlers(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    
    # Proxy fix for GCP App Engine
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        logging.warning(f"404 error: {error}")
        return {"error": "Resource not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"500 error: {error}")
        db.session.rollback()
        return {"error": "Internal server error"}, 500
    
    @app.errorhandler(429)
    def rate_limit_error(error):
        logging.warning(f"Rate limit exceeded: {error}")
        return {"error": "Rate limit exceeded"}, 429
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            
        # Check Redis connection
        redis_status = "healthy" if app.redis and app.redis.ping() else "unavailable"
        
        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "database": db_status,
            "redis": redis_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Add request middleware
    @app.before_request
    def before_request():
        import uuid
        from flask import g
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()
    
    @app.after_request  
    def after_request(response):
        from flask import g
        from utils.logging_config import APILogger
        from utils.rate_limiter import SecurityMiddleware
        
        # Log API access
        if hasattr(g, 'start_time'):
            response_time = (time.time() - g.start_time) * 1000
            APILogger.log_response(
                endpoint=request.endpoint,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                user_id=getattr(g, 'current_user', {}).get('id')
            )
        
        # Apply security headers
        SecurityMiddleware.apply_security_headers(response)
        
        # Add request ID to response
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    # Register blueprints
    from auth import auth_bp
    from routes import main_bp
    from admin_routes import admin_bp
    from docs.api_documentation import api_docs_bp
    
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_docs_bp)
    
    # Create database tables
    with app.app_context():
        import models  
        import permissions_models  
        try:
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
    
    return app

# Create app instance
app = create_app()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
