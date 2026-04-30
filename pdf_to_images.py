import fitz  # pymupdf
import os
from PIL import Image

def pdf_to_images(pdf_path, output_folder="pages", dpi=300):
    """
    Converts every page of a PDF into a PNG image.
    Works for both scanned and digital PDFs.
    
    Args:
        pdf_path     : path to your PDF file
        output_folder: folder where page images will be saved
        dpi          : resolution (300 is ideal for OCR)
    
    Returns:
        list of saved image paths in order
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(pdf_path)
    saved_paths = []

    print(f"PDF loaded — {len(doc)} pages found")

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Convert page to image at given DPI
        # 72 is PyMuPDF default DPI, so we scale up from that
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)

        # Save as PNG
        img_path = os.path.join(output_folder, f"page_{page_num + 1:03d}.png")
        pix.save(img_path)
        saved_paths.append(img_path)

        print(f"  Saved page {page_num + 1}/{len(doc)} → {img_path}")

    doc.close()
    print(f"\nDone — {len(saved_paths)} images saved to '{output_folder}/'")
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
    image_paths = pdf_to_images(PDF_FILE, output_folder="pages", dpi=300)

    print(f"\nFirst image saved at: {image_paths[0]}")
    print("Open the 'pages' folder to visually check quality.")