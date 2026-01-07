import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from flask import current_app
from utils.error_handlers import APIError


class OpenAIImageService:
    """OpenAI DALL-E API integration"""
    
    BASE_URL = "https://api.openai.com/v1/images/generations"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_image(self, prompt, api_key, model="dall-e-3", size="1024x1024",
                      quality="standard", style="vivid", n=1):
        """
        Generate image using DALL-E
        
        Args:
            prompt: Text description
            api_key: OpenAI API key
            model: dall-e-3 or dall-e-2
            size: Image size (1024x1024, 1792x1024, 1024x1792 for DALL-E 3)
            quality: standard or hd (DALL-E 3 only)
            style: vivid or natural (DALL-E 3 only)
            n: Number of images (1 for DALL-E 3, 1-10 for DALL-E 2)
        
        Returns:
            List of image URLs
        """
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "prompt": prompt,
                "n": n if model == "dall-e-2" else 1,
                "size": size
            }
            
            # DALL-E 3 specific parameters
            if model == "dall-e-3":
                payload["quality"] = quality
                payload["style"] = style
            
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=current_app.config['REQUEST_TIMEOUT'] * 3  # Image gen takes longer
            )
            
            if response.status_code == 401:
                raise APIError("Invalid OpenAI API key", 401, "OpenAI DALL-E")
            elif response.status_code == 429:
                raise APIError("OpenAI API rate limit exceeded", 429, "OpenAI DALL-E")
            elif response.status_code == 400:
                error_msg = response.json().get('error', {}).get('message', response.text)
                raise APIError(f"DALL-E error: {error_msg}", 400, "OpenAI DALL-E")
            elif response.status_code != 200:
                raise APIError(f"DALL-E API error: {response.text}", response.status_code, "OpenAI DALL-E")
            
            data = response.json()
            return [img['url'] for img in data['data']]
            
        except requests.exceptions.Timeout:
            raise APIError("DALL-E API request timeout", 408, "OpenAI DALL-E")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"DALL-E request failed: {str(e)}", 500, "OpenAI DALL-E")


class StabilityAIService:
    """Stability AI (Stable Diffusion) API integration"""
    
    BASE_URL = "https://api.stability.ai/v1/generation"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_image(self, prompt, api_key, engine="stable-diffusion-xl-1024-v1-0",
                      width=1024, height=1024, cfg_scale=7, steps=30, samples=1, seed=None):
        """
        Generate image using Stability AI
        
        Args:
            prompt: Text description
            api_key: Stability AI API key
            engine: Engine ID
            width: Image width (multiple of 64)
            height: Image height (multiple of 64)
            cfg_scale: Prompt strength (0-35)
            steps: Generation steps (10-50)
            samples: Number of images
            seed: Random seed for reproducibility
        
        Returns:
            List of base64 encoded images
        """
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1
                    }
                ],
                "cfg_scale": cfg_scale,
                "width": width,
                "height": height,
                "steps": steps,
                "samples": samples
            }
            
            if seed is not None:
                payload["seed"] = seed
            
            url = f"{self.BASE_URL}/{engine}/text-to-image"
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=current_app.config['REQUEST_TIMEOUT'] * 3
            )
            
            if response.status_code == 401:
                raise APIError("Invalid Stability AI API key", 401, "Stability AI")
            elif response.status_code == 429:
                raise APIError("Stability AI rate limit exceeded", 429, "Stability AI")
            elif response.status_code != 200:
                raise APIError(f"Stability AI error: {response.text}", response.status_code, "Stability AI")
            
            data = response.json()
            return [img['base64'] for img in data['artifacts']]
            
        except requests.exceptions.Timeout:
            raise APIError("Stability AI request timeout", 408, "Stability AI")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Stability AI request failed: {str(e)}", 500, "Stability AI")


class ReplicateService:
    """Replicate API integration for various image generation models"""
    
    BASE_URL = "https://api.replicate.com/v1/predictions"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_image(self, prompt, api_key, model="stability-ai/sdxl:latest",
                      width=1024, height=1024, **kwargs):
        """
        Generate image using Replicate
        
        Args:
            prompt: Text description
            api_key: Replicate API key
            model: Model identifier
            width: Image width
            height: Image height
            **kwargs: Additional model-specific parameters
        
        Returns:
            Image URL (after polling for completion)
        """
        try:
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            }
            
            input_params = {
                "prompt": prompt,
                "width": width,
                "height": height,
                **kwargs
            }
            
            payload = {
                "version": model,
                "input": input_params
            }
            
            # Create prediction
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=current_app.config['REQUEST_TIMEOUT']
            )
            
            if response.status_code == 401:
                raise APIError("Invalid Replicate API key", 401, "Replicate")
            elif response.status_code == 429:
                raise APIError("Replicate rate limit exceeded", 429, "Replicate")
            elif response.status_code not in (200, 201):
                raise APIError(f"Replicate error: {response.text}", response.status_code, "Replicate")
            
            prediction = response.json()
            prediction_id = prediction['id']
            
            # Poll for completion (simplified - in production, use webhooks)
            import time
            max_attempts = 30
            for _ in range(max_attempts):
                time.sleep(2)
                
                status_response = requests.get(
                    f"{self.BASE_URL}/{prediction_id}",
                    headers=headers,
                    timeout=current_app.config['REQUEST_TIMEOUT']
                )
                
                if status_response.status_code != 200:
                    raise APIError("Failed to check prediction status", status_response.status_code, "Replicate")
                
                status_data = status_response.json()
                
                if status_data['status'] == 'succeeded':
                    return status_data['output']
                elif status_data['status'] == 'failed':
                    raise APIError("Image generation failed", 500, "Replicate")
            
            raise APIError("Image generation timeout", 408, "Replicate")
            
        except requests.exceptions.Timeout:
            raise APIError("Replicate request timeout", 408, "Replicate")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Replicate request failed: {str(e)}", 500, "Replicate")
