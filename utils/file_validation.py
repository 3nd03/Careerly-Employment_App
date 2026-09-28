from fastapi import HTTPException, status

MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024
PDF_MAGIC_BYTES = b"%PDF"


def validate_pdf(file_bytes: bytes, filename: str) -> None:
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a .pdf file")
    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not a valid PDF")
    if len(file_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be under 5MB")
