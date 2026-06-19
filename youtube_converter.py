import yt_dlp
import os

def download_mp3(youtube_url: str, output_path: str = "./downloads") -> str:
    """
    Downloads the audio from a YouTube video and converts it to an MP3 file using yt-dlp.
    """
    try:
        # Create output directory
        os.makedirs(output_path, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading and converting to MP3: {youtube_url}")
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            print(f"Download complete: {filename}")
            return filename

    except Exception as e:
        return f"An error occurred: {e}"

def get_audio_stream_url(youtube_url: str) -> str:
    """
    Gets the direct URL to the highest quality audio stream using yt-dlp.
    """
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Fetching audio stream URL: {youtube_url}")
            info = ydl.extract_info(youtube_url, download=False)
            return info['url']

    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    print("--- YouTube Converter (yt-dlp version) ---")

    # Test URL (simple video)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Test MP3 download
    print("\nTesting MP3 download...")
    mp3_result = download_mp3(test_url)
    print(f"MP3 Download Result: {mp3_result}")
