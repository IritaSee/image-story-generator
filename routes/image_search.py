from flask import Blueprint, request, jsonify
from services.google_search import GoogleSearchService, BingSearchService
from utils.validators import validate_api_key
from utils.error_handlers import APIError

bp = Blueprint('image_search', __name__, url_prefix='/api')

google_search = GoogleSearchService()
bing_search = BingSearchService()


@bp.route('/search', methods=['POST'])
def search_images():
    """
    Search for images using Google Custom Search or Bing
    
    Request JSON:
    {
        "query": "search query",
        "provider": "google" or "bing",
        "api_key": "your-api-key",
        "cse_id": "custom-search-engine-id" (for Google only),
        "num_results": 10 (optional)
    }
    
    Response:
    {
        "images": [
            {
                "url": "image-url",
                "thumbnail": "thumbnail-url",
                "title": "image-title",
                "width": 800,
                "height": 600
            }
        ],
        "count": 10
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        query = data.get('query', '').strip()
        provider = data.get('provider', 'google').lower()
        api_key = data.get('api_key', '').strip()
        num_results = min(int(data.get('num_results', 10)), 10)
        
        # Validate inputs
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        if provider not in ['google', 'bing']:
            return jsonify({'error': 'Invalid provider. Use "google" or "bing"'}), 400
        
        is_valid, error_msg = validate_api_key(api_key, provider)
        if not is_valid:
            return jsonify({'error': error_msg}), 401
        
        # Perform search based on provider
        if provider == 'google':
            cse_id = data.get('cse_id', '').strip()
            if not cse_id:
                return jsonify({'error': 'Google Custom Search Engine ID (cse_id) is required'}), 400
            
            images = google_search.search_images(query, api_key, cse_id, num_results)
        
        else:  # bing
            images = bing_search.search_images(query, api_key, num_results)
        
        return jsonify({
            'images': images,
            'count': len(images),
            'provider': provider
        }), 200
    
    except APIError as e:
        return jsonify({
            'error': e.message,
            'provider': e.provider
        }), e.status_code
    
    except Exception as e:
        return jsonify({
            'error': f'Search failed: {str(e)}'
        }), 500
