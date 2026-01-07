from flask import Flask, render_template
from flask_cors import CORS
import os
from config import config
from utils.error_handlers import register_error_handlers


def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Enable CORS
    CORS(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    from routes.image_search import bp as search_bp
    from routes.story_generation import bp as story_bp
    from routes.image_generation import bp as image_gen_bp
    
    app.register_blueprint(search_bp)
    app.register_blueprint(story_bp)
    app.register_blueprint(image_gen_bp)
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Main route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=5000, debug=True)
