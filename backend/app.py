"""
SOAR Platform - Main Flask Application
Entry point for the Security Orchestration, Automation, and Response platform
"""
import os
import logging
from logging.config import dictConfig
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
from sqlalchemy import text

from backend.config import get_config
from backend.models import db
from backend.auth import login_manager, init_default_users

# Load environment variables
load_dotenv()

# Configure logging
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/soar_platform.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'default'
        }
    },
    'root': {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'handlers': ['console', 'file']
    }
})


def create_app(config_name: str = None) -> Flask:
    """Application factory pattern"""
    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')

    # Load configuration
    if config_name is None:
        config_name = os.getenv('ENVIRONMENT', 'development')

    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_routes.login'

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Initialize database
    with app.app_context():
        db.create_all()
        init_default_users(app)

    # Log application startup
    app.logger.info(f"SOAR Platform started in {config_name} mode")

    return app


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints"""
    from backend.routes.incidents import incidents_bp
    from backend.routes.playbooks import playbooks_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.auth_routes import auth_bp

    app.register_blueprint(incidents_bp, url_prefix='/api/v1/incidents')
    app.register_blueprint(playbooks_bp, url_prefix='/api/v1/playbooks')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    # Main routes
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('dashboard.html')

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Check database connection
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            db_status = 'healthy'
        except Exception as e:
            app.logger.error(f"Database health check failed: {e}")
            db_status = 'unhealthy'

        return jsonify({
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'components': {
                'database': db_status,
                'api': 'healthy'
            }
        }), 200 if db_status == 'healthy' else 503

    @app.route('/api/v1/status')
    def api_status():
        """API status endpoint"""
        return jsonify({
            'api_version': 'v1',
            'platform': 'SOAR',
            'environment': app.config.get('ENVIRONMENT', 'development'),
            'timestamp': datetime.utcnow().isoformat()
        })


def register_error_handlers(app: Flask) -> None:
    """Register error handlers"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error)
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Insufficient permissions'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error) if app.debug else 'An unexpected error occurred'
        }), 500


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config.get('APP_HOST', '0.0.0.0'),
        port=app.config.get('APP_PORT', 5000),
        debug=app.config.get('DEBUG', False)
    )
