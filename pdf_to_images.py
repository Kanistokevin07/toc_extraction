import fitz  # pymupdf
import os
from PIL import Image

def pdf_to_images(pdf_path, output_folder, dpi=300, max_pages=None):
    import os
    import fitz

    output_folder = os.path.abspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(pdf_path)
    saved_paths = []

    total_pages = len(doc)
    limit = min(max_pages, total_pages) if max_pages else total_pages

    print(f"PDF loaded — {total_pages} pages found")
    print(f"Processing first {limit} pages")

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page_num in range(limit):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=matrix)

        img_path = os.path.join(output_folder, f"page_{page_num + 1:03d}.png")
        pix.save(img_path)

        saved_paths.append(img_path)
        print(f"  Saved page {page_num + 1}/{limit} → {img_path}")

    doc.close()

    print(f"\nDone — {len(saved_paths)} images saved")
    return saved_paths
    
def get_pdf_info(pdf_path):
    """
    Quick inspection of a PDF before processing.
    Tells you if it's scanned or digital.
    """
    doc = fitz.open(pdf_path)
    
    print(f"\n--- PDF Info: {os.path.basename(pdf_path)} ---")
    print(f"Total pages : {len(doc)}")
    
    # Check first 5 pages for text
    text_pages = 0
    for i in range(min(5, len(doc))):
        text = doc[i].get_text().strip()
        if len(text) > 50:
            text_pages += 1

    if text_pages >= 3:
        print(f"Type        : Digital PDF (has embedded text)")
        print(f"OCR needed  : No — can extract text directly")
    else:
        print(f"Type        : Scanned PDF (image-based)")
        print(f"OCR needed  : Yes — must run OCR on page images")

    # Show metadata if available
    meta = doc.metadata
    if meta.get("title"):
        print(f"Title       : {meta['title']}")
    if meta.get("author"):
        print(f"Author      : {meta['author']}")

    doc.close()


# --- Test it ---
if __name__ == "__main__":
    import sys

    # Put your PDF filename here
    PDF_FILE = "test_book_dsa.pdf"

    if not os.path.exists(PDF_FILE):
        print(f"ERROR: '{PDF_FILE}' not found in current folder.")
        print("Place a PDF in your project folder and update PDF_FILE variable.")
        sys.exit(1)

    # Step 1: inspect the PDF
    get_pdf_info(PDF_FILE)

    # Step 2: convert to images
    image_paths = pdf_to_images(PDF_FILE, dpi=300)

    print(f"\nFirst image saved at: {image_paths[0]}")
    print("Open the 'pages' folder to visually check quality.")