from .base_parser import BaseParser
import logging
import pytesseract
from PIL import Image
from .pdf_parser import PdfParser


class ImageParser(BaseParser):
    def __init__(self):
        if not PdfParser._verify_tesseract():
            raise RuntimeError("Tesseract OCR is not properly installed")

    def parse(self, filepath: str) -> str:
        try:
            # Open and preprocess image
            image = Image.open(filepath)
            preprocessed_image = self._preprocess_image(image)

            # Perform OCR
            text = pytesseract.image_to_string(
                preprocessed_image,
                config="--psm 3 --oem 3",  # Page segmentation + LSTM OCR
            ).strip()

            if not text:
                raise ValueError("No text extracted from image")

            logging.info(f"Successfully extracted text from image: {filepath}")
            return text

        except Exception as e:
            logging.error(f"Error processing image: {e}")
            return f"Error processing image file: {str(e)}"

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        try:
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize if too small
            if image.size[0] < 300 or image.size[1] < 300:
                ratio = 300 / min(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logging.error(f"Error preprocessing image: {e}")
            raise
