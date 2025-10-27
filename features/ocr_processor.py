
import pytesseract
from PIL import Image
import io
import base64

try:
    import google.generativeai as genai
except ImportError:
    genai = None

class OCRProcessor:
    def __init__(self):
        self.genai = genai
    
    def extract_text(self, file) -> str:
        """Extract text using Tesseract OCR (fallback method)"""
        try:
            if hasattr(file, "read"):
                img = Image.open(file)
            else:
                img = Image.open(io.BytesIO(file))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception:
            return ""
    
    def parse_receipt_with_gemini(self, file, api_key: str) -> dict:
        """
        Parse receipt image using Gemini Vision API and extract expense details.
        Returns a dictionary with amount, category, note, date, currency.
        """
        if self.genai is None:
            return None
        
        try:
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Read file to bytes
            if hasattr(file, "read"):
                # Reset file pointer to beginning if already read
                file.seek(0)
                file_bytes = file.read()
            else:
                file_bytes = file
            
            # Prepare image for Gemini
            from PIL import Image as PILImage
            from io import BytesIO
            
            if hasattr(file, "read"):
                file.seek(0)
                img = PILImage.open(file)
            else:
                img = PILImage.open(BytesIO(file_bytes))
            
            # Create prompt for Gemini Vision
            prompt = """
Analyze this receipt image and extract expense information.
Return a JSON object with the following structure:
{
    "amount": <numeric value>,
    "category": "<Food/Transport/Rent/Utilities/Entertainment/Other>",
    "note": "<description from receipt>",
    "date": "<YYYY-MM-DD format>",
    "currency": "<currency code like USD, INR, etc>"
}

Rules:
- Use today's date (YYYY-MM-DD) if date not found on receipt
- Default currency to USD if not specified
- Match category to: Food, Transport, Rent, Utilities, Entertainment, or Other
- Be precise with amount extraction
Return ONLY valid JSON, no additional text.
"""
            
            # Use Gemini Vision model
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Generate response with image
            response = model.generate_content([prompt, img])
            
            # Parse JSON from response
            import json
            import re
            
            text = response.text.strip()
            
            # Try to extract JSON from markdown code blocks first
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if not json_match:
                # Try without markdown
                json_match = re.search(r'\{.*?\}', text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1) if json_match.lastindex else json_match.group(0)
                data = json.loads(json_str)
                
                # Validate and set defaults
                if "amount" not in data or not isinstance(data["amount"], (int, float)):
                    return None
                if "category" not in data:
                    data["category"] = "Other"
                if "date" not in data:
                    from datetime import datetime
                    data["date"] = datetime.now().strftime("%Y-%m-%d")
                if "currency" not in data:
                    data["currency"] = "USD"
                if "note" not in data:
                    data["note"] = "Receipt"
                
                return data
            else:
                # Fallback: return None if parsing fails
                return None
                
        except Exception as e:
            print(f"Gemini Vision error: {e}")
            return None
