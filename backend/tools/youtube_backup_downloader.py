import os
import traceback
import logging
from yt_dlp import YoutubeDL

from backend.config import DOWNLOAD_FOLDER

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def build_ydl_opts(target_folder: str):
    folder_path = os.path.join(DOWNLOAD_FOLDER, target_folder)
    os.makedirs(folder_path, exist_ok=True)

    logger.info(f"Preparing download folder: {folder_path}")

    return {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(folder_path, "%(title)s.%(ext)s"),
        "concurrent_downloads": 4,
        "concurrent_fragment_downloads": 4,
        "ffmpeg_location": r"C:\ffmpeg-master-latest-win64-gpl-shared\bin",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        ],
        "ignoreerrors": True,
        "continuedl": True,
        "overwrites": False,
        "noplaylist": False,
        "download_archive": os.path.join(folder_path, "downloaded.txt"),
        "retries": 10,
        "fragment_retries": 10,
        "quiet": False,
        "no_warnings": True,
    }


def _extract_song_titles(info: dict) -> list[str]:
    if not info:
        return []

    if isinstance(info.get("entries"), list):
        return [
            entry.get("title")
            for entry in info["entries"]
            if isinstance(entry, dict) and entry.get("title")
        ]

    if info.get("title"):
        return [info["title"]]

    return []


def download_url(url: str, folder: str = "Liked Songs"):
    ydl_opts = build_ydl_opts(folder)
    folder_path = os.path.join(DOWNLOAD_FOLDER, folder)

    logger.info(f"Starting download for URL: {url}")

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            planned_songs = _extract_song_titles(info)

            logger.info(f"Planned downloads: {len(planned_songs)} items")

            ydl.download([url])

            logger.info("Download completed successfully")

            return {
                "status": "success",
                "download_folder": folder_path,
                "downloaded_songs": planned_songs,
                "downloaded_count": len(planned_songs),
                "source_url": url,
            }

        except Exception as e:
            logger.error("Download error occurred")
            logger.error(traceback.format_exc())

            return {
                "status": "error",
                "download_folder": folder_path,
                "downloaded_songs": [],
                "downloaded_count": 0,
                "source_url": url,
            }


def run_youtube_backup(url: str, folder: str = None):
    try:
        url = url.replace("music.youtube.com", "www.youtube.com")
        target_folder = folder if folder else "Liked Songs"

        logger.info(f"Running YouTube backup. Target folder: {target_folder}")

        result = download_url(url, folder=target_folder)
        result["target_folder"] = target_folder

        return result

    except Exception:
        logger.error("Fatal error during YouTube backup")
        logger.error(traceback.format_exc())

        return {
            "status": "error",
            "target_folder": folder if folder else "Liked Songs",
            "downloaded_songs": [],
            "downloaded_count": 0,
        }


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
