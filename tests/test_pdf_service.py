import io
import shutil

import pytest
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas

from app.services.pdf_service import PdfExtractionError, extract_text_from_pdf

OCR_AVAILABLE = shutil.which("tesseract") is not None and shutil.which("pdftoppm") is not None
requires_ocr = pytest.mark.skipif(
    not OCR_AVAILABLE, reason="tesseract and poppler-utils are required for OCR tests"
)


def _text_pdf(pages: list[str]) -> bytes:
    """Matn qatlami bor PDF yaratadi."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    for text in pages:
        pdf.setFont("Helvetica", 14)
        pdf.drawString(72, 750, text)
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _scanned_pdf(text: str) -> bytes:
    """Faqat rasmdan iborat (matn qatlamisiz) PDF - skaner qilingan hujjatni taqlid qiladi."""
    image = Image.new("RGB", (1240, 400), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
    draw.text((40, 150), text, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PDF", resolution=150)
    return buffer.getvalue()


def test_text_pdf_is_read_without_ocr():
    pdf = _text_pdf(["Refund policy allows returns within thirty days.", "Shipping takes five business days."])
    result = extract_text_from_pdf(pdf)

    assert result.total_pages == 2
    assert result.ocr_pages == []
    assert "Refund policy" in result.text
    assert "Shipping takes five" in result.text


@requires_ocr
def test_scanned_pdf_falls_back_to_ocr():
    pdf = _scanned_pdf("Invoice total amount due is 450 dollars")
    result = extract_text_from_pdf(pdf)

    assert result.ocr_pages == [1]
    assert "Invoice" in result.text
    assert "450" in result.text


@requires_ocr
def test_mixed_pdf_only_ocrs_scanned_pages():
    """Aralash hujjat: 1-sahifa matnli, 2-sahifa skaner - OCR faqat 2-sahifaga ishlashi kerak."""
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    writer.add_page(PdfReader(io.BytesIO(_text_pdf(["Cover page with a long enough title text"]))).pages[0])
    writer.add_page(PdfReader(io.BytesIO(_scanned_pdf("Scanned appendix with signature"))).pages[0])
    buffer = io.BytesIO()
    writer.write(buffer)

    result = extract_text_from_pdf(buffer.getvalue())

    assert result.total_pages == 2
    assert result.ocr_pages == [2]
    assert "Cover page" in result.text
    assert "appendix" in result.text.lower()


def test_garbage_bytes_raise_extraction_error():
    with pytest.raises(PdfExtractionError):
        extract_text_from_pdf(b"%PDF-1.4 this is not really a pdf")


def test_too_many_pages_rejected(monkeypatch):
    monkeypatch.setattr("app.services.pdf_service.MAX_PAGES", 1)
    pdf = _text_pdf(["Page one has enough text here.", "Page two has enough text here."])
    with pytest.raises(PdfExtractionError, match="too many pages"):
        extract_text_from_pdf(pdf)
