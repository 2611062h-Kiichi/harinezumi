import os

import pdfplumber
from fastapi import HTTPException
from pptx import Presentation
from pptx.shapes.group import GroupShape

from app.models.schemas import SlideContent, SlideExtractionResult


def extract_from_pdf(path: str, filename: str) -> SlideExtractionResult:
    slides: list[SlideContent] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            slides.append(SlideContent(index=i + 1, text=text.strip()))
    return SlideExtractionResult(filename=filename, slides=slides)


def _shape_texts(shapes) -> list[str]:
    """Text of each shape in order, looking inside groups (recursively) and tables."""
    texts: list[str] = []
    for shape in shapes:
        # isinstance, not shape.shape_type: python-pptx raises NotImplementedError
        # from shape_type for valid shapes that have no geometry element.
        if isinstance(shape, GroupShape):
            texts.extend(_shape_texts(shape.shapes))
        elif shape.has_table:
            for row in shape.table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                line = " | ".join(c for c in cells if c)
                if line:
                    texts.append(line)
        elif shape.has_text_frame and shape.text_frame.text.strip():
            texts.append(shape.text_frame.text.strip())
    return texts


def extract_from_pptx(path: str, filename: str) -> SlideExtractionResult:
    presentation = Presentation(path)
    slides: list[SlideContent] = []
    for i, slide in enumerate(presentation.slides):
        texts = _shape_texts(slide.shapes)
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        slides.append(SlideContent(index=i + 1, text="\n".join(texts), notes=notes))
    return SlideExtractionResult(filename=filename, slides=slides)


def extract_slides(path: str, filename: str) -> SlideExtractionResult:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return extract_from_pdf(path, filename)
    if ext == ".pptx":
        return extract_from_pptx(path, filename)
    raise HTTPException(status_code=400, detail="対応していないスライド形式です（.pdf / .pptx のみ）。")
