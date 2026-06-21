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
import base64
from enum import Enum
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query, Depends, Security
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt

app = FastAPI(
    title="YouTube Audio Streamer",
    description="API untuk streaming audio dari YouTube secara real-time.",
    version="0.1.0"
)

# Allow CORS for local development (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
)

# --- Security configuration ---------------------------------------------------

# Secret key for JWT signing – in production set this via environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-to-a-strong-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Static username/password pairs (for demo purposes). Store passwords in plain text only for this simple example.
STATIC_USERS = {
    "admin": "password123",
}

# FastAPI security utilities
basic_auth = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def verify_basic_credentials(credentials: HTTPBasicCredentials = Security(basic_auth)) -> str:
    """Validate username/password using the static dict.

    Returns the username if valid, otherwise raises 401.
    """
    username = credentials.username
    password = credentials.password
    expected = STATIC_USERS.get(username)
    if expected is None or password != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return username

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token missing subject")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# --- End of security configuration --------------------------------------------

# --- Helper Functions ---

class AudioQuality(str, Enum):
    low = "128"
    medium = "192"
    high = "320"


def get_video_info(youtube_url: str) -> dict:
    """
    Mengambil metadata detail video YouTube dari URL.
    Tidak mendownload, hanya ekstrak info.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_id = info.get("id")
            return {
                "id": video_id,
                "title": info.get("title"),
                "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else youtube_url,
                "duration": info.get("duration"),
                "duration_string": _format_duration(info.get("duration")),
                "thumbnail": info.get("thumbnail") or (f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else None),
                "thumbnails": info.get("thumbnails", []),
                "channel": info.get("channel") or info.get("uploader"),
                "channel_id": info.get("channel_id"),
                "channel_url": info.get("channel_url") or info.get("uploader_url"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "description": info.get("description"),
                "upload_date": info.get("upload_date"),
                "tags": info.get("tags", []),
                "categories": info.get("categories", []),
                "is_live": info.get("is_live", False),
                "availability": info.get("availability"),
                "formats": [
                    {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "abr": f.get("abr"),
                        "vcodec": f.get("vcodec"),
                        "acodec": f.get("acodec"),
                        "filesize": f.get("filesize"),
                        "format_note": f.get("format_note"),
                    }
                    for f in info.get("formats", [])
                    if f.get("acodec") != "none"  # hanya format yang punya audio
                ],
            }
    except yt_dlp.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"URL video tidak valid atau tidak tersedia: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan saat mengambil info: {str(e)}")


def _format_duration(seconds: int | None) -> str | None:
    """Format duration in seconds to HH:MM:SS or MM:SS."""
    if seconds is None:
        return None
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def search_youtube(query: str, max_results: int = 10) -> list[dict]:
    """
    Mencari video YouTube berdasarkan kata kunci menggunakan yt-dlp.
    Mengembalikan daftar hasil pencarian dengan metadata.
    """
    search_query = f"ytsearch{max_results}:{query}"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,   # faster — tidak mengekstrak info detail per video
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            entries = info.get("entries", [])
            results = []
            for entry in entries:
                if entry is None:
                    continue
                video_id = entry.get("id")
                results.append({
                    "id": video_id,
                    "title": entry.get("title"),
                    "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
                    "duration": entry.get("duration"),
                    "thumbnail": entry.get("thumbnail") or (f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else None),
                    "channel": entry.get("channel") or entry.get("uploader"),
                    "channel_url": entry.get("channel_url") or entry.get("uploader_url"),
                    "view_count": entry.get("view_count"),
                })
            return results
    except yt_dlp.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Gagal mencari video: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan saat mencari: {str(e)}")


def get_audio_stream_url(youtube_url: str, quality: AudioQuality = AudioQuality.medium) -> str:
    """
    Mengambil URL stream audio berdasarkan kualitas yang diminta.
    """
    ydl_opts = {
        "format": f"bestaudio[abr<={quality.value}]/bestaudio",
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

def download_mp3(youtube_url: str, quality: AudioQuality = AudioQuality.medium, output_dir: str = "./downloads") -> str:
    """
    Mendownload audio dari video YouTube dan mengonversinya ke MP3.
    Mengembalikan path file MP3 yang sudah di-download.
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": f"bestaudio[abr<={quality.value}]/bestaudio",
        "outtmpl": os.path.join(output_dir, "%(title)s-%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality.value,
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

# --- API Endpoints -----------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Selamat datang di YouTube Audio Streamer API", "docs": "/docs"}

@app.post("/login")
async def login(current_user: str = Depends(verify_basic_credentials)):
    """Authenticate using HTTP Basic and return a JWT.

    The client sends `Authorization: Basic <base64>` header. FastAPI's `HTTPBasic`
    dependency extracts the credentials and `verify_basic_credentials` validates
    them against the static user dict. If valid, a JWT containing the username as
    the `sub` claim is returned.
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": current_user}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/stream")
async def stream_audio(
    url: str = Query(..., description="URL video YouTube yang ingin di-stream audio-nya"),
    quality: AudioQuality = Query(default=AudioQuality.medium, description="Kualitas audio: 128, 192, atau 320 kbps"),
    current_user: str = Depends(get_current_user)
):
    """
    Mengembalikan aliran audio langsung dari video YouTube.
    URL akan diputar langsung oleh pemain audio (bukan didownload).
    Memerlukan token JWT yang valid.
    """
    audio_url = get_audio_stream_url(url, quality)
    return proxy_stream(audio_url)

@app.get("/url")
async def get_audio_url_only(
    url: str = Query(..., description="URL video YouTube"),
    quality: AudioQuality = Query(default=AudioQuality.medium, description="Kualitas audio: 128, 192, atau 320 kbps"),
    current_user: str = Depends(get_current_user)
):
    """
    Hanya mengembalikan URL langsung ke stream audio.
    Berguna jika Anda ingin memainkan audio secara langsung di aplikasi Anda.
    Memerlukan token JWT yang valid.
    """
    audio_url = get_audio_stream_url(url, quality)
    return {"audio_url": audio_url}

@app.get("/download")
async def download_audio(
    url: str = Query(..., description="URL video YouTube yang ingin di-download MP3-nya"),
    quality: AudioQuality = Query(default=AudioQuality.medium, description="Kualitas audio: 128, 192, atau 320 kbps"),
    current_user: str = Depends(get_current_user)
):
    """
    Mendownload audio dari video YouTube sebagai file MP3.
    File akan dikirim langsung ke klien sebagai lampiran.
    Memerlukan token JWT yang valid.
    """
    mp3_path = download_mp3(url, quality)
    filename = os.path.basename(mp3_path)
    return FileResponse(
        path=mp3_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/search")
async def search_video(
    q: str = Query(..., min_length=1, description="Kata kunci pencarian video YouTube"),
    max_results: int = Query(default=10, ge=1, le=50, description="Jumlah maksimal hasil (1-50)"),
    current_user: str = Depends(get_current_user)
):
    """
    Mencari video YouTube berdasarkan kata kunci.
    Mengembalikan daftar video beserta metadata (judul, durasi, channel, dll).
    Memerlukan token JWT yang valid.
    """
    results = search_youtube(q, max_results)
    return {
        "query": q,
        "total": len(results),
        "results": results,
    }

@app.get("/video-detail")
async def get_video_details(
    url: str = Query(..., description="URL video YouTube yang ingin diambil detailnya"),
    current_user: str = Depends(get_current_user)
):
    """
    Mengambil detail lengkap video YouTube (judul, durasi, thumbnail, deskripsi, dll).
    Memerlukan token JWT yang valid.
    """
    return get_video_info(url)


# --- Main ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)