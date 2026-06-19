"""
YouTube Audio Streamer API
--------------------------
A FastAPI service that:
1. Returns the direct audio stream URL (without downloading).
2. Proxies the audio stream in real-time (no permanent file stored).
3. Downloads and converts to MP3.

Usage:
    uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

import yt_dlp
import requests
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="YouTube Audio Streamer",
    description="API untuk streaming audio dari YouTube secara real-time.",
    version="0.1.0"
)

# Allow CORS for local development (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
)

# --- Helper Functions ---

def get_best_audio_url(youtube_url: str) -> str:
    """
    Mengambil URL stream audio terbaik dari video YouTube dengan optimasi kecepatan.
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info["url"]
    except yt_dlp.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"URL video tidak valid atau tidak tersedia: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")

def download_mp3(youtube_url: str, output_dir: str = "./downloads") -> str:
    """
    Mendownload audio dari video YouTube dan mengonversinya ke MP3.
    Mengembalikan path file MP3 yang sudah di-download.
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s-%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "noplaylist": True,
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            base_path = ydl.prepare_filename(info)
            mp3_path = os.path.splitext(base_path)[0] + ".mp3"

            if not os.path.exists(mp3_path):
                raise HTTPException(status_code=500, detail="File MP3 gagal dibuat setelah proses download.")

            return mp3_path
    except yt_dlp.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Gagal mendownload video: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan saat download: {str(e)}")


def proxy_stream(audio_url: str):
    """
    Mengambil aliran audio dari URL langsung dan meneruskannya ke klien.
    Menambahkan header User-Agent agar tidak diblokir.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*",
        "Range": "bytes=0-",
    }
    try:
        response = requests.get(audio_url, headers=headers, stream=True, timeout=15)
        if response.status_code not in (200, 206):
            raise HTTPException(status_code=502, detail=f"Gagal mengambil stream (status: {response.status_code})")
        content_type = response.headers.get("Content-Type", "audio/mpeg")
        def generate():
            for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
                if chunk:
                    yield chunk
        return StreamingResponse(
            generate(),
            media_type=content_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": response.headers.get("Content-Length", ""),
            },
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Gagal terhubung ke sumber audio: {str(e)}")

# --- API Endpoints ---

@app.get("/")
async def root():
    return {"message": "Selamat datang di YouTube Audio Streamer API", "docs": "/docs"}

@app.get("/stream")
async def stream_audio(
    url: str = Query(..., description="URL video YouTube yang ingin di-stream audio-nya")
):
    """
    Mengembalikan aliran audio langsung dari video YouTube.
    URL akan diputar langsung oleh pemain audio (bukan didownload).
    """
    audio_url = get_best_audio_url(url)
    return proxy_stream(audio_url)

@app.get("/url")
async def get_audio_url_only(
    url: str = Query(..., description="URL video YouTube")
):
    """
    Hanya mengembalikan URL langsung ke stream audio.
    Berguna jika Anda ingin memainkan audio secara langsung di aplikasi Anda.
    """
    audio_url = get_best_audio_url(url)
    return {"audio_url": audio_url}

@app.get("/download")
async def download_audio(
    url: str = Query(..., description="URL video YouTube yang ingin di-download MP3-nya")
):
    """
    Mendownload audio dari video YouTube sebagai file MP3.
    File akan dikirim langsung ke klien sebagai lampiran.
    """
    mp3_path = download_mp3(url)
    filename = os.path.basename(mp3_path)
    return FileResponse(
        path=mp3_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# --- Main ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)