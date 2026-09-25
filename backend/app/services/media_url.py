import os
from urllib.parse import urlparse

import yt_dlp
from fastapi import HTTPException

ALLOWED_SCHEMES = {"http", "https"}

# Whisper accepts these directly, so the format selector is constrained to
# them — no local ffmpeg conversion/merge step is ever needed.
FORMAT_SELECTOR = "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[ext=mp3]/best[ext=mp4]/best[ext=webm]"


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise HTTPException(status_code=400, detail="無効なURLです。http/httpsのURLを指定してください。")


def download_audio_from_url(url: str, out_dir: str, max_media_mb: int) -> tuple[str, str]:
    """Downloads audio from a URL — either a direct media file link or a
    yt-dlp-supported platform (YouTube, Vimeo, etc.) — and returns
    (local_audio_path, display_filename). No local ffmpeg is required: the
    format selector only picks formats Whisper accepts directly."""
    _validate_url(url)

    out_template = os.path.join(out_dir, "url_media.%(ext)s")
    ydl_opts = {
        "format": FORMAT_SELECTOR,
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": max_media_mb * 1024 * 1024,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="URLから音声/動画を取得できませんでした。URLが正しいか、非公開になっていないか確認してください。",
        ) from e

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=500, detail="URLからの音声取得に失敗しました。")

    display_name = (info or {}).get("title") or "url_media"
    ext = os.path.splitext(audio_path)[1]
    return audio_path, f"{display_name}{ext}"
