import os
import traceback
from yt_dlp import YoutubeDL

from backend.config import DOWNLOAD_FOLDER


def build_ydl_opts(target_folder: str):
    folder_path = os.path.join(DOWNLOAD_FOLDER, target_folder)
    os.makedirs(folder_path, exist_ok=True)

    return {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(folder_path, "%(title)s.%(ext)s"),
        # Performance (KEY PART)
        "concurrent_downloads": 4,  # multiple videos at once
        "concurrent_fragment_downloads": 4,  # fragments per video
        # Audio conversion
        "ffmpeg_location": r"C:\ffmpeg-master-latest-win64-gpl-shared\bin",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",  # best VBR quality
            }
        ],
        # Stability
        "ignoreerrors": True,
        "continuedl": True,
        "overwrites": False,
        "noplaylist": False,
        # Duplicate protection
        "download_archive": os.path.join(folder_path, "downloaded.txt"),
        # Network stability
        "retries": 10,
        "fragment_retries": 10,
        # Console
        "quiet": False,
        "no_warnings": True,
    }


def download_url(url: str, folder: str = "Liked Songs"):
    ydl_opts = build_ydl_opts(folder)

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except Exception:
            print("Download error:")
            traceback.print_exc()


def run_youtube_backup(url: str, folder: str = None):
    try:
        url = url.replace("music.youtube.com", "www.youtube.com")
        target_folder = folder if folder else "Liked Songs"
        download_url(url, folder=target_folder)
        return {"status": "success"}
    except Exception:
        print("FULL ERROR:")
        traceback.print_exc()
        return {"status": "error"}


if __name__ == "__main__":
    while True:
        user_input = input(
            "Enter Youtube URL optionally followed by folder name, or 'quit': "
        ).strip()

        if user_input.lower() == "quit":
            break

        parts = user_input.split()
        url = parts[0]
        folder = " ".join(parts[1:]) if len(parts) > 1 else "Liked Songs"

        download_url(url, folder)
