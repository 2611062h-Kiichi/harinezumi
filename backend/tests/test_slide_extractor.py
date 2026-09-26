import pytest
from fastapi import HTTPException
from pptx import Presentation

from app.services.slide_extractor import extract_slides


def make_pptx(path, slides):
    presentation = Presentation()
    layout = presentation.slide_layouts[1]  # title + content
    for title, body, notes in slides:
        slide = presentation.slides.add_slide(layout)
        slide.shapes.title.text = title
        slide.placeholders[1].text = body
        if notes:
            slide.notes_slide.notes_text_frame.text = notes
    presentation.save(path)


def test_extracts_text_and_notes_from_pptx(tmp_path):
    path = tmp_path / "pitch.pptx"
    make_pptx(
        path,
        [
            ("課題", "学生の8割が就活情報に困っている", "ここで間を取る"),
            ("解決策", "AIが企業情報を要約する", ""),
        ],
    )

    result = extract_slides(str(path), "pitch.pptx")

    assert result.filename == "pitch.pptx"
    assert [s.index for s in result.slides] == [1, 2]
    assert "課題" in result.slides[0].text
    assert "学生の8割が就活情報に困っている" in result.slides[0].text
    assert result.slides[0].notes == "ここで間を取る"
    assert "AIが企業情報を要約する" in result.slides[1].text
    assert result.slides[1].notes == ""


def test_unsupported_extension_is_rejected(tmp_path):
    path = tmp_path / "pitch.key"
    path.write_bytes(b"not a slide deck")

    with pytest.raises(HTTPException) as excinfo:
        extract_slides(str(path), "pitch.key")

    assert excinfo.value.status_code == 400
