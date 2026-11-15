import io
import logging
from dataclasses import dataclass

from pypdf import PdfReader

logger = logging.getLogger(__name__)

# Sahifada shu miqdordan kam belgi bo'lsa, u skanerlangan (rasm) sahifa deb
# hisoblanadi va OCR ishlatiladi.
MIN_TEXT_CHARS_PER_PAGE = 20

# Juda katta PDF'lar worker/API'ni bloklab qo'ymasligi uchun cheklov.
MAX_PAGES = 100

# OCR uchun sahifa rasmining sifati (DPI). 200 - tezlik va aniqlik o'rtasida yaxshi kelishuv.
OCR_DPI = 200


class PdfExtractionError(Exception):
    """PDF'ni o'qib bo'lmaganda (buzilgan fayl, parol bilan himoyalangan va h.k.)"""


@dataclass
class PdfExtractionResult:
    text: str
    total_pages: int
    ocr_pages: list[int]  # OCR ishlatilgan sahifalar raqami (1 dan boshlanadi)


def _ocr_page(pdf_bytes: bytes, page_number: int, lang: str) -> str:
    """Bitta sahifani rasmga aylantirib, Tesseract orqali matnga o'giradi."""
    # Import shu yerda: OCR kutubxonalari faqat kerak bo'lganda yuklanadi
    # (matnli PDF'lar uchun Tesseract o'rnatilgan bo'lishi shart emas).
    import pytesseract
    from pdf2image import convert_from_bytes

    images = convert_from_bytes(
        pdf_bytes, dpi=OCR_DPI, first_page=page_number, last_page=page_number
    )
    if not images:
        return ""
    return pytesseract.image_to_string(images[0], lang=lang)


def extract_text_from_pdf(pdf_bytes: bytes, ocr_lang: str = "eng") -> PdfExtractionResult:
    """
    PDF'dan matn ajratadi. Avval har bir sahifaning matn qatlamidan o'qiydi
    (tez va aniq). Agar sahifada deyarli matn bo'lmasa (skaner qilingan
    hujjat), faqat shu sahifa uchun OCR ishga tushadi.

    ocr_lang - Tesseract til kodi, bir nechta til uchun "eng+rus" kabi.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if reader.is_encrypted:
            raise PdfExtractionError("Password-protected PDFs are not supported.")
        total_pages = len(reader.pages)
    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfExtractionError("Could not read the PDF file.") from exc

    if total_pages > MAX_PAGES:
        raise PdfExtractionError(f"PDF has too many pages (max {MAX_PAGES}).")

    page_texts: list[str] = []
    ocr_pages: list[int] = []

    for index, page in enumerate(reader.pages):
        page_number = index + 1
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            logger.warning("Text extraction failed on page %d, trying OCR", page_number)
            text = ""

        if len(text) < MIN_TEXT_CHARS_PER_PAGE:
            try:
                ocr_text = _ocr_page(pdf_bytes, page_number, ocr_lang).strip()
            except Exception:
                # OCR o'rnatilmagan yoki sahifa rasmga aylanmadi - qolgan sahifalar baribir ishlansin
                logger.warning("OCR failed on page %d", page_number, exc_info=True)
                ocr_text = ""
            if len(ocr_text) > len(text):
                text = ocr_text
                ocr_pages.append(page_number)

        if text:
            page_texts.append(text)

    return PdfExtractionResult(
        text="\n\n".join(page_texts),
        total_pages=total_pages,
        ocr_pages=ocr_pages,
    )
