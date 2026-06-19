# Panduan Claude Code untuk YouTube Audio Streamer API

Ini adalah panduan untuk membantu Claude Code lebih cepat memahami dan membantu Anda dengan proyek **YouTube Audio Streamer API**.

## 📝 Ringkasan Proyek

Proyek ini adalah API berbasis FastAPI yang memungkinkan streaming audio real-time dan konversi/download audio MP3 dari video YouTube. Tujuannya adalah menyediakan microservice untuk fungsionalitas audio YouTube.

## 🎯 Tujuan Claude Code

Saya dapat membantu Anda dengan:
- Debugging dan pemecahan masalah (troubleshooting)
- Implementasi fitur baru dari roadmap
- Penulisan tes
- Optimalisasi kode
- Pengaturan Docker
- Menjelaskan bagian-bagian kode atau fungsionalitas API

## 🚀 Setup Cepat

Untuk memulai bekerja dengan proyek ini, ikuti langkah-langkah berikut:

1.  **Prasyarat:**
    *   Python 3.12.3
    *   `ffmpeg` (opsional, diperlukan untuk download & convert MP3)
        *   **Ubuntu/Debian (WSL2):** `sudo apt-get update && sudo apt-get install -y ffmpeg`
        *   **macOS:** `brew install ffmpeg`

2.  **Instalasi Dependensi:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

## ▶️ Menjalankan Aplikasi

Pastikan virtual environment aktif, lalu jalankan server FastAPI:

```bash
source venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```
Server akan berjalan di `http://localhost:8000`.

## 🌐 Fitur Utama & Endpoint API

Akses dokumentasi otomatis (Swagger UI) di `http://localhost:8000/docs`.

**Endpoint yang tersedia:**

*   **Dapatkan URL stream audio:**
    *   `GET /url?url=<youtube_video_url>`
    *   Mengembalikan URL langsung untuk streaming audio.
    *   Contoh: `curl "http://localhost:8000/url?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"`

*   **Stream audio langsung:**
    *   `GET /stream?url=<youtube_video_url>`
    *   Streaming audio real-time yang dapat langsung diputar di browser atau `ffplay`.
    *   Contoh: `http://localhost:8000/stream?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ`

*   **Download & konversi audio ke MP3:**
    *   `GET /download?url=<youtube_video_url>`
    *   Mendownload dan mengonversi audio ke file MP3 (membutuhkan `ffmpeg`).
    *   File disimpan sementara di folder `downloads/`.
    *   Kualitas default: 192 kbps.
    *   Contoh: `curl -o "audio.mp3" "http://localhost:8000/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"`

## ❓ Troubleshooting

*   **`HTTP Error 400`**: Pastikan `yt-dlp` terbaru (`pip install --upgrade yt-dlp`).
*   **`Connection refused`**: Pastikan server berjalan di port 8000.
*   **Audio tidak muncul di browser**: Browser mungkin tidak mendukung format. Coba `ffplay`.
*   **`ffmpeg` tidak ditemukan**: Pastikan `ffmpeg` terinstal (lihat bagian Prasyarat).
*   **Download MP3 gagal**: Periksa instalasi `ffmpeg` dan ketersediaan video.
*   **File MP3 tidak muncul**: Cek folder `downloads/` (harus ada dan writable).

## 🚀 Roadmap

*   [x] **Download & convert ke MP3**
*   [x] **Streaming & URL endpoint stabil** (optimasi `yt-dlp` dan header User-Agent)
*   [x] Pilihan kualitas audio (128kbps, 192kbps, 320kbps)
*   [ ] Authentication/JWT
*   [ ] Docker setup

---
Saya siap membantu Anda dengan proyek ini. Beri tahu saya jika ada tugas atau pertanyaan!
