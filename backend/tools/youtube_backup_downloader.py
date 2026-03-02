import os
from yt_dlp import YoutubeDL
from backend.config import DOWNLOAD_FOLDER

ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": os.path.join(
        DOWNLOAD_FOLDER,
        "%(artist,uploader,creator)s",
        "%(title)s.%(ext)s",
    ),
    "ffmpeg_location": r"C:\ffmpeg-master-latest-win64-gpl-shared\bin",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "quiet": False,
    "no_warnings": True,
}


def download_url(url: str):
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print(info.keys())
        ydl.download([url])


def run_youtube_backup(url: str):
    try:
        url = url.replace("music.youtube.com", "www.youtube.com")
        download_url(url)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    while True:
        url = input("Enter Youtube URL or introduce 'quit' to exit ").strip()

        if url.lower() == "quit":
            break
        try:
            download_url(url)
        except Exception as e:
            print("error:", e)
