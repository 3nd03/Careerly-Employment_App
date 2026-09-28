import pytest
from fastapi import HTTPException

from utils.file_validation import validate_pdf

VALID_PDF_BYTES = b"%PDF-1.4\n%mock pdf content"


def test_valid_pdf_passes():
    validate_pdf(VALID_PDF_BYTES, "cv.pdf")


def test_rejects_wrong_extension():
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf(VALID_PDF_BYTES, "cv.docx")
    assert exc_info.value.status_code == 400


def test_rejects_wrong_magic_bytes():
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf(b"not a real pdf", "cv.pdf")
    assert exc_info.value.status_code == 400


def test_rejects_oversized_file():
    oversized = b"%PDF-1.4" + b"0" * (5 * 1024 * 1024 + 1)
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf(oversized, "cv.pdf")
    assert exc_info.value.status_code == 400
