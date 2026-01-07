from flask import jsonify


def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'error': 'File too large',
            'message': 'Maximum file size is 5MB per image'
        }), 413
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404


class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message, status_code=500, provider=None):
        self.message = message
        self.status_code = status_code
        self.provider = provider
        super().__init__(self.message)
