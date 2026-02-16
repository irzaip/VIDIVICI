@echo off
echo Starting VIDIVICI...
cd /d "%~dp0"
pip install -r requirements.txt
set FAL_KEY=your_fal_key_here
set OLLAMA_HOST=http://localhost:11434
set OLLAMA_MODEL=llama3.2
python -m app.main
