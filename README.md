# Image Story Generator

A monolithic Flask web application that searches for images, generates creative stories from images using AI, and creates images from text descriptions. Features a modern, responsive UI with API key management and few-shot learning capabilities.

## Features

### 🔍 Image Search
- **Google Custom Search API** integration
- **Bing Image Search API** as fallback
- Interactive image grid with multi-select (up to 10 images)
- Image preview and selection

### 💬 AI Story Generation
- **Multi-provider support:**
  - OpenAI (GPT-4o, GPT-4o Mini)
  - Anthropic (Claude 3.5 Sonnet, Claude 3 Opus/Sonnet/Haiku)
  - Google (Gemini 2.0 Flash Thinking, Gemini 1.5 Pro/Flash)
- **Tunable parameters:**
  - Temperature (0.0-2.0)
  - Max tokens (100-4096)
  - Top-p nucleus sampling
  - Top-k sampling (Anthropic/Google)
  - Thinking budget (Gemini 2.0 Thinking)
- **Few-shot learning:** Upload example image-story pairs to guide AI output
- Support for both uploaded images and searched images
- Preset configurations (Precise, Balanced, Creative)

### 🎨 Image Generation
- **OpenAI DALL-E 3/2** with quality and style controls
- **Stability AI** (Stable Diffusion XL) with advanced parameters
- **Replicate** integration for various models
- Configurable size, CFG scale, steps, and more

### 🔐 Security Features
- **BYOK (Bring Your Own Key)** approach
- Client-side API key storage (localStorage)
- No server-side key persistence
- API keys sent per-request only

### 🎯 UX Features
- Responsive design (mobile-friendly)
- Drag-and-drop file upload
- Real-time parameter preview
- Toast notifications
- Loading states with progress indicators
- Export/import few-shot examples
- Copy and save generated stories

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone/Download the project:**
```bash
cd /tmp/image-story-generator
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env if needed (optional - users provide keys via UI)
```

5. **Run the application:**
```bash
python app.py
```

6. **Open browser:**
```
http://localhost:5000
```

## Configuration

### API Keys (Required)

Configure these in the UI settings (⚙️ icon):

#### Image Search
- **Google Custom Search:**
  - API Key: Get from [Google Cloud Console](https://console.cloud.google.com/)
  - CSE ID: Create at [Programmable Search Engine](https://programmablesearchengine.google.com/)
- **Bing Search API:**
  - Get from [Azure Portal](https://portal.azure.com/)

#### AI Story Generation
- **OpenAI:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic:** [console.anthropic.com](https://console.anthropic.com/)
- **Google AI:** [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

#### Image Generation
- **Stability AI:** [platform.stability.ai/account/keys](https://platform.stability.ai/account/keys)
- **Replicate:** [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens)

## Usage

### 1. Configure API Keys
1. Click the ⚙️ settings icon in the header
2. Enter your API keys for desired services
3. Click "Save Settings"
4. Keys are stored in your browser's localStorage

### 2. Search for Images
1. Go to "🔍 Search Images" tab
2. Select provider (Google or Bing)
3. Enter search query
4. Click "Search"
5. Select images (up to 10)

### 3. Upload Images
1. Go to "📤 Upload Images" tab
2. Drag & drop images or click to browse
3. Max 10 images, 5MB each

### 4. Configure Few-Shot Examples (Optional)
1. Click the examples panel on the right
2. Click "+ Add Example"
3. Upload an image and write the desired story style
4. Save up to 5 examples
5. Export/import for backup

### 5. Generate Story
1. Ensure you have selected or uploaded images
2. Choose AI provider and model
3. Adjust parameters (or use presets)
4. Click "Generate Story"
5. Copy, save, or regenerate as needed

### 6. Generate Images from Text
1. Go to "🎨 Generate Image" tab
2. Enter description/prompt
3. Select provider and configure parameters
4. Click "Generate Image"

## API Endpoints

### POST /api/search
Search for images using Google or Bing.

**Request:**
```json
{
  "query": "sunset beach",
  "provider": "google",
  "api_key": "your-api-key",
  "cse_id": "your-cse-id",
  "num_results": 10
}
```

**Response:**
```json
{
  "images": [
    {
      "url": "https://...",
      "thumbnail": "https://...",
      "title": "Beautiful sunset",
      "width": 1920,
      "height": 1080
    }
  ],
  "count": 10,
  "provider": "google"
}
```

### POST /api/generate-story
Generate story from images using AI.

**Request:** multipart/form-data
- `files`: Image files (up to 10)
- `image_urls`: JSON array of image URLs
- `provider`: "openai", "anthropic", or "google"
- `model`: Model name
- `api_key`: API key
- `temperature`: 0.0-2.0
- `max_tokens`: integer
- `top_p`: 0.0-1.0
- `top_k`: integer (optional)
- `thinking_budget`: integer (optional)
- `few_shot_examples`: JSON array

**Response:**
```json
{
  "story": "Generated story text...",
  "provider": "openai",
  "model": "gpt-4o"
}
```

### POST /api/generate-image
Generate image from text prompt.

**Request:**
```json
{
  "prompt": "A futuristic city at sunset",
  "provider": "openai",
  "api_key": "your-api-key",
  "model": "dall-e-3",
  "size": "1024x1024",
  "quality": "standard",
  "style": "vivid"
}
```

**Response:**
```json
{
  "images": ["https://..."],
  "provider": "openai",
  "model": "dall-e-3"
}
```

## Project Structure

```
image-story-generator/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration classes
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── routes/
│   ├── image_search.py        # Image search endpoint
│   ├── story_generation.py    # Story generation endpoint
│   └── image_generation.py    # Image generation endpoint
├── services/
│   ├── google_search.py       # Google/Bing search integration
│   ├── llm_service.py         # OpenAI/Anthropic/Gemini services
│   └── image_gen_service.py   # DALL-E/Stability/Replicate services
├── utils/
│   ├── validators.py          # Input validation
│   └── error_handlers.py      # Error handling
├── templates/
│   └── index.html             # Main HTML template
└── static/
    ├── css/
    │   └── styles.css         # Application styles
    ├── js/
    │   └── app.js             # Frontend JavaScript
    └── uploads/               # Temporary upload folder
```

## Development

### Run in development mode:
```bash
export FLASK_ENV=development
python app.py
```

### Production deployment:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Limitations

- **File size:** 5MB per image
- **Max images:** 10 per request
- **Few-shot examples:** 5 maximum
- **API rate limits:** Depends on your API tier
- **Cost:** API calls are charged by providers

## Troubleshooting

### "Invalid API key" error
- Verify key is correct in settings
- Check key hasn't expired
- Ensure billing is enabled for the API

### "File too large" error
- Compress images before upload
- Max 5MB per image

### "Maximum images exceeded"
- Limit to 10 images total
- Clear selection before adding more

### CORS errors
- Ensure running on localhost or proper domain
- Check browser console for details

## Security Notes

⚠️ **Important:**
- API keys are stored in browser localStorage
- Use HTTPS in production
- Don't expose API keys in screenshots/logs
- Implement rate limiting for production
- Consider backend key storage for production use

## License

MIT License - feel free to use and modify.

## Support

For issues or questions:
1. Check API provider documentation
2. Verify API keys are valid
3. Check browser console for errors
4. Review API quotas and billing

## Acknowledgments

- OpenAI for GPT-4 Vision and DALL-E
- Anthropic for Claude 3
- Google for Gemini
- Stability AI for Stable Diffusion
- Built with Flask, vanilla JavaScript, and modern CSS
