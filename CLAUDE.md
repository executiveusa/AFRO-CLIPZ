# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AFRO-CLIPZ is an AI-powered video clipping application that extracts relevant segments from videos based on natural language prompts. It uses multimodal analysis combining visual, audio, and sentiment cues.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the enhanced version (recommended, includes zero-secrets support)
python app_enhanced.py

# Run the original version
python app.py

# Set custom query via environment variable
USER_QUERY="Find clips about topic X" python app_enhanced.py
```

## Architecture

### Two Application Versions

- **`app.py`** - Original version with hardcoded API key placeholder, minimal error handling
- **`app_enhanced.py`** - Production-ready version with zero-secrets architecture, cost monitoring, and maintenance mode support

### Processing Pipeline

1. **Transcription**: FFmpeg extracts audio → Whisper generates timestamped transcript
2. **Segment Selection**: Transcript + user query sent to Groq API (llama-3.1-70b-versatile) or returns mock segments in stub mode
3. **Video Editing**: MoviePy extracts relevant clips, applies fade transitions, concatenates to final output

### Key Classes (app_enhanced.py)

- **`Config`**: Centralized configuration from environment variables with safe defaults
- **`CostMonitor`**: Tracks memory usage and triggers maintenance mode if limits exceeded

### Zero-Secrets Architecture

When `GROQ_API_KEY` is unset or set to `stub-key`, the app falls back to `get_relevant_segments_stubbed()` which returns mock segments from the transcript without making API calls.

## Key Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GROQ_API_KEY` | `stub-key` | Real key enables AI processing; stub mode returns mock segments |
| `WHISPER_MODEL` | `base` | Options: tiny, base, small, medium, large |
| `VIDEO_INPUT_PATH` | `input_video.mp4` | Input video file |
| `VIDEO_OUTPUT_PATH` | `edited_output.mp4` | Output video file |
| `FREE_TIER_LIMIT_MB` | `500` | Memory limit before maintenance mode triggers |
| `MAINTENANCE_MODE_ENABLED` | `false` | Set true to serve maintenance page |

## Dependencies

- **Runtime**: Python 3.12+
- **System**: FFmpeg (required for audio extraction)
- **Key packages**: openai-whisper, moviepy, torch, requests, psutil

## Deployment Configurations

- **`railway.toml`** / **`railway.json`** - Railway platform deployment
- **`nixpacks.toml`** - Nixpacks build configuration (includes ffmpeg)
- **`Procfile`** - Process definition: `web: python app.py`
- **`maintenance.html`** - Static page served when maintenance mode enabled

## Related Documentation

- `DEPLOYMENT.md` - Complete deployment guide
- `COOLIFY_MIGRATION.md` - Railway → Coolify migration steps
- `.agents` - Secret schema and integration specifications
