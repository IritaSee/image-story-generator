import os
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def validate_image(file_storage):
    """
    Validate uploaded image file
    Returns: (is_valid, error_message)
    """
    # Check file exists
    if not file_storage:
        return False, "No file provided"
    
    # Check filename
    if file_storage.filename == '':
        return False, "No filename"
    
    # Check extension
    if not allowed_file(file_storage.filename):
        return False, f"Invalid file type. Allowed: {', '.join(current_app.config['ALLOWED_EXTENSIONS'])}"
    
    # Check file size (read first 5MB + 1 byte to check if exceeds limit)
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)
    
    max_size = current_app.config['MAX_CONTENT_LENGTH']
    if file_size > max_size:
        return False, f"File size exceeds {max_size / (1024*1024):.0f}MB limit"
    
    # Validate image content (prevents fake extensions)
    try:
        img = Image.open(file_storage)
        img.verify()
        file_storage.seek(0)  # Reset after verify
        return True, None
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


def validate_image_count(count):
    """Validate number of images"""
    max_images = current_app.config['MAX_IMAGES_PER_REQUEST']
    if count > max_images:
        return False, f"Too many images. Maximum {max_images} allowed"
    if count < 1:
        return False, "At least one image required"
    return True, None


def validate_api_key(api_key, provider):
    """Basic API key validation"""
    if not api_key:
        return False, f"API key required for {provider}"
    
    if not isinstance(api_key, str):
        return False, "Invalid API key format"
    
    # Basic length check (most API keys are at least 20 chars)
    if len(api_key.strip()) < 10:
        return False, "API key too short"
    
    return True, None
