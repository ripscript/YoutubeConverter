# YouTube Audio Streamer API

API untuk streaming audio dan download MP3 langsung dari video YouTube menggunakan **FastAPI**.

> **Fitur utama:**
> - Streaming audio real-time (bukan download permanen)
> - Mendapatkan URL stream audio secara langsung
> - **Download & convert audio ke MP3** (membutuhkan `ffmpeg`)
> - Siap untuk dijadikan microservice

---

## 📋 Daftar Isi

1. [Prasyarat](#prasyarat)
2. [Instalasi](#instalasi)
3. [Menjalankan Aplikasi](#menjalankan-aplikasi)
4. [Penggunaan API](#penggunaan-api)
5. [Docker](#docker)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Prasyarat

- Python 3.12.3
- `ffmpeg` (opsional, diperlukan kalau ingin download & convert ke MP3)

### Instalasi `ffmpeg` (jika belum):

**Ubuntu/Debian (WSL2):**
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

---

## 📦 Instalasi

1. **Masuk ke direktori proyek:**
   ```bash
   cd /home/ripscript/project/youtube-converter
   ```

2. **Buat & aktifkan virtual environment (jika belum):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

   Atau install manual:
   ```bash
   pip install fastapi uvicorn requests yt-dlp
   ```

---

## ▶️ Menjalankan Aplikasi

Jalankan server FastAPI:

```bash
# Pastikan venv sudah aktif
source venv/bin/activate

# Jalankan server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

> Server akan berjalan di `http://localhost:8000`

---

## 🌐 Penggunaan API

### Buka dokumentasi otomatis (Swagger UI):
```
http://localhost:8000/docs
```

### Endpoint 1: Dapatkan URL stream audio
```bash
curl "http://localhost:8000/url?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Response:**
```json
{
  "audio_url": "https://r4---sn-5uaeznzs.googlevideo.com/..."
}
```

### Endpoint 2: Stream audio langsung
Bisa diputar langsung di browser:
```
http://localhost:8000/stream?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Atau pakai `ffplay`:
```bash
ffplay -autoexit "http://localhost:8000/stream?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Atau di HTML:
```html
<audio controls>
  <source src="http://localhost:8000/stream?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" type="audio/mp4">
</audio>
```

### Endpoint 3: Download & konversi audio ke MP3

Mendownload audio dari video YouTube dan mengonversinya ke file MP3 (membutuhkan `ffmpeg` terinstal):

```bash
curl -o "audio.mp3" "http://localhost:8000/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Atau di browser, buka URL:
```
http://localhost:8000/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### 🎵 Pilihan Kualitas Audio

Semua endpoint menerima parameter opsional `quality` untuk mengatur bitrate audio:

| Nilai | Bitrate |
|-------|---------|
| `low` | 128 kbps |
| `medium` | 192 kbps (default) |
| `high` | 320 kbps |

**Contoh penggunaan:**
```bash
# Streaming dengan kualitas tinggi
curl "http://localhost:8000/stream?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=high"

# URL audio dengan kualitas rendah (hemat bandwidth)
curl "http://localhost:8000/url?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=low"

# Download MP3 kualitas tinggi (320 kbps)
curl -o "audio.mp3" "http://localhost:8000/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=high"
```

> **Catatan:** Kualitas yang dipilih adalah batas maksimal (bitrate ≤ nilai yang diminta). Jika YouTube tidak menyediakan bitrate yang diminta, yt-dlp akan memilih kualitas terbaik yang tersedia di bawah bitrate tersebut.

---

## 🐳 Docker

Proyek ini sudah siap dijalankan dengan Docker. Container akan otomatis menyertakan `ffmpeg`, Python, dan semua dependensi.

### Build Image

```bash
docker build -t youtube-converter .
```

### Jalankan Container

```bash
docker run -d -p 8000:8000 --name youtube-converter youtube-converter
```

Akses di `http://localhost:8000`.

### Setel JWT_SECRET_KEY

Untuk keamanan, setel `JWT_SECRET_KEY` saat menjalankan container:

```bash
docker run -d -p 8000:8000 -e JWT_SECRET_KEY="rahasiakuat123" --name youtube-converter youtube-converter
```

> **⚠️ Penting:** Di production, gunakan kunci yang kuat dan acak. Tanpa disetel, akan dipakai nilai default yang tidak aman.

**Ganti port host (misal 8080):**
```bash
docker run -d -p 8080:8000 --name youtube-converter youtube-converter
```

**Lihat log langsung (foreground):**
```bash
docker run -it --rm -p 8000:8000 youtube-converter
```

### Management Container

```bash
# Hentikan
docker stop youtube-converter

# Mulai lagi
docker start youtube-converter

# Hapus container
docker rm youtube-converter
```

---

## ❓ Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `HTTP Error 400` | Pastikan `yt-dlp` yang terbaru terinstal (`pip install --upgrade yt-dlp`) |
| `Connection refused` | Pastikan server sudah berjalan di port 8000 |
| Audio tidak muncul di browser | Browser mungkin tidak mendukung format audio. Coba pakai `ffplay` dulu |
| `ffmpeg` tidak ditemukan | Pastikan `ffmpeg` sudah terinstal di sistem (lihat [Prasyarat](#prasyarat)) |
| Download MP3 gagal | Periksa apakah `ffmpeg` sudah terinstal dan video tersedia |
| File MP3 tidak muncul | Cek folder `downloads/` — pastikan ada dan writable |
| Stream/URL lambat atau error | Server otomatis menambahkan header User-Agent agar tidak diblokir. Pastikan koneksi internet stabil. |

**Selamat mencoba! Jika ada error, beri tahu saya apa pesan errornya.**