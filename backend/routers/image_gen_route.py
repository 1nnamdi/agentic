from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from io import BytesIO
from fastapi.responses import StreamingResponse
from config.model import generate_image_serverless
from PIL.Image import UnidentifiedImageError
import os


router = APIRouter()


# Define Pydantic model to handle prompt input
class ImageRequest(BaseModel):
    prompt: str

@router.post("/serverless-image-generation/")#, tags=["Image Generation"])
async def serverless_image_generation(prompt: str):
   # prompt = request.prompt
   # Initiate the huggingface API token
    TOKEN =os.environ.get("HF_API_TOKEN")

    try:
        image = generate_image_serverless(prompt, TOKEN)
        
        # Convert the image to bytes for streaming response
        buffer = BytesIO()
        try:
            image.save(buffer, format="PNG")
        except UnidentifiedImageError:
            raise HTTPException(status_code=500, detail="Failed to encode the generated image")
        except AttributeError:
            raise HTTPException(status_code=500, detail="Invalid image object returned from generation")
            
        buffer.seek(0)
        
        headers = {
            'Content-Disposition': 'inline; filename="generated_image.png"',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        return StreamingResponse(
            buffer, 
            media_type="image/png",
           headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Image generation failed: {str(e)}"
        )
    
