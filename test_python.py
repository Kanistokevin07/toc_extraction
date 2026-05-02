"""import fitz          # pymupdf
import pdfplumber
import cv2
import pytesseract
from PIL import Image
import easyocr

# Tell pytesseract where tesseract.exe is
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

print("✓ PyMuPDF     :", fitz.__version__)
print("✓ pdfplumber  : ok")
print("✓ OpenCV      :", cv2.__version__)
print("✓ Pillow      : ok")

# Quick Tesseract check
version = pytesseract.get_tesseract_version()
print("✓ Tesseract   :", version)

# EasyOCR init (downloads model on first run ~100MB, normal)
reader = easyocr.Reader(['en'], verbose=False)
print("✓ EasyOCR     : ok")

print("\nAll good — ready to build!")"""


from google import genai

client = genai.Client(api_key="AIzaSyBn31hjX73-4GmUR-Fst-UgaMBldalujCM")

models = client.models.list()

for m in models:
    print(m.name)