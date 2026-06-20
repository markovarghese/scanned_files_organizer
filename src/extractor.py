import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pytesseract import Output

class Extractor:
    def __init__(self):
        pass

    def _auto_rotate_image(self, img):
        try:
            osd = pytesseract.image_to_osd(img, output_type=Output.DICT)
            angle = osd.get('rotate', 0)
            if angle != 0:
                return img.rotate(-angle, expand=True)
        except Exception:
            # OSD might fail if there's no text (e.g. pure photos), safely ignore
            pass
        return img

    def extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from the first two pages of a PDF document.
        """
        try:
            # Convert up to the first 2 pages
            images = convert_from_path(file_path, first_page=1, last_page=2)
            extracted_text = ""
            for img in images:
                img = self._auto_rotate_image(img)
                text = pytesseract.image_to_string(img)
                extracted_text += text + "\n"
            return extracted_text.strip()
        except Exception as e:
            print(f"[Extractor] Error reading PDF {file_path}: {e}")
            return ""

    def extract_from_image(self, file_path: str) -> str:
        """
        Extract text from an image.
        Returns the text, which could be empty/sparse if it's a photograph.
        """
        try:
            img = Image.open(file_path)
            img = self._auto_rotate_image(img)
            # Basic OCR
            extracted_text = pytesseract.image_to_string(img)
            return extracted_text.strip()
        except Exception as e:
            print(f"[Extractor] Error reading Image {file_path}: {e}")
            return ""

    def extract_text(self, file_path: str) -> str:
        """
        Convenience route handling.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return self.extract_from_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png']:
            return self.extract_from_image(file_path)
        return ""
