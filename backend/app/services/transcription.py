import os

from fastapi import HTTPException
from openai import AsyncOpenAI

from app.config import get_settings
from app.models.schemas import TranscriptionResult

WHISPER_MAX_BYTES = 25 * 1024 * 1024


async def transcribe(audio_path: str, filename: str) -> TranscriptionResult:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEYが設定されていません。")

    size = os.path.getsize(audio_path)
    if size > WHISPER_MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail="音声/動画ファイルが大きすぎます。25MB相当以下になるよう録音を短くしてください。",
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    with open(audio_path, "rb") as f:
        transcript = await client.audio.transcriptions.create(
            model=settings.whisper_model,
            file=f,
        )
    return TranscriptionResult(filename=filename, text=transcript.text)
