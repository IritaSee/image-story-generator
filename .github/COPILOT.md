# Copilot Guide

This repository is a monolithic Flask app with a static frontend for:
- Image search via Google Custom Search (primary) and Bing (fallback)
- Story generation from images using multi-provider Vision LLMs (OpenAI, Anthropic, Google)
- Text-to-image generation via OpenAI DALL-E, Stability AI, and Replicate

Follow these directives when proposing code or completing tasks.

## Architecture & Conventions
- Use Flask blueprints under `routes/` and service abstractions under `services/`.
- Keep validation utilities in `utils/` and global error handling in `utils/error_handlers.py`.
- Frontend is static HTML/CSS/JS in `templates/` and `static/`.
- Configuration via `config.py` and environment variables; DO NOT persist API keys server-side.
- Respect these limits: max 10 images per request; max 5MB per image; allowed extensions: png, jpg, jpeg, webp.
- Prefer small, focused changes; preserve public APIs and file structure.
- Avoid inline comments unless explicitly requested.

## Endpoints (Contract)

### 1) Image Search
Route: `/api/search` (POST)
- Request JSON: `{ query, provider: "google"|"bing", api_key, cse_id (google only), num_results? }`
- Return: `{ images: [{ url, thumbnail, title, width, height }], count, provider }`
- Use `services/google_search.py` for Google and Bing adapters.
- Handle errors with consistent JSON and status codes; retry transient failures.

### 2) Story Generation from Images
Route: `/api/generate-story` (POST, multipart/form-data)
- Form fields:
  - `files`: image uploads (0–10)
  - `image_urls`: JSON array of URLs
  - `provider`: `openai` | `anthropic` | `google`
  - `model`: provider-specific model name
  - `api_key`: BYOK passed in request
  - `temperature`, `max_tokens`, `top_p`
  - `top_k` (Anthropic/Google), `thinking_budget` (Gemini 2.0 Thinking)
  - `few_shot_examples`: JSON array of `{ image_base64, story }`, up to 5
- Return: `{ story, provider, model }`
- Validate image count and size with `utils/validators.py`.
- Use `services/llm_service.py` providers (OpenAI GPT‑4o, Anthropic Claude 3.x, Google Gemini 1.5/2.0).
- Convert images to base64 (JPEG), resize if needed, and construct provider-specific message formats.

### 3) Text-to-Image Generation (Fallback)
Route: `/api/generate-image` (POST)
- Request JSON includes: `{ prompt, provider: openai|stability|replicate, api_key, model, ...params }`
- Provider-specific params:
  - OpenAI DALL‑E: `size`, `quality`, `style`
  - Stability AI: `width`, `height`, `cfg_scale`, `steps`, `samples`, `seed`
  - Replicate: `replicate_params` map
- Return: `{ images: [url|base64], provider, model }`
- Implement polling for Replicate; prefer webhooks for production.

## Frontend UX Requirements
- Image search tab: grid results with checkboxes; enforce 10-image selection cap.
- Upload tab: drag‑and‑drop, preview thumbnails, client‑side validation for ≤5MB and count ≤10.
- Story panel: provider/model dropdowns; sliders for `temperature`, `max_tokens`, `top_p`; conditional `top_k` and `thinking_budget`.
- Preset buttons: Precise (0.3), Balanced (1.0), Creative (1.5).
- Few‑shot panel: manage example image+story pairs in `localStorage`; export/import JSON.
- Settings modal: BYOK inputs saved in `localStorage` (OpenAI, Anthropic, Google AI; Google CSE and Bing for search; Stability and Replicate for image gen). Never persist keys server‑side.
- Loading overlay, toast notifications, and responsive layout.

## Validation & Security
- Enforce 10 images max and 5MB max per image in both frontend and backend.
- Verify image content with Pillow to prevent fake extensions.
- BYOK: accept keys in request (form/body). Do not log or store keys.
- Use `tenacity` for retries; set reasonable timeouts.
- Return friendly error messages with appropriate HTTP status codes.
- Do not implement scraping; use official APIs only.

## Model Providers & Parameters
- OpenAI: GPT‑4o/GPT‑4o‑mini; `temperature`, `top_p`, `max_tokens`.
- Anthropic: Claude 3.x; `temperature`, `top_p`, `top_k`, `max_tokens`.
- Google: Gemini 1.5/2.0; `temperature`, `topP`, `topK`, `maxOutputTokens`, optional `thinkingBudget` for 2.0 Thinking models.
- For text‑to‑image: DALL‑E 3/2, Stability SDXL, Replicate models.

## Error Handling (Patterns)
- Map provider errors to JSON with `error` and `provider` fields.
- Handle 401 (invalid key), 429 (rate limit/quota), 400 (bad request), 408 (timeout), 500 (unexpected).
- Use exponential backoff for transient network errors.

## Docker & Run
- Containerize with `Dockerfile` and `docker-compose.yml`.
- Expose port 5000; serve via Gunicorn in production.
- Persist uploads via `uploads` named volume.

## Coding Style & Non‑Goals
- Python: snake_case, minimal side effects in routes, isolate external calls in services.
- Keep changes minimal and aligned with current structure; don’t rename files unless necessary.
- Avoid adding heavy frameworks; stick to Flask + static frontend.
- Don’t store secrets server‑side; don’t add scraping.

## Suggested Copilot Behaviors
- When asked to add endpoints, follow the contracts above and place code in the correct module.
- For new providers/models, add adapter methods in `services/llm_service.py` or `services/image_gen_service.py` and extend frontend model dropdowns.
- For UX tweaks, modify `templates/index.html` and `static/js/app.js` with progressive enhancement; ensure validation remains in sync.
- Propose retries and clear error messages for any new external API calls.
- Respect image limits and parameter ranges; fail fast with user‑friendly errors.

## Content Policy
- Follow Microsoft content policies. If prompted for harmful, hateful, racist, sexist, lewd, or violent content, respond with: "Sorry, I can't assist with that."