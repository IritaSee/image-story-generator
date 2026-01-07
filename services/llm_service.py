import base64
import io
import requests
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential
from flask import current_app
from utils.error_handlers import APIError


class ImageProcessor:
    """Utility for processing images before sending to APIs"""
    
    @staticmethod
    def resize_image(image, max_size=(2048, 2048)):
        """Resize image if it exceeds max dimensions"""
        if image.width > max_size[0] or image.height > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image
    
    @staticmethod
    def image_to_base64(image, format='JPEG'):
        """Convert PIL Image to base64 string"""
        buffered = io.BytesIO()
        
        # Convert RGBA to RGB if saving as JPEG
        if format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image
        
        image.save(buffered, format=format, quality=85)
        img_bytes = buffered.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')
    
    @staticmethod
    def load_image_from_url(url, timeout=10):
        """Download and load image from URL"""
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            raise APIError(f"Failed to load image from URL: {str(e)}", 400)
    
    @staticmethod
    def load_image_from_file(file_storage):
        """Load image from Flask file storage"""
        try:
            return Image.open(file_storage.stream)
        except Exception as e:
            raise APIError(f"Failed to load image from file: {str(e)}", 400)


class BaseLLMService:
    """Base class for LLM services"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
    
    def prepare_few_shot_examples(self, examples, api_format):
        """
        Convert few-shot examples to API-specific format
        Must be implemented by subclasses
        """
        raise NotImplementedError


class OpenAIService(BaseLLMService):
    """OpenAI GPT-4 Vision API integration"""
    
    BASE_URL = "https://api.openai.com/v1/chat/completions"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_story(self, images, api_key, model="gpt-4o", temperature=1.0, 
                      max_tokens=1000, top_p=1.0, few_shot_examples=None):
        """
        Generate story from images using OpenAI Vision API
        
        Args:
            images: List of PIL Image objects
            api_key: OpenAI API key
            model: Model name (gpt-4o, gpt-4o-mini, etc.)
            temperature: 0.0-2.0
            max_tokens: Maximum output tokens
            top_p: Nucleus sampling parameter
            few_shot_examples: List of example dicts with 'image' and 'story' keys
        
        Returns:
            Generated story text
        """
        try:
            # Prepare messages
            messages = []
            
            # Add few-shot examples
            if few_shot_examples:
                for example in few_shot_examples[:5]:  # Limit to 5 examples
                    user_content = [
                        {"type": "text", "text": "Generate a creative story based on this image."}
                    ]
                    
                    # Add example image
                    if 'image_base64' in example:
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{example['image_base64']}"
                            }
                        })
                    
                    messages.append({"role": "user", "content": user_content})
                    messages.append({"role": "assistant", "content": example['story']})
            
            # Add current request
            user_content = [
                {"type": "text", "text": "Generate a creative story based on these images."}
            ]
            
            for img in images:
                resized = self.image_processor.resize_image(img)
                b64_img = self.image_processor.image_to_base64(resized, 'JPEG')
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64_img}"
                    }
                })
            
            messages.append({"role": "user", "content": user_content})
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p
            }
            
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=current_app.config['REQUEST_TIMEOUT'] * 2  # Vision takes longer
            )
            
            if response.status_code == 401:
                raise APIError("Invalid OpenAI API key", 401, "OpenAI")
            elif response.status_code == 429:
                raise APIError("OpenAI API rate limit exceeded", 429, "OpenAI")
            elif response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', response.text)
                raise APIError(f"OpenAI API error: {error_msg}", response.status_code, "OpenAI")
            
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except requests.exceptions.Timeout:
            raise APIError("OpenAI API request timeout", 408, "OpenAI")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"OpenAI request failed: {str(e)}", 500, "OpenAI")


class AnthropicService(BaseLLMService):
    """Anthropic Claude Vision API integration"""
    
    BASE_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_story(self, images, api_key, model="claude-3-5-sonnet-20241022", 
                      temperature=1.0, max_tokens=1000, top_p=1.0, top_k=None,
                      few_shot_examples=None):
        """
        Generate story from images using Claude Vision API
        
        Args:
            images: List of PIL Image objects
            api_key: Anthropic API key
            model: Model name (claude-3-opus, claude-3-sonnet, claude-3-haiku)
            temperature: 0.0-1.0
            max_tokens: Maximum output tokens (required)
            top_p: Nucleus sampling
            top_k: Top-k sampling
            few_shot_examples: List of example dicts
        
        Returns:
            Generated story text
        """
        try:
            # Prepare messages
            messages = []
            
            # Add few-shot examples
            if few_shot_examples:
                for example in few_shot_examples[:5]:
                    user_content = [
                        {"type": "text", "text": "Generate a creative story based on this image."}
                    ]
                    
                    if 'image_base64' in example:
                        user_content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": example['image_base64']
                            }
                        })
                    
                    messages.append({"role": "user", "content": user_content})
                    messages.append({"role": "assistant", "content": example['story']})
            
            # Add current request
            user_content = [
                {"type": "text", "text": "Generate a creative story based on these images."}
            ]
            
            for img in images:
                resized = self.image_processor.resize_image(img)
                b64_img = self.image_processor.image_to_base64(resized, 'JPEG')
                user_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64_img
                    }
                })
            
            messages.append({"role": "user", "content": user_content})
            
            # Make API request
            headers = {
                "x-api-key": api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p
            }
            
            if top_k is not None:
                payload["top_k"] = top_k
            
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=current_app.config['REQUEST_TIMEOUT'] * 2
            )
            
            if response.status_code == 401:
                raise APIError("Invalid Anthropic API key", 401, "Anthropic")
            elif response.status_code == 429:
                raise APIError("Anthropic API rate limit exceeded", 429, "Anthropic")
            elif response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', response.text)
                raise APIError(f"Anthropic API error: {error_msg}", response.status_code, "Anthropic")
            
            data = response.json()
            return data['content'][0]['text']
            
        except requests.exceptions.Timeout:
            raise APIError("Anthropic API request timeout", 408, "Anthropic")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Anthropic request failed: {str(e)}", 500, "Anthropic")


class GoogleGeminiService(BaseLLMService):
    """Google Gemini Vision API integration"""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_story(self, images, api_key, model="gemini-1.5-flash", 
                      temperature=1.0, max_tokens=1000, top_p=1.0, top_k=None,
                      thinking_budget=None, few_shot_examples=None):
        """
        Generate story from images using Google Gemini API
        
        Args:
            images: List of PIL Image objects
            api_key: Google AI API key
            model: Model name (gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-thinking-exp)
            temperature: 0.0-2.0
            max_tokens: Maximum output tokens
            top_p: Nucleus sampling
            top_k: Top-k sampling
            thinking_budget: Thinking budget for Gemini 2.0 Flash Thinking
            few_shot_examples: List of example dicts
        
        Returns:
            Generated story text
        """
        try:
            # Prepare contents
            contents = []
            
            # Add few-shot examples
            if few_shot_examples:
                for example in few_shot_examples[:5]:
                    user_parts = [
                        {"text": "Generate a creative story based on this image."}
                    ]
                    
                    if 'image_base64' in example:
                        user_parts.append({
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": example['image_base64']
                            }
                        })
                    
                    contents.append({"role": "user", "parts": user_parts})
                    contents.append({"role": "model", "parts": [{"text": example['story']}]})
            
            # Add current request
            user_parts = [
                {"text": "Generate a creative story based on these images."}
            ]
            
            for img in images:
                resized = self.image_processor.resize_image(img)
                b64_img = self.image_processor.image_to_base64(resized, 'JPEG')
                user_parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64_img
                    }
                })
            
            contents.append({"role": "user", "parts": user_parts})
            
            # Prepare generation config
            generation_config = {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": top_p
            }
            
            if top_k is not None:
                generation_config["topK"] = top_k
            
            # Add thinking config for Gemini 2.0 Flash Thinking
            if thinking_budget is not None and "thinking" in model.lower():
                generation_config["thinkingConfig"] = {
                    "thinkingBudget": thinking_budget
                }
            
            payload = {
                "contents": contents,
                "generationConfig": generation_config
            }
            
            # Make API request
            url = f"{self.BASE_URL}/{model}:generateContent?key={api_key}"
            
            response = requests.post(
                url,
                json=payload,
                timeout=current_app.config['REQUEST_TIMEOUT'] * 2
            )
            
            if response.status_code == 400:
                error_data = response.json()
                if 'API_KEY_INVALID' in str(error_data):
                    raise APIError("Invalid Google AI API key", 401, "Google Gemini")
                raise APIError(f"Google Gemini API error: {response.text}", 400, "Google Gemini")
            elif response.status_code == 429:
                raise APIError("Google Gemini API rate limit exceeded", 429, "Google Gemini")
            elif response.status_code != 200:
                raise APIError(f"Google Gemini API error: {response.text}", response.status_code, "Google Gemini")
            
            data = response.json()
            
            if 'candidates' not in data or len(data['candidates']) == 0:
                raise APIError("No response from Gemini", 500, "Google Gemini")
            
            return data['candidates'][0]['content']['parts'][0]['text']
            
        except requests.exceptions.Timeout:
            raise APIError("Google Gemini API request timeout", 408, "Google Gemini")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Google Gemini request failed: {str(e)}", 500, "Google Gemini")
