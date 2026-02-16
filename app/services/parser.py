import re
from typing import List, Dict, Any


async def parse_storyboard(markdown: str) -> List[Dict[str, Any]]:
    shots = fallback_parse(markdown)

    for i, shot in enumerate(shots):
        if "shot_number" not in shot:
            shot["shot_number"] = str(i + 1).zfill(2)
        if "aspect_ratio" not in shot:
            shot["aspect_ratio"] = "9:16"

    return shots


def fallback_parse(markdown: str) -> List[Dict[str, Any]]:
    shots = []
    lines = markdown.split("\n")
    current_shot = None
    prompt_lines = []
    capture_prompt = False

    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("###") and "Shot" in stripped:
            if current_shot and prompt_lines:
                current_shot["prompt"] = " ".join(prompt_lines).strip()
                prompt_lines = []
            if current_shot:
                shots.append(current_shot)
            num = re.search(r'Shot\s*(\d+)', stripped, re.IGNORECASE)
            current_shot = {
                "shot_number": num.group(1).zfill(2) if num else str(len(shots) + 1).zfill(2),
                "scene": "",
                "duration": "",
                "narration": "",
                "prompt": "",
                "aspect_ratio": "9:16"
            }
            capture_prompt = False
        elif "Prompt Video:" in stripped or stripped.startswith("Prompt:"):
            capture_prompt = True
            prompt_text = stripped.split(":", 1)[-1].strip()
            if prompt_text:
                prompt_lines.append(prompt_text)
        elif capture_prompt and stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            prompt_lines.append(stripped)
        elif "16:9" in stripped:
            if current_shot:
                current_shot["aspect_ratio"] = "16:9"
        elif stripped.startswith("##") and "SCENE" in stripped:
            if current_shot:
                current_shot["scene"] = stripped

    if current_shot and prompt_lines:
        current_shot["prompt"] = " ".join(prompt_lines).strip()
    if current_shot:
        shots.append(current_shot)

    return shots
