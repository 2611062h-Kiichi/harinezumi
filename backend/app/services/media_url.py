import os
import shutil
from urllib.parse import urlparse

import yt_dlp
from fastapi import HTTPException

ALLOWED_SCHEMES = {"http", "https"}


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise HTTPException(status_code=400, detail="無効なURLです。http/httpsのURLを指定してください。")


def download_audio_from_url(url: str, out_dir: str, max_media_mb: int) -> tuple[str, str]:
    """Downloads audio from a URL — either a direct media file link or a
    yt-dlp-supported platform (YouTube, Vimeo, etc.) — and returns
    (local_audio_path, display_filename)."""
    _validate_url(url)
    if shutil.which("ffmpeg") is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "ffmpegがインストールされていません。URLからの音声取得にはffmpegが必要です。"
                "READMEの手順に従ってffmpegをインストールし、PATHに追加してから再度お試しください。"
            ),
        )

    out_template = os.path.join(out_dir, "url_media.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }
        ],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": max_media_mb * 1024 * 1024,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="URLから音声/動画を取得できませんでした。URLが正しいか、非公開になっていないか確認してください。",
        ) from e

    audio_path = os.path.join(out_dir, "url_media.mp3")
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=500, detail="URLからの音声抽出に失敗しました。")

    display_name = (info or {}).get("title") or "url_media"
    return audio_path, f"{display_name}.mp3"
