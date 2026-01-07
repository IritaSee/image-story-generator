// App State
const state = {
    selectedImages: new Set(),
    uploadedFiles: [],
    fewShotExamples: [],
    apiKeys: {},
    currentEditingExample: null
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadApiKeys();
    loadFewShotExamples();
    initializeEventListeners();
    updateModelOptions();
});

// API Keys Management
function loadApiKeys() {
    const keys = ['googleApiKey', 'googleCseId', 'bingApiKey', 'openaiApiKey', 
                  'anthropicApiKey', 'googleAiApiKey', 'stabilityApiKey', 'replicateApiKey'];
    
    keys.forEach(key => {
        const value = localStorage.getItem(key);
        if (value) {
            state.apiKeys[key] = value;
            const input = document.getElementById(key);
            if (input) input.value = value;
            updateKeyStatus(key, true);
        }
    });
}

function saveApiKeys() {
    const keys = ['googleApiKey', 'googleCseId', 'bingApiKey', 'openaiApiKey', 
                  'anthropicApiKey', 'googleAiApiKey', 'stabilityApiKey', 'replicateApiKey'];
    
    keys.forEach(key => {
        const input = document.getElementById(key);
        if (input && input.value) {
            localStorage.setItem(key, input.value);
            state.apiKeys[key] = input.value;
            updateKeyStatus(key, true);
        }
    });
    
    showToast('API keys saved successfully', 'success');
    closeModal('settingsModal');
}

function updateKeyStatus(key, hasValue) {
    const statusMap = {
        'googleApiKey': 'googleStatus',
        'bingApiKey': 'bingStatus',
        'openaiApiKey': 'openaiStatus',
        'anthropicApiKey': 'anthropicStatus',
        'googleAiApiKey': 'googleAiStatus',
        'stabilityApiKey': 'stabilityStatus',
        'replicateApiKey': 'replicateStatus'
    };
    
    const statusId = statusMap[key];
    if (statusId) {
        const statusEl = document.getElementById(statusId);
        if (statusEl) {
            statusEl.textContent = hasValue ? '✓' : '';
            statusEl.className = 'status-indicator ' + (hasValue ? 'valid' : '');
        }
    }
}

// Few-Shot Examples Management
function loadFewShotExamples() {
    const saved = localStorage.getItem('fewShotExamples');
    if (saved) {
        state.fewShotExamples = JSON.parse(saved);
        renderExamplesList();
    }
}

function saveFewShotExamples() {
    localStorage.setItem('fewShotExamples', JSON.stringify(state.fewShotExamples));
}

function renderExamplesList() {
    const container = document.getElementById('examplesList');
    container.innerHTML = '';
    
    if (state.fewShotExamples.length === 0) {
        container.innerHTML = '<p class="help-text">No examples yet. Add some to improve story quality!</p>';
        return;
    }
    
    state.fewShotExamples.forEach((example, index) => {
        const div = document.createElement('div');
        div.className = 'example-item';
        div.innerHTML = `
            <img src="data:image/jpeg;base64,${example.image_base64}" alt="Example ${index + 1}">
            <div class="example-content">
                <p class="example-story">${example.story.substring(0, 100)}...</p>
                <button class="btn-icon-delete" onclick="deleteExample(${index})">🗑️</button>
            </div>
        `;
        container.appendChild(div);
    });
}

function deleteExample(index) {
    if (confirm('Delete this example?')) {
        state.fewShotExamples.splice(index, 1);
        saveFewShotExamples();
        renderExamplesList();
        showToast('Example deleted', 'info');
    }
}

function exportExamples() {
    const data = JSON.stringify(state.fewShotExamples, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'few-shot-examples.json';
    a.click();
    URL.revokeObjectURL(url);
    showToast('Examples exported', 'success');
}

function importExamples(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            if (Array.isArray(data)) {
                state.fewShotExamples = data;
                saveFewShotExamples();
                renderExamplesList();
                showToast('Examples imported successfully', 'success');
            }
        } catch (err) {
            showToast('Invalid JSON file', 'error');
        }
    };
    reader.readAsText(file);
}

// Event Listeners
function initializeEventListeners() {
    // Settings modal
    document.getElementById('settingsBtn').onclick = () => openModal('settingsModal');
    document.getElementById('saveSettings').onclick = saveApiKeys;
    
    // Modal close buttons
    document.querySelectorAll('.close').forEach(btn => {
        btn.onclick = function() {
            this.closest('.modal').style.display = 'none';
        };
    });
    
    // Click outside modal to close
    window.onclick = (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    };
    
    // Few-shot panel
    document.getElementById('toggleFewShot').onclick = toggleFewShotPanel;
    document.getElementById('addExample').onclick = () => openModal('exampleModal');
    document.getElementById('saveExample').onclick = saveExample;
    document.getElementById('exportExamples').onclick = exportExamples;
    document.getElementById('importExamples').onclick = () => document.getElementById('importFile').click();
    document.getElementById('importFile').onchange = importExamples;
    
    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.onclick = () => switchTab(tab.dataset.tab);
    });
    
    // Search
    document.getElementById('searchBtn').onclick = searchImages;
    document.getElementById('searchQuery').onkeypress = (e) => {
        if (e.key === 'Enter') searchImages();
    };
    
    // Upload
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    dropZone.onclick = () => fileInput.click();
    fileInput.onchange = handleFileSelect;
    
    dropZone.ondragover = (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    };
    
    dropZone.ondragleave = () => {
        dropZone.classList.remove('drag-over');
    };
    
    dropZone.ondrop = (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        handleFileSelect({ target: { files: e.dataTransfer.files } });
    };
    
    // Image generation
    document.getElementById('imageGenProvider').onchange = updateImageGenParams;
    document.getElementById('generateImageBtn').onclick = generateImage;
    
    // LLM provider/model
    document.getElementById('llmProvider').onchange = updateModelOptions;
    
    // Parameter sliders
    setupSlider('temperature', 'tempValue');
    setupSlider('maxTokens', 'tokensValue');
    setupSlider('topP', 'topPValue');
    setupSlider('topK', 'topKValue');
    setupSlider('thinkingBudget', 'thinkingBudgetValue');
    setupSlider('cfgScale', 'cfgScaleValue');
    setupSlider('steps', 'stepsValue');
    
    // Presets
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.onclick = () => {
            const temp = parseFloat(btn.dataset.temp);
            document.getElementById('temperature').value = temp;
            document.getElementById('tempValue').textContent = temp.toFixed(1);
        };
    });
    
    // Story generation
    document.getElementById('generateStoryBtn').onclick = generateStory;
    document.getElementById('copyStory').onclick = copyStory;
    document.getElementById('saveStory').onclick = saveStory;
    document.getElementById('regenerateStory').onclick = generateStory;
    
    // Example image preview
    document.getElementById('exampleImage').onchange = previewExampleImage;
}

function setupSlider(sliderId, valueId) {
    const slider = document.getElementById(sliderId);
    const valueDisplay = document.getElementById(valueId);
    
    if (slider && valueDisplay) {
        slider.oninput = () => {
            valueDisplay.textContent = slider.value;
        };
    }
}

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function toggleFewShotPanel() {
    const panel = document.getElementById('fewShotPanel');
    const btn = document.getElementById('toggleFewShot');
    panel.classList.toggle('collapsed');
    btn.textContent = panel.classList.contains('collapsed') ? '▶' : '◀';
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(tabName + 'Tab').classList.add('active');
}

// Image Search
async function searchImages() {
    const query = document.getElementById('searchQuery').value.trim();
    const provider = document.getElementById('searchProvider').value;
    
    if (!query) {
        showToast('Please enter a search query', 'error');
        return;
    }
    
    const apiKey = provider === 'google' ? state.apiKeys.googleApiKey : state.apiKeys.bingApiKey;
    if (!apiKey) {
        showToast(`Please configure ${provider} API key in settings`, 'error');
        return;
    }
    
    showLoading('Searching for images...');
    
    try {
        const body = {
            query,
            provider,
            api_key: apiKey,
            num_results: 10
        };
        
        if (provider === 'google') {
            body.cse_id = state.apiKeys.googleCseId;
            if (!body.cse_id) {
                throw new Error('Google CSE ID not configured');
            }
        }
        
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Search failed');
        }
        
        displaySearchResults(data.images);
        showToast(`Found ${data.count} images`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

function displaySearchResults(images) {
    const container = document.getElementById('searchResults');
    container.innerHTML = '';
    
    if (images.length === 0) {
        container.innerHTML = '<p class="help-text">No images found</p>';
        return;
    }
    
    images.forEach((img, index) => {
        const div = document.createElement('div');
        div.className = 'image-item';
        div.innerHTML = `
            <img src="${img.thumbnail}" alt="${img.title}" loading="lazy">
            <input type="checkbox" class="image-checkbox" data-url="${img.url}" data-index="${index}">
        `;
        
        const checkbox = div.querySelector('.image-checkbox');
        checkbox.onchange = () => handleImageSelection(img.url, checkbox.checked);
        
        container.appendChild(div);
    });
}

function handleImageSelection(url, selected) {
    if (selected) {
        if (state.selectedImages.size >= 10) {
            showToast('Maximum 10 images allowed', 'error');
            event.target.checked = false;
            return;
        }
        state.selectedImages.add(url);
    } else {
        state.selectedImages.delete(url);
    }
    
    updateSelectedCount();
}

function updateSelectedCount() {
    document.getElementById('selectedCount').textContent = state.selectedImages.size;
}

// File Upload
function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    
    // Validate count
    if (state.uploadedFiles.length + files.length > 10) {
        showToast('Maximum 10 images allowed', 'error');
        return;
    }
    
    files.forEach(file => {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            showToast(`${file.name} is not an image`, 'error');
            return;
        }
        
        // Validate file size
        if (file.size > 5 * 1024 * 1024) {
            showToast(`${file.name} exceeds 5MB limit`, 'error');
            return;
        }
        
        state.uploadedFiles.push(file);
        displayUploadedImage(file);
    });
    
    updateUploadedCount();
}

function displayUploadedImage(file) {
    const container = document.getElementById('uploadedImages');
    const reader = new FileReader();
    
    reader.onload = (e) => {
        const div = document.createElement('div');
        div.className = 'image-item';
        div.innerHTML = `
            <img src="${e.target.result}" alt="${file.name}">
            <button class="remove-btn" onclick="removeUploadedImage(${state.uploadedFiles.length - 1})">×</button>
        `;
        container.appendChild(div);
    };
    
    reader.readAsDataURL(file);
}

function removeUploadedImage(index) {
    state.uploadedFiles.splice(index, 1);
    
    // Re-render all uploaded images
    const container = document.getElementById('uploadedImages');
    container.innerHTML = '';
    state.uploadedFiles.forEach(file => displayUploadedImage(file));
    
    updateUploadedCount();
}

function updateUploadedCount() {
    document.getElementById('uploadedCount').textContent = state.uploadedFiles.length;
}

// Model Options
function updateModelOptions() {
    const provider = document.getElementById('llmProvider').value;
    const modelSelect = document.getElementById('llmModel');
    
    const models = {
        openai: [
            { value: 'gpt-4o', text: 'GPT-4o' },
            { value: 'gpt-4o-mini', text: 'GPT-4o Mini' }
        ],
        anthropic: [
            { value: 'claude-3-5-sonnet-20241022', text: 'Claude 3.5 Sonnet' },
            { value: 'claude-3-opus-20240229', text: 'Claude 3 Opus' },
            { value: 'claude-3-sonnet-20240229', text: 'Claude 3 Sonnet' },
            { value: 'claude-3-haiku-20240307', text: 'Claude 3 Haiku' }
        ],
        google: [
            { value: 'gemini-2.0-flash-thinking-exp', text: 'Gemini 2.0 Flash Thinking' },
            { value: 'gemini-1.5-pro', text: 'Gemini 1.5 Pro' },
            { value: 'gemini-1.5-flash', text: 'Gemini 1.5 Flash' }
        ]
    };
    
    modelSelect.innerHTML = '';
    models[provider].forEach(model => {
        const option = document.createElement('option');
        option.value = model.value;
        option.textContent = model.text;
        modelSelect.appendChild(option);
    });
    
    // Show/hide provider-specific parameters
    const topKLabel = document.getElementById('topKLabel');
    const thinkingLabel = document.getElementById('thinkingBudgetLabel');
    
    topKLabel.style.display = (provider === 'anthropic' || provider === 'google') ? 'block' : 'none';
    
    modelSelect.onchange = () => {
        const model = modelSelect.value;
        thinkingLabel.style.display = model.includes('thinking') ? 'block' : 'none';
    };
    
    // Trigger initial check
    modelSelect.onchange();
}

function updateImageGenParams() {
    const provider = document.getElementById('imageGenProvider').value;
    const modelSelect = document.getElementById('imageGenModel');
    const modelLabel = document.getElementById('imageGenModelLabel');
    
    // Update model options
    const models = {
        openai: [
            { value: 'dall-e-3', text: 'DALL-E 3' },
            { value: 'dall-e-2', text: 'DALL-E 2' }
        ],
        stability: [
            { value: 'stable-diffusion-xl-1024-v1-0', text: 'SDXL 1.0' }
        ],
        replicate: [
            { value: 'stability-ai/sdxl:latest', text: 'SDXL (Replicate)' }
        ]
    };
    
    modelSelect.innerHTML = '';
    models[provider].forEach(model => {
        const option = document.createElement('option');
        option.value = model.value;
        option.textContent = model.text;
        modelSelect.appendChild(option);
    });
    
    // Show/hide parameter groups
    document.getElementById('dalleParams').style.display = provider === 'openai' ? 'block' : 'none';
    document.getElementById('stabilityParams').style.display = provider === 'stability' ? 'block' : 'none';
}

// Story Generation
async function generateStory() {
    // Collect images
    const totalImages = state.selectedImages.size + state.uploadedFiles.length;
    
    if (totalImages === 0) {
        showToast('Please select or upload at least one image', 'error');
        return;
    }
    
    if (totalImages > 10) {
        showToast('Maximum 10 images allowed', 'error');
        return;
    }
    
    const provider = document.getElementById('llmProvider').value;
    const apiKeyMap = {
        openai: 'openaiApiKey',
        anthropic: 'anthropicApiKey',
        google: 'googleAiApiKey'
    };
    
    const apiKey = state.apiKeys[apiKeyMap[provider]];
    if (!apiKey) {
        showToast(`Please configure ${provider} API key in settings`, 'error');
        return;
    }
    
    showLoading('Generating story...');
    
    try {
        const formData = new FormData();
        
        // Add uploaded files
        state.uploadedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        // Add selected image URLs
        formData.append('image_urls', JSON.stringify(Array.from(state.selectedImages)));
        
        // Add parameters
        formData.append('provider', provider);
        formData.append('model', document.getElementById('llmModel').value);
        formData.append('api_key', apiKey);
        formData.append('temperature', document.getElementById('temperature').value);
        formData.append('max_tokens', document.getElementById('maxTokens').value);
        formData.append('top_p', document.getElementById('topP').value);
        
        if (provider === 'anthropic' || provider === 'google') {
            formData.append('top_k', document.getElementById('topK').value);
        }
        
        const model = document.getElementById('llmModel').value;
        if (model.includes('thinking')) {
            formData.append('thinking_budget', document.getElementById('thinkingBudget').value);
        }
        
        // Add few-shot examples
        formData.append('few_shot_examples', JSON.stringify(state.fewShotExamples));
        
        const response = await fetch('/api/generate-story', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Story generation failed');
        }
        
        displayStory(data.story);
        showToast('Story generated successfully', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

function displayStory(story) {
    document.getElementById('storyText').textContent = story;
    document.getElementById('storyResult').style.display = 'block';
}

function copyStory() {
    const story = document.getElementById('storyText').textContent;
    navigator.clipboard.writeText(story).then(() => {
        showToast('Story copied to clipboard', 'success');
    });
}

function saveStory() {
    const story = document.getElementById('storyText').textContent;
    const blob = new Blob([story], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `story-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Story saved', 'success');
}

// Image Generation
async function generateImage() {
    const prompt = document.getElementById('imagePrompt').value.trim();
    const provider = document.getElementById('imageGenProvider').value;
    
    if (!prompt) {
        showToast('Please enter a prompt', 'error');
        return;
    }
    
    const apiKeyMap = {
        openai: 'openaiApiKey',
        stability: 'stabilityApiKey',
        replicate: 'replicateApiKey'
    };
    
    const apiKey = state.apiKeys[apiKeyMap[provider]];
    if (!apiKey) {
        showToast(`Please configure ${provider} API key in settings`, 'error');
        return;
    }
    
    showLoading('Generating image...');
    
    try {
        const body = {
            prompt,
            provider,
            api_key: apiKey,
            model: document.getElementById('imageGenModel').value
        };
        
        if (provider === 'openai') {
            body.size = document.getElementById('dalleSize').value;
            body.quality = document.getElementById('dalleQuality').value;
            body.style = document.getElementById('dalleStyle').value;
        } else if (provider === 'stability') {
            body.width = parseInt(document.getElementById('stabilityWidth').value);
            body.height = parseInt(document.getElementById('stabilityHeight').value);
            body.cfg_scale = parseFloat(document.getElementById('cfgScale').value);
            body.steps = parseInt(document.getElementById('steps').value);
        }
        
        const response = await fetch('/api/generate-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Image generation failed');
        }
        
        displayGeneratedImage(data.images, provider);
        showToast('Image generated successfully', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

function displayGeneratedImage(images, provider) {
    const container = document.getElementById('generatedImageResult');
    container.innerHTML = '';
    
    images.forEach(img => {
        const imgEl = document.createElement('img');
        
        if (provider === 'stability') {
            imgEl.src = `data:image/png;base64,${img}`;
        } else {
            imgEl.src = img;
        }
        
        imgEl.alt = 'Generated image';
        container.appendChild(imgEl);
    });
}

// Example Management
function previewExampleImage(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (file.size > 5 * 1024 * 1024) {
        showToast('Image must be under 5MB', 'error');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('exampleImagePreview');
        preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
    };
    reader.readAsDataURL(file);
}

function saveExample() {
    const fileInput = document.getElementById('exampleImage');
    const storyText = document.getElementById('exampleStory').value.trim();
    
    if (!fileInput.files[0]) {
        showToast('Please select an image', 'error');
        return;
    }
    
    if (!storyText) {
        showToast('Please enter a story', 'error');
        return;
    }
    
    if (state.fewShotExamples.length >= 5) {
        showToast('Maximum 5 examples allowed', 'error');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
        // Extract base64 data (remove data URL prefix)
        const base64 = e.target.result.split(',')[1];
        
        state.fewShotExamples.push({
            image_base64: base64,
            story: storyText
        });
        
        saveFewShotExamples();
        renderExamplesList();
        
        // Clear form
        fileInput.value = '';
        document.getElementById('exampleStory').value = '';
        document.getElementById('exampleImagePreview').innerHTML = '';
        
        closeModal('exampleModal');
        showToast('Example added', 'success');
    };
    
    reader.readAsDataURL(fileInput.files[0]);
}

// UI Helpers
function showLoading(message = 'Loading...') {
    document.getElementById('loadingText').textContent = message;
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
