from flask import Flask, render_template
from flask_cors import CORS
import os
from config import config
from utils.error_handlers import register_error_handlers

# CHANGED: Default config_name to None so we can check the environment variable
def create_app(config_name=None):
    """Application factory"""
    
    # NEW LOGIC: If no argument is passed, check environment variable, else default to 'default'
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # ... rest of your code remains exactly the same ...
    CORS(app)
    register_error_handlers(app)
    
    from routes.image_search import bp as search_bp
    from routes.story_generation import bp as story_bp
    from routes.image_generation import bp as image_gen_bp
    
    app.register_blueprint(search_bp)
    app.register_blueprint(story_bp)
    app.register_blueprint(image_gen_bp)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=5000, debug=True)