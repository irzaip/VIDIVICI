import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from app.services.parser import parse_storyboard
from app.services.image_gen import generate_images
from app.services.video_gen import generate_video

app = FastAPI(title="VIDIVICI - AI Video Generator")

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")

@app.get("/projects/{project_name}/{filename}")
async def serve_project_file(project_name: str, filename: str):
    file_path = BASE_DIR / project_name / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    from fastapi.responses import FileResponse
    return FileResponse(file_path)

@app.get("/videos/{project_name}/{filename}")
async def serve_video(project_name: str, filename: str):
    file_path = BASE_DIR / project_name / "videos" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    from fastapi.responses import FileResponse
    return FileResponse(file_path, media_type="video/mp4")

IMAGE_MODELS = [
    {"id": "seedream_v4.5", "name": "Seedream v4.5"},
    {"id": "seedream_v4", "name": "Seedream v4"},
    {"id": "seedream_v3", "name": "Seedream v3"},
    {"id": "flux_dev", "name": "FLUX.1 Dev"},
    {"id": "flux_pro", "name": "FLUX.1 Pro"},
    {"id": "flux_2_pro", "name": "FLUX.2 Pro"},
    {"id": "flux_2_flex", "name": "FLUX.2 Flex"},
]

VIDEO_MODELS = [
    {"id": "kling_2.1", "name": "Kling 2.1"},
    {"id": "veo2", "name": "Veo 2"},
    {"id": "veo3", "name": "Veo 3"},
    {"id": "wan2.1", "name": "Wan 2.1"},
    {"id": "vidu", "name": "Vidu"},
    {"id": "magi", "name": "MAGI-1"},
]

ASPECT_RATIOS = [
    {"id": "9:16", "name": "9:16 (Portrait)"},
    {"id": "16:9", "name": "16:9 (Landscape)"},
]

class ParseRequest(BaseModel):
    project_name: str
    storyboard: str
    image_model: str = "seedream_v4.5"
    aspect_ratio: str = "9:16"

class GenerateImagesRequest(BaseModel):
    project_name: str
    shots: List[Dict[str, Any]]
    image_model: str = "seedream_v4.5"
    aspect_ratio: str = "9:16"

class SelectImagesRequest(BaseModel):
    project_name: str
    selections: Dict[str, List[str]]

class GenerateVideoRequest(BaseModel):
    project_name: str
    selections: Dict[str, List[str]]
    video_model: str = "veo2"
    aspect_ratio: str = "9:16"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "image_models": IMAGE_MODELS,
        "video_models": VIDEO_MODELS,
        "aspect_ratios": ASPECT_RATIOS
    })

@app.post("/api/parse")
async def api_parse(request: ParseRequest):
    try:
        shots = await parse_storyboard(request.storyboard)

        project_dir = BASE_DIR / request.project_name
        project_dir.mkdir(exist_ok=True)

        return {
            "success": True,
            "project_name": request.project_name,
            "shots": shots,
            "image_model": request.image_model,
            "aspect_ratio": request.aspect_ratio
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-images")
async def api_generate_images(request: GenerateImagesRequest):
    try:
        project_dir = BASE_DIR / request.project_name
        project_dir.mkdir(exist_ok=True)

        print(f"Generating images for project: {request.project_name}")
        print(f"Shots: {request.shots}")

        all_results = []

        for shot in request.shots:
            shot_name = f"SHOT-{shot['shot_number'].zfill(2)}"
            prompt = shot.get("prompt", "")
            shot_model = shot.get("image_model", request.image_model)
            shot_aspect = shot.get("aspect_ratio", request.aspect_ratio)

            print(f"Generating for shot {shot_name}: model={shot_model}, aspect={shot_aspect}")

            results = await generate_images(
                prompt=prompt,
                aspect_ratio=shot_aspect,
                num_images=4,
                model=shot_model,
                output_dir=str(project_dir),
                shot_name=shot_name
            )
            
            print(f"Results for {shot_name}: {results}")

            all_results.append({
                "shot": shot,
                "images": results
            })

        return {
            "success": True,
            "project_name": request.project_name,
            "results": all_results
        }
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-videos")
async def api_generate_videos(request: GenerateVideoRequest):
    try:
        project_dir = BASE_DIR / request.project_name

        all_results = {}
        
        tasks = []
        task_info = []
        for shot_name, variants in request.selections.items():
            for variant in variants:
                image_filename = f"{shot_name}-{variant}.JPG"
                image_path = project_dir / image_filename
                if image_path.exists():
                    tasks.append(generate_video(
                        image_path=str(image_path),
                        prompt="gentle natural motion, smooth movement",
                        model=request.video_model,
                        aspect_ratio=request.aspect_ratio,
                        output_dir=str(project_dir),
                        shot_name=f"{shot_name}-{variant}"
                    ))
                    task_info.append((shot_name, variant))

        if tasks:
            for i in range(0, len(tasks), 2):
                batch = tasks[i:i+2]
                batch_info = task_info[i:i+2]
                
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                for j, result in enumerate(results):
                    if isinstance(result, Exception):
                        all_results[f"error_{i+j}"] = {"success": False, "error": str(result)}
                    else:
                        shot_key, var_key = batch_info[j]
                        all_results[f"{shot_key}-{var_key}"] = result

        return {
            "success": True,
            "project_name": request.project_name,
            "results": all_results
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")

@app.get("/api/projects")
async def list_projects():
    try:
        projects = []
        for item in BASE_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name != '__pycache__':
                all_images = list(item.glob("*.JPG")) + list(item.glob("*.jpg"))
                images = []
                seen = set()
                for img in all_images:
                    if img.name.lower() not in seen:
                        seen.add(img.name.lower())
                        images.append(img)
                
                videos = list((item / "videos").glob("*.mp4")) if (item / "videos").exists() else []
                
                shots = []
                for img in images:
                    match = re.match(r'SHOT-(\d+)-(.+)\.JPG', img.name, re.IGNORECASE)
                    if match:
                        shot_num = match.group(1)
                        if shot_num not in shots:
                            shots.append(shot_num)
                
                projects.append({
                    "name": item.name,
                    "shots": sorted(shots),
                    "image_count": len(images),
                    "video_count": len(videos)
                })
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_name}/images")
async def get_project_images(project_name: str):
    try:
        project_dir = BASE_DIR / project_name
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        images = []
        seen = set()
        for img in sorted(project_dir.glob("*.JPG")) + sorted(project_dir.glob("*.jpg")):
            if img.name.lower() not in seen:
                seen.add(img.name.lower())
                images.append({
                    "name": img.name,
                    "url": f"/projects/{project_name}/{img.name}"
                })
        return {"project_name": project_name, "images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_name}/videos")
async def get_project_videos(project_name: str):
    try:
        project_dir = BASE_DIR / project_name
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        videos_dir = project_dir / "videos"
        videos = []
        if videos_dir.exists():
            for vid in sorted(videos_dir.glob("*.mp4")):
                videos.append({
                    "name": vid.name,
                    "url": f"/videos/{project_name}/{vid.name}"
                })
        return {"project_name": project_name, "videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host=host, port=port)
