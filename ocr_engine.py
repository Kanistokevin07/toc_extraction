import pytesseract
import easyocr
import cv2
import os
import json

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize EasyOCR once (expensive to reload each time)
easy_reader = easyocr.Reader(['en'], verbose=False)


def ocr_tesseract(image_path):
    """
    Extract text from a single image using Tesseract.
    Fast, good for clean scans.
    """
    image = cv2.imread(image_path)
    if image is None:
        return ""

    # PSM 6 = assume single uniform block of text (good for book pages)
    config = "--psm 6 --oem 3"
    text = pytesseract.image_to_string(image, config=config)
    return text.strip()


def ocr_easyocr(image_path):
    """
    Extract text using EasyOCR.
    Slower but better on noisy/curved scans.
    """
    results = easy_reader.readtext(image_path, detail=0, paragraph=True)
    return "\n".join(results).strip()


def ocr_page(image_path, engine="tesseract"):
    """
    OCR a single page image.

    Args:
        image_path : path to preprocessed page image
        engine     : 'tesseract' or 'easyocr'

    Returns:
        extracted text as string
    """
    if not os.path.exists(image_path):
        print(f"  ERROR: {image_path} not found")
        return ""

    if engine == "tesseract":
        return ocr_tesseract(image_path)
    elif engine == "easyocr":
        return ocr_easyocr(image_path)
    else:
        raise ValueError(f"Unknown engine: {engine}. Use 'tesseract' or 'easyocr'.")


def ocr_all_pages(input_folder="pages_clean", output_folder="ocr_output", engine="tesseract", max_pages=None):
    """
    Runs OCR on every preprocessed page image and saves text files.

    Args:
        input_folder : folder with clean page images (from Module 2)
        output_folder: folder to save per-page text files
        engine       : 'tesseract' or 'easyocr'

    Returns:
        dict of { page_number: text }
    """
    os.makedirs(output_folder, exist_ok=True)

    image_files = sorted([
        f for f in os.listdir(input_folder)
        if f.endswith(".png")
    ])

    # Limit to first N pages if specified
    if max_pages:
        image_files = image_files[:max_pages]

    if not image_files:
        print(f"No images found in '{input_folder}/'")
        return {}

    print(f"Running OCR on {len(image_files)} pages using {engine}...\n")

    results = {}

    for idx, filename in enumerate(image_files):
        image_path = os.path.join(input_folder, filename)
        page_num = idx + 1

        print(f"  Page {page_num}/{len(image_files)} — {filename}")

        text = ocr_page(image_path, engine=engine)

        # Save individual text file per page
        txt_path = os.path.join(output_folder, f"page_{page_num:03d}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        results[page_num] = text

    # Also save everything as one combined JSON
    json_path = os.path.join(output_folder, "all_pages.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone — OCR text saved to '{output_folder}/'")
    print(f"Combined JSON: {json_path}")

    return results


# --- Test it ---
if __name__ == "__main__":
    results = ocr_all_pages(
        input_folder="pages_clean",
        output_folder="ocr_output",
        engine="tesseract",
        max_pages=389
    )