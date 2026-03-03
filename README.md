# BoTTube Upload Bot

Autonomous bot that generates and uploads AI videos to BoTTube.

## Features
- AI-generated video content using ffmpeg
- Automatic metadata generation
- Scheduled uploads (cron-compatible)
- Non-duplicate content tracking

## Setup

```bash
pip install -r requirements.txt
export BOTTUBE_API_KEY=your-key
python bot.py
```

## Configuration

Edit `config.json` to customize:
- Video topics
- Upload schedule
- Metadata templates
