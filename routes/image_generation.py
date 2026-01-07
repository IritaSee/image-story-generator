from flask import Blueprint, request, jsonify
import base64
from services.image_gen_service import OpenAIImageService, StabilityAIService, ReplicateService
from utils.validators import validate_api_key
from utils.error_handlers import APIError

bp = Blueprint('image_generation', __name__, url_prefix='/api')

openai_image = OpenAIImageService()
stability_ai = StabilityAIService()
replicate = ReplicateService()


@bp.route('/generate-image', methods=['POST'])
def generate_image():
    """
    Generate image from text prompt using various providers
    
    Request JSON:
    {
        "prompt": "text description",
        "provider": "openai", "stability", or "replicate",
        "api_key": "your-api-key",
        "model": "model-name" (optional, provider-specific defaults),
        
        // OpenAI DALL-E parameters
        "size": "1024x1024" (or "1792x1024", "1024x1792"),
        "quality": "standard" or "hd",
        "style": "vivid" or "natural",
        "n": 1,
        
        // Stability AI parameters
        "width": 1024,
        "height": 1024,
        "cfg_scale": 7,
        "steps": 30,
        "samples": 1,
        "seed": null or int,
        
        // Replicate parameters (varies by model)
        "replicate_params": {}
    }
    
    Response:
    {
        "images": ["url" or "base64-data"],
        "provider": "openai",
        "model": "dall-e-3"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        prompt = data.get('prompt', '').strip()
        provider = data.get('provider', 'openai').lower()
        api_key = data.get('api_key', '').strip()
        model = data.get('model', '')
        
        # Validate inputs
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        if len(prompt) > 4000:
            return jsonify({'error': 'Prompt too long (max 4000 characters)'}), 400
        
        is_valid, error_msg = validate_api_key(api_key, provider)
        if not is_valid:
            return jsonify({'error': error_msg}), 401
        
        # Generate image based on provider
        if provider == 'openai':
            model = model or 'dall-e-3'
            size = data.get('size', '1024x1024')
            quality = data.get('quality', 'standard')
            style = data.get('style', 'vivid')
            n = data.get('n', 1)
            
            images = openai_image.generate_image(
                prompt=prompt,
                api_key=api_key,
                model=model,
                size=size,
                quality=quality,
                style=style,
                n=n
            )
        
        elif provider == 'stability':
            model = model or 'stable-diffusion-xl-1024-v1-0'
            width = data.get('width', 1024)
            height = data.get('height', 1024)
            cfg_scale = data.get('cfg_scale', 7)
            steps = data.get('steps', 30)
            samples = data.get('samples', 1)
            seed = data.get('seed')
            
            images = stability_ai.generate_image(
                prompt=prompt,
                api_key=api_key,
                engine=model,
                width=width,
                height=height,
                cfg_scale=cfg_scale,
                steps=steps,
                samples=samples,
                seed=seed
            )
        
        elif provider == 'replicate':
            model = model or 'stability-ai/sdxl:latest'
            width = data.get('width', 1024)
            height = data.get('height', 1024)
            replicate_params = data.get('replicate_params', {})
            
            result = replicate.generate_image(
                prompt=prompt,
                api_key=api_key,
                model=model,
                width=width,
                height=height,
                **replicate_params
            )
            
            # Replicate returns a single URL or list
            images = result if isinstance(result, list) else [result]
        
        else:
            return jsonify({'error': f'Invalid provider: {provider}'}), 400
        
        return jsonify({
            'images': images,
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
            'error': f'Image generation failed: {str(e)}'
        }), 500
