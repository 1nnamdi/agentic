#from diffusers import StableDiffusionPipeline, FluxPipeline
# import torch
import requests
from PIL import Image
import io
import os
import json



def generate_image_serverless(prompt: str, TOKEN: str):
    """
    Generate an image using the Flux model via Hugging Face model API.
    """
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if not TOKEN:
        raise ValueError("HF_API_TOKEN environment variable is not set")

    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        response.raise_for_status()  # Raise an exception for bad status codes

        # Check if response is JSON (error message) instead of bytes
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            error_data = response.json()
            raise ValueError(f"API returned error: {error_data}")

        # Ensure we have image data
        image_bytes = response.content
        if not image_bytes:
            raise ValueError("No image data received from API")

        # Try to open the image data
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Verify it's a valid image
        image = Image.open(io.BytesIO(image_bytes))  # Reopen after verify
        return image

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API request failed: {str(e)}")
    except (ValueError, IOError) as e:
        raise RuntimeError(f"Image processing failed: {str(e)}")
    