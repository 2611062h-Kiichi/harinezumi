import os
import subprocess

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


def is_video_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in VIDEO_EXTS


def extract_audio(input_path: str, out_dir: str) -> str:
    out_path = os.path.join(out_dir, "extracted_audio.mp3")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
                out_path,
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "ffmpegが見つかりません。ffmpegをインストールし、PATHに追加してください。"
        ) from e
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
        raise RuntimeError(f"音声の抽出に失敗しました: {stderr[-500:]}") from e
    return out_path
