import os
import httpx
import asyncio
import tempfile
from PIL import Image
from typing import Dict, Any
import fal_client

FAL_KEY = os.getenv("FAL_KEY", "")

VIDEO_MODELS = {
    "kling_2.1": "fal-ai/kling-video/v2.1/standard/image-to-video",
    "veo2": "fal-ai/veo2/image-to-video",
    "veo3": "fal-ai/veo3/image-to-video",
    "wan2.1": "fal-ai/wan-pro/image-to-video",
    "vidu": "fal-ai/vidu/image-to-video",
    "magi": "fal-ai/magi/image-to-video",
}


async def resize_image_if_needed(image_path: str) -> str:
    if image_path.startswith("http"):
        async with httpx.AsyncClient() as client:
            response = await client.get(image_path)
            if response.status_code != 200:
                return image_path
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            
            file_size = len(response.content)
            if file_size <= 10 * 1024 * 1024:
                with Image.open(tmp_path) as img:
                    if max(img.size) <= 2048:
                        return image_path
            
            with Image.open(tmp_path) as img:
                max_dim = 2048
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                img.save(tmp_path, "JPEG", quality=85)
            
            return tmp_path
    else:
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:
                with Image.open(image_path) as img:
                    max_dim = 2048
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                    img.save(image_path, "JPEG", quality=85)
        return image_path


async def generate_video(
    image_path: str,
    prompt: str = "",
    model: str = "kling_2.1",
    aspect_ratio: str = "9:16",
    duration: str = "5",
    output_dir: str = "",
    shot_name: str = ""
) -> Dict[str, Any]:
    if not FAL_KEY or FAL_KEY == "your_fal_key_here":
        return {"success": False, "error": "FAL_KEY not configured"}
    
    os.environ["FAL_KEY"] = FAL_KEY
    
    model_endpoint = VIDEO_MODELS.get(model, VIDEO_MODELS["kling_2.1"])

    resized_path = await resize_image_if_needed(image_path)
    
    if resized_path.startswith("http"):
        image_url = resized_path
    else:
        image_url = await asyncio.to_thread(fal_client.upload_file, resized_path)

    try:
        result = await asyncio.to_thread(
            fal_client.subscribe,
            model_endpoint,
            arguments={
                "prompt": prompt or "gentle natural motion, smooth movement",
                "image_url": image_url,
                "duration": duration,
                "negative_prompt": "blur, distort, low quality",
                "cfg_scale": 0.5
            }
        )
        
        video_url = result["video"]["url"]
        
        filename = f"{shot_name}.mp4" if shot_name else "video.mp4"
        videos_dir = os.path.join(output_dir, "videos") if output_dir else "videos"
        os.makedirs(videos_dir, exist_ok=True)
        filepath = os.path.join(videos_dir, filename)

        async with httpx.AsyncClient() as client:
            video_response = await client.get(video_url)
            with open(filepath, "wb") as f:
                f.write(video_response.content)

        return {
            "success": True,
            "video_url": video_url,
            "filepath": filepath,
            "filename": filename
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
