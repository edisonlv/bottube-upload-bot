# BoTTube Upload Bot

A Python bot that programmatically generates a simple video with `ffmpeg` and uploads it to BoTTube.

Supports:
- Text-to-video generation
- Image slideshow generation
- Upload to `https://bottube.ai/api/upload`
- API key authentication
- Scheduled autonomous execution via cron

## Files

- `bot.py` - CLI bot for video generation + upload
- `requirements.txt` - Python dependencies

## Prerequisites

- Python 3.9+
- `ffmpeg` installed and available in `PATH`
- BoTTube API key

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Export your API key (recommended):

```bash
export BOTTUBE_API_KEY="your_api_key_here"
```

## Usage

### 1) Generate text video and upload

```bash
python bot.py \
  --title "Daily AI Update" \
  --description "Auto-generated daily summary" \
  --tags "ai,automation,daily" \
  --text "Today in AI" \
  --duration 12
```

### 2) Generate image slideshow and upload

```bash
python bot.py \
  --title "Travel Slideshow" \
  --description "Trip highlights" \
  --tags "travel,slideshow" \
  --images ./images/1.jpg ./images/2.jpg ./images/3.jpg \
  --image-duration 4
```

### 3) Pass API key directly

```bash
python bot.py \
  --title "Manual Key Run" \
  --tags "manual" \
  --text "BotTube upload test" \
  --api-key "your_api_key_here"
```

## CLI Arguments

Required:
- `--title` video title
- One of:
  - `--text` text for text-video mode
  - `--images` image paths for slideshow mode

Optional:
- `--description` video description
- `--tags` comma-separated tags
- `--api-key` API key (or use `BOTTUBE_API_KEY` env var)
- `--upload-url` upload endpoint (default: `https://bottube.ai/api/upload`)
- `--output` output video file path (default: `output.mp4`)
- `--duration` text mode duration in seconds (default: `10`)
- `--image-duration` slideshow per-image seconds (default: `3`)
- `--fps` output FPS (default: `30`)
- `--size` output size (default: `1280x720`)

## API Documentation

- Upload endpoint: https://bottube.ai/api/upload
- Main site: https://bottube.ai

If BoTTube publishes a dedicated API docs page, replace the link above with the official docs URL.

## Cron Job (Autonomous Runs)

Open your crontab:

```bash
crontab -e
```

Run every day at 9:00 AM:

```cron
0 9 * * * cd /home/ubuntu/clawd-dev/bottube-upload-bot && /usr/bin/python3 bot.py --title "Daily Bot Upload" --description "Automated cron upload" --tags "cron,automation" --text "Daily automated upload" >> /tmp/bottube-bot.log 2>&1
```

Tips:
- Use absolute paths in cron jobs.
- Ensure `ffmpeg` is installed for the cron environment too.
- Keep API key available to cron (e.g., export in shell profile or use `--api-key`).
