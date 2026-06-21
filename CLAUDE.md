# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Audio Streamer API — FastAPI microservice for real-time audio streaming, MP3 conversion/download, and YouTube video search. Uses `yt-dlp` for extraction and `ffmpeg` for audio transcoding.

## Architecture

- **`app.py`** — Single-file FastAPI application containing all endpoints, auth, and helper functions.
  - Endpoints: `/` (root), `/login` (JWT), `/stream` (proxy audio), `/url` (stream URL), `/download` (MP3), `/search` (video search).
  - Auth: JWT-based (`python-jose`) with static user dict; `/login` uses HTTP Basic, other endpoints require Bearer token via `Authorization` header.
  - Helper functions: `get_audio_stream_url()`, `proxy_stream()`, `download_mp3()`, `search_youtube()`.
- **`youtube_converter.py`** — Standalone CLI utility (not used by the API, just a legacy script).

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | Web framework & server |
| `yt-dlp` | YouTube metadata + audio extraction |
| `requests` | Streaming proxy (`proxy_stream`) |
| `python-jose[cryptography]` | JWT creation/validation |

## Commands

```bash
# Run development server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
pip install -r requirements.txt

# Docker
docker build -t youtube-converter .
docker run -d -p 8000:8000 -e JWT_SECRET_KEY="strong-secret" youtube-converter

# Get JWT token (default creds: admin / password123)
curl -s -X POST http://localhost:8000/login -u "admin:password123"
```

## Important Code Patterns

- **Audio extraction** uses `yt-dlp` with format `bestaudio[abr<={quality}]/bestaudio` (quality: 128/192/320).
- **Streaming proxy** (`proxy_stream()`) fetches audio in 1 MB chunks with a real browser User-Agent.
- **JWT config** via env var `JWT_SECRET_KEY` (default: `"change-me-to-a-strong-secret"`).
- **Static users** defined in `STATIC_USERS` dict — add new users here for now.
- **Downloaded MP3** files land in `downloads/` (gitignored). No cleanup logic exists yet.

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `JWT_SECRET_KEY` | `"change-me-to-a-strong-secret"` | Set a strong secret in production |
