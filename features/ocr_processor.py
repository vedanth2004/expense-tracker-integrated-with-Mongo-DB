import pytesseract
from PIL import Image
import io

class OCRProcessor:
    def extract_text(self, file) -> str:
        try:
            if hasattr(file, "read"):
                img = Image.open(file)
            else:
                img = Image.open(io.BytesIO(file))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception:
            return ""
