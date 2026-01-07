from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import base64
from services.llm_service import OpenAIService, AnthropicService, GoogleGeminiService, ImageProcessor
from utils.validators import validate_image, validate_image_count, validate_api_key
from utils.error_handlers import APIError

bp = Blueprint('story_generation', __name__, url_prefix='/api')

openai_service = OpenAIService()
anthropic_service = AnthropicService()
gemini_service = GoogleGeminiService()
image_processor = ImageProcessor()


@bp.route('/generate-story', methods=['POST'])
def generate_story():
    """
    Generate story from images using various LLM providers
    
    Request (multipart/form-data):
    - files: uploaded image files (up to 10, max 5MB each)
    - image_urls: JSON array of image URLs
    - provider: "openai", "anthropic", or "google"
    - model: specific model name
    - api_key: API key for the provider
    - temperature: float (0.0-2.0)
    - max_tokens: int
    - top_p: float (0.0-1.0)
    - top_k: int (optional, for Anthropic/Google)
    - thinking_budget: int (optional, for Gemini 2.0 Thinking)
    - few_shot_examples: JSON array of example objects
    
    Response:
    {
        "story": "generated story text",
        "provider": "openai",
        "model": "gpt-4o"
    }
    """
    try:
        # Get form data
        provider = request.form.get('provider', 'openai').lower()
        model = request.form.get('model', '')
        api_key = request.form.get('api_key', '').strip()
        
        # Validate API key
        is_valid, error_msg = validate_api_key(api_key, provider)
        if not is_valid:
            return jsonify({'error': error_msg}), 401
        
        # Get parameters
        try:
            temperature = float(request.form.get('temperature', 1.0))
            max_tokens = int(request.form.get('max_tokens', 1000))
            top_p = float(request.form.get('top_p', 1.0))
            top_k = request.form.get('top_k')
            if top_k:
                top_k = int(top_k)
            thinking_budget = request.form.get('thinking_budget')
            if thinking_budget:
                thinking_budget = int(thinking_budget)
        except ValueError as e:
            return jsonify({'error': f'Invalid parameter value: {str(e)}'}), 400
        
        # Collect images
        images = []
        
        # Process uploaded files
        uploaded_files = request.files.getlist('files')
        for file in uploaded_files:
            if file.filename:
                is_valid, error_msg = validate_image(file)
                if not is_valid:
                    return jsonify({'error': f'Invalid image: {error_msg}'}), 400
                
                img = image_processor.load_image_from_file(file)
                images.append(img)
        
        # Process image URLs
        import json
        image_urls = request.form.get('image_urls', '[]')
        try:
            urls = json.loads(image_urls)
            for url in urls:
                img = image_processor.load_image_from_url(url)
                images.append(img)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid image_urls JSON'}), 400
        
        # Validate image count
        is_valid, error_msg = validate_image_count(len(images))
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Process few-shot examples
        few_shot_examples = None
        examples_json = request.form.get('few_shot_examples', '[]')
        try:
            examples = json.loads(examples_json)
            if examples:
                few_shot_examples = []
                for ex in examples[:5]:  # Limit to 5 examples
                    if 'image_base64' in ex and 'story' in ex:
                        few_shot_examples.append(ex)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid few_shot_examples JSON'}), 400
        
        # Set default models if not provided
        if not model:
            if provider == 'openai':
                model = 'gpt-4o'
            elif provider == 'anthropic':
                model = 'claude-3-5-sonnet-20241022'
            elif provider == 'google':
                model = 'gemini-1.5-flash'
        
        # Generate story based on provider
        if provider == 'openai':
            story = openai_service.generate_story(
                images=images,
                api_key=api_key,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                few_shot_examples=few_shot_examples
            )
        
        elif provider == 'anthropic':
            story = anthropic_service.generate_story(
                images=images,
                api_key=api_key,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                few_shot_examples=few_shot_examples
            )
        
        elif provider == 'google':
            story = gemini_service.generate_story(
                images=images,
                api_key=api_key,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                thinking_budget=thinking_budget,
                few_shot_examples=few_shot_examples
            )
        
        else:
            return jsonify({'error': f'Invalid provider: {provider}'}), 400
        
        return jsonify({
            'story': story,
            'provider': provider,
            'model': model
        }), 200
    
    except APIError as e:
        return jsonify({
            'error': e.message,
            'provider': e.provider
        }), e.status_code
    
    except Exception as e:
        return jsonify({
            'error': f'Story generation failed: {str(e)}'
        }), 500
