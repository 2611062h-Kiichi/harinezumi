import base64
import io
import logging

import av

logger = logging.getLogger(__name__)

VIDEO_EXTS = {".mp4", ".webm"}
NUM_FRAMES = 4
JPEG_QUALITY = 70


def is_video_file(filename: str) -> bool:
    import os

    return os.path.splitext(filename)[1].lower() in VIDEO_EXTS


def extract_frames_base64(video_path: str, num_frames: int = NUM_FRAMES) -> list[str]:
    """Extracts `num_frames` JPEG frames evenly spaced through the video's
    duration using PyAV (no system ffmpeg binary required — safe on
    serverless). Returns base64-encoded JPEG strings, or an empty list if the
    file has no video stream (e.g. it's actually audio-only) or extraction
    otherwise fails — callers should treat that as "no visual signal
    available" rather than an error."""
    try:
        container = av.open(video_path)
        if not container.streams.video:
            return []
        stream = container.streams.video[0]
        if not stream.duration:
            return []
        duration = float(stream.duration * stream.time_base)

        images: list[str] = []
        for i in range(num_frames):
            target_sec = duration * (i + 1) / (num_frames + 1)
            container.seek(int(target_sec / stream.time_base), stream=stream)
            for frame in container.decode(stream):
                buf = io.BytesIO()
                frame.to_image().convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY)
                images.append(base64.standard_b64encode(buf.getvalue()).decode("utf-8"))
                break
        return images
    except Exception:
        logger.warning("Video frame extraction failed; continuing without visual analysis", exc_info=True)
        return []
