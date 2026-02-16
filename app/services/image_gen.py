import os
import httpx
import asyncio
from typing import Dict, Any, List
import fal_client

FAL_KEY = os.getenv("FAL_KEY", "")

IMAGE_MODELS = {
    "seedream_v4.5": "fal-ai/bytedance/seedream/v4.5/text-to-image",
    "seedream_v4": "fal-ai/bytedance/seedream/v4/text-to-image",
    "seedream_v3": "fal-ai/bytedance/seedream/v3/text-to-image",
    "flux_dev": "fal-ai/flux/dev",
    "flux_pro": "fal-ai/flux/pro",
    "flux_2_pro": "fal-ai/flux2/pro",
    "flux_2_flex": "fal-ai/flux2/flex",
}

ASPECT_RATIO_MAP = {
    "9:16": "portrait_16_9",
    "16:9": "landscape_16_9",
}


async def generate_images(
    prompt: str,
    aspect_ratio: str = "9:16",
    num_images: int = 4,
    model: str = "seedream_v4.5",
    output_dir: str = "",
    shot_name: str = ""
) -> List[Dict[str, Any]]:
    if not FAL_KEY or FAL_KEY == "your_fal_key_here":
        return [{"error": "FAL_KEY not configured"}]
    
    os.environ["FAL_KEY"] = FAL_KEY
    
    model_endpoint = IMAGE_MODELS.get(model, IMAGE_MODELS["seedream_v4.5"])
    
    image_size = ASPECT_RATIO_MAP.get(aspect_ratio, "portrait_16_9")
    
    results = []
    
    async def generate_one(idx: int):
        try:
            print(f"Generating image {idx} with model {model_endpoint}")
            
            result = await asyncio.to_thread(
                fal_client.subscribe,
                model_endpoint,
                arguments={
                    "prompt": prompt,
                    "image_size": image_size,
                    "num_images": 1
                }
            )
            
            print(f"Result: {result}")
            
            if not result or "images" not in result:
                return {"error": f"No images in result: {result}"}
            
            image_url = result["images"][0]["url"]
            
            filename = f"{shot_name}-{chr(97+idx)}.JPG" if shot_name else f"image_{idx}.JPG"
            filepath = os.path.join(output_dir, filename)
            
            async with httpx.AsyncClient() as client:
                img_response = await client.get(image_url)
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
            
            return {
                "url": image_url,
                "filename": filename,
                "filepath": filepath,
                "variant": chr(97+idx)
            }
        except Exception as e:
            import traceback
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    tasks = [generate_one(i) for i in range(num_images)]
    results = await asyncio.gather(*tasks)
    
    return results
