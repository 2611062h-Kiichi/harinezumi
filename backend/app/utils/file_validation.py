import os
import tempfile

from fastapi import HTTPException, UploadFile


def validate_upload(file: UploadFile, allowed_exts: set[str], max_mb: int) -> None:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_exts:
        allowed = "/".join(sorted(allowed_exts))
        raise HTTPException(
            status_code=400,
            detail=f"対応していないファイル形式です（対応形式: {allowed}）。",
        )

    size = file.size
    if size is not None and size > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"ファイルサイズが大きすぎます（上限 {max_mb}MB）。",
        )


def save_temp_upload(file: UploadFile, dest_dir: str) -> str:
    ext = os.path.splitext(file.filename or "")[1]
    fd, path = tempfile.mkstemp(suffix=ext, dir=dest_dir)
    with os.fdopen(fd, "wb") as f:
        while chunk := file.file.read(1024 * 1024):
            f.write(chunk)
    return path
