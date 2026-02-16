# VIDIVICI - AI Video Generation Web App

An AI-powered web application that transforms storyboard markdown into videos using image generation (Bytedance Seedream 4.5) and video generation (Kling 2.1) via fal.ai API.

## Features

- **Storyboard Parser**: Parse markdown storyboards into individual shots using regex
- **Image Generation**: Generate images from shot descriptions using Bytedance Seedream 4.5
- **Video Generation**: Animate images into videos using Kling 2.1
- **Project Management**: Load and manage existing projects from directories
- **Flexible Controls**: Per-shot model selection and aspect ratio (9:16 or 16:9)
- **Live Status Console**: Real-time progress monitoring

## Requirements

- Python 3.11+
- fal.ai API key

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory:

```env
FAL_KEY=your_fal_api_key_here
```

Get your fal.ai API key at: https://fal.ai/dashboard/keys

## Usage

### Start the Server

```bash
python -m uvicorn app.main:app --reload --port 8001
```

Or use the provided batch file:

```bash
run.bat
```

### Access the Web UI

Open your browser to: http://localhost:8001

## Workflow

1. **Input Step**: Enter your storyboard in markdown format
2. **Confirm Step**: Review parsed shots, adjust models/aspect ratios, delete unwanted shots
3. **Select Images**: Choose which shots to generate images for
4. **Generate Videos**: Generate videos from selected images

## Storyboard Format

```markdown
# Shot 1
A wide shot of a sunset over mountains

# Shot 2  
Close-up of a flower in the foreground
```

Each shot starts with `# Shot N` followed by a description.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/api/parse` | POST | Parse storyboard markdown |
| `/api/generate-images` | POST | Generate images for shots |
| `/api/generate-videos` | POST | Generate videos from images |
| `/api/projects` | GET | List existing projects |
| `/api/projects/{name}` | GET | Load specific project |
| `/api/save-shots` | POST | Save shots to project |

## Project Structure

```
VIDIVICI/
├── app/
│   ├── main.py              # FastAPI server and routes
│   ├── services/
│   │   ├── parser.py       # Storyboard parser
│   │   ├── image_gen.py    # fal.ai image generation
│   │   └── video_gen.py    # fal.ai video generation
│   └── templates/
│       └── index.html      # Web UI
├── .env                    # API configuration
├── requirements.txt        # Python dependencies
└── run.bat                 # Quick start script
```

## Generated Output

Each project creates a directory with:
- `SHOT-XX-x.JPG` - Generated images
- `videos/SHOT-XX-x.mp4` - Generated videos

## Models

- **Image**: Bytedance Seedream 4.5 (`fal-ai/bytedance/seedream/v4.5/text-to-image`)
- **Video**: Kling 2.1 (`fal-ai/kling-video/v2.1/standard/image-to-video`)

## License

MIT
