import os
from pypdf import PdfReader
from fpdf import FPDF
from fpdf.enums import XPos, YPos

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")

LANGUAGE_FONTS = {
    "Mandarin": os.path.join(FONTS_DIR, "NotoSansSC-Regular.otf"),
    "Arabic": os.path.join(FONTS_DIR, "NotoSansArabic-Regular.ttf"),
}


def extract_pdf_text(pdf_file) -> str:
    reader = PdfReader(pdf_file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def generate_pdf(text: str, language: str = "") -> bytes:
    pdf = FPDF()
    pdf.add_page()

    font_path = LANGUAGE_FONTS.get(language)
    if font_path:
        pdf.add_font("Body", "", font_path)
        pdf.set_font("Body", size=11)
    else:
        pdf.set_font("Helvetica", size=11)

    for line in text.split("\n"):
        if line.strip():
            pdf.multi_cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.ln(6)

    return bytes(pdf.output())
