import os
import shutil
import argparse
import json

from pdf_to_images import pdf_to_images
from preprocess import preprocess_all
from ocr_engine import ocr_all_pages

from toc_detector import detect_toc_pages, extract_toc_text
from toc_llm_integration import extract_toc_with_llm
from toc_parser import parse_toc, add_page_ranges, build_hierarchy


# -------------------------------
# Utils
# -------------------------------

def reset_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def setup_book_folder(pdf_path):
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    base = os.path.join("books", book_name)

    os.makedirs(base, exist_ok=True)

    return {
        "base": base,
        "pdf": pdf_path,
        "pages_raw": os.path.join(base, "pages_raw"),
        "pages_clean": os.path.join(base, "pages_clean"),
        "ocr_output": os.path.join(base, "ocr_output"),
        "toc_raw": os.path.join(base, "toc_raw.txt"),
        "toc_json": os.path.join(base, "toc_parsed.json"),
    }


# -------------------------------
# Pipeline
# -------------------------------

def run_pipeline(pdf_path):
    paths = setup_book_folder(pdf_path)

    print(f"\n📘 Processing book: {pdf_path}")

    # 1. Reset folders (prevents stale data bug)
    reset_folder(paths["pages_raw"])
    reset_folder(paths["pages_clean"])
    reset_folder(paths["ocr_output"])

    # 2. PDF → images
    print("\n📄 Converting PDF to images...")
    pdf_to_images(pdf_path, paths["pages_raw"], max_pages=20)

    # 3. Clean images
    print("\n🧹 Cleaning images...")
    preprocess_all(paths["pages_raw"], paths["pages_clean"])

    # 4. OCR
    print("\n🔍 Running OCR...")
    ocr_results = ocr_all_pages(paths["pages_clean"], paths["ocr_output"])

    # 5. Detect TOC
    toc_pages = detect_toc_pages(ocr_results, score_threshold=40, skip_pages=1)

    if not toc_pages:
        print("❌ No TOC pages found")
        return

    # 6. LLM (single call)
    print("\n🚀 Running Vision LLM...")
    entries, conf = extract_toc_with_llm(toc_pages, paths["pages_clean"])

    print(f"\nLLM confidence: {conf:.2f}")

    # 7. Fallback
    # 7. Decide source
    if conf >= 0.7 and entries:
        print("✅ Using LLM hierarchy directly")
        hierarchy = entries
    else:
        print("\n⚠️ Falling back to OCR parser")

        toc_text = extract_toc_text(ocr_results, toc_pages)

        with open(paths["toc_raw"], "w", encoding="utf-8") as f:
            f.write(toc_text)

        entries = parse_toc(toc_text)
        hierarchy = build_hierarchy(entries)


    with open(paths["toc_json"], "w", encoding="utf-8") as f:
        json.dump(hierarchy, f, indent=2, ensure_ascii=False)

    print("\n✅ Done! TOC saved at:")
    print(paths["toc_json"])


# -------------------------------
# CLI
# -------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to PDF file")

    args = parser.parse_args()

    run_pipeline(args.pdf)