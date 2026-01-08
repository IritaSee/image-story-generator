from flask import Flask, render_template
from flask_cors import CORS
import os
import logging
from config import config
from utils.error_handlers import register_error_handlers

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CHANGED: Default config_name to None so we can check the environment variable
def create_app(config_name=None):
    """Application factory"""
    
    # NEW LOGIC: If no argument is passed, check environment variable, else default to 'default'
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    logger.info(f"Creating Flask app with config: {config_name}")
    app = Flask(__name__)
    
    # Load configuration
    try:
        app.config.from_object(config[config_name])
        logger.info(f"Successfully loaded config: {config_name}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise
    
    # Enable CORS
    CORS(app)
    register_error_handlers(app)
    
    # Register blueprints with error handling
    try:
        from routes.image_search import bp as search_bp
        from routes.story_generation import bp as story_bp
        from routes.image_generation import bp as image_gen_bp
        
        app.register_blueprint(search_bp)
        app.register_blueprint(story_bp)
        app.register_blueprint(image_gen_bp)
        logger.info("Successfully registered blueprints")
    except Exception as e:
        logger.error(f"Failed to register blueprints: {e}")
        raise
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    logger.info("Flask app created successfully")
    return app

# WSGI entry point for gunicorn
try:
    app = create_app(os.getenv('FLASK_CONFIG', 'default'))
except Exception as e:
    logger.error(f"FATAL: Failed to create app: {e}", exc_info=True)
    raise

if __name__ == '__main__':
    # Local development
    dev_app = create_app(os.getenv('FLASK_ENV', 'development'))
    dev_app.run(host='0.0.0.0', port=5000, debug=True)