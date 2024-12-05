from .base_parser import BaseParser
import logging
import PyPDF2
import pytesseract
import fitz
from PIL import Image

# Concrete parser for PDF
class PdfParser(BaseParser):
    @staticmethod
    def _verify_tesseract():
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logging.error(f"Tesseract not properly configured: {e}")
            return False

    def __init__(self):
        if not self._verify_tesseract():
            raise RuntimeError("Tesseract OCR is not properly installed")
        # Optionally set tesseract path
        # pytesseract.pytesseract.tesseract_cmd = (
        #     r"C:\Programs\Tesseract-OCR\tesseract.exe"
        # )

    def parse(self, filepath: str) -> str:
        try:
            content = []

            # First try basic PDF text extraction
            with open(filepath, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                if reader.is_encrypted:
                    try:
                        reader.decrypt("")
                    except Exception as e:
                        logging.error(f"Failed to decrypt PDF: {e}")
                        return "Unable to decrypt PDF"

                for page_num in range(len(reader.pages)):
                    try:
                        page = reader.pages[page_num]
                        page_content = page.extract_text()

                        # Clean the extracted text
                        if page_content:
                            page_content = page_content.replace("\x00", "")
                            page_content = " ".join(page_content.split())
                            content.append(page_content)
                    except Exception as e:
                        logging.error(
                            f"Error extracting text from page {page_num}: {e}"
                        )
                        continue

            # If no text was extracted, try OCR
            if not "".join(content).strip():
                logging.info("No text extracted, attempting OCR...")
                doc = fitz.open(filepath)
                for page_num in range(len(doc)):
                    try:
                        ocr_text = self._ocr_page(filepath, page_num)
                        if ocr_text:
                            ocr_text = ocr_text.replace("\x00", "")
                            ocr_text = " ".join(ocr_text.split())
                            content.append(ocr_text)
                    except Exception as e:
                        logging.error(f"Error performing OCR on page {
                                      page_num}: {e}")
                        continue
                doc.close()

            final_content = " ".join(content)
            if not final_content.strip():
                raise ValueError("No text content extracted from PDF")

            return final_content

        except Exception as e:
            logging.error(f"Error processing PDF: {e}")
            return f"Error processing PDF file: {str(e)}"

    def _ocr_page(self, filepath: str, page_num: int) -> str:
        try:
            doc = fitz.open(filepath)
            page = doc[page_num]
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)
            doc.close()
            return text
        except Exception as e:
            logging.error(f"OCR failed for page {page_num}: {e}")
            return ""
