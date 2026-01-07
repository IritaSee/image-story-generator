import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from flask import current_app
from utils.error_handlers import APIError


class GoogleSearchService:
    """Google Custom Search API integration"""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def search_images(self, query, api_key, cse_id, num_results=10):
        """
        Search for images using Google Custom Search API
        
        Args:
            query: Search query string
            api_key: Google API key
            cse_id: Custom Search Engine ID
            num_results: Number of results (max 10 per request)
        
        Returns:
            List of image URLs
        """
        try:
            params = {
                'key': api_key,
                'cx': cse_id,
                'q': query,
                'searchType': 'image',
                'num': min(num_results, 10),
                'safe': 'active'
            }
            
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=current_app.config['REQUEST_TIMEOUT']
            )
            
            if response.status_code == 401:
                raise APIError("Invalid Google API key", 401, "Google")
            elif response.status_code == 429:
                raise APIError("Google API quota exceeded", 429, "Google")
            elif response.status_code != 200:
                raise APIError(f"Google API error: {response.text}", response.status_code, "Google")
            
            data = response.json()
            
            if 'items' not in data:
                return []
            
            images = []
            for item in data['items']:
                images.append({
                    'url': item['link'],
                    'thumbnail': item.get('image', {}).get('thumbnailLink', item['link']),
                    'title': item.get('title', ''),
                    'width': item.get('image', {}).get('width'),
                    'height': item.get('image', {}).get('height')
                })
            
            return images
            
        except requests.exceptions.Timeout:
            raise APIError("Google API request timeout", 408, "Google")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Google API request failed: {str(e)}", 500, "Google")


class BingSearchService:
    """Bing Image Search API integration"""
    
    BASE_URL = "https://api.bing.microsoft.com/v7.0/images/search"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def search_images(self, query, api_key, num_results=10):
        """
        Search for images using Bing Image Search API
        
        Args:
            query: Search query string
            api_key: Bing API key
            num_results: Number of results
        
        Returns:
            List of image URLs
        """
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': api_key
            }
            
            params = {
                'q': query,
                'count': num_results,
                'safeSearch': 'Moderate'
            }
            
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=current_app.config['REQUEST_TIMEOUT']
            )
            
            if response.status_code == 401:
                raise APIError("Invalid Bing API key", 401, "Bing")
            elif response.status_code == 429:
                raise APIError("Bing API quota exceeded", 429, "Bing")
            elif response.status_code != 200:
                raise APIError(f"Bing API error: {response.text}", response.status_code, "Bing")
            
            data = response.json()
            
            if 'value' not in data:
                return []
            
            images = []
            for item in data['value']:
                images.append({
                    'url': item['contentUrl'],
                    'thumbnail': item['thumbnailUrl'],
                    'title': item.get('name', ''),
                    'width': item.get('width'),
                    'height': item.get('height')
                })
            
            return images
            
        except requests.exceptions.Timeout:
            raise APIError("Bing API request timeout", 408, "Bing")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Bing API request failed: {str(e)}", 500, "Bing")
