from PIL import Image
import os
from toc_llm_parser import parse_toc_multi


def load_toc_images(toc_pages, folder):
    images = []

    for p in toc_pages:
        path = os.path.join(folder, f"page_{int(p):03d}.png")

        if os.path.exists(path):
            images.append(Image.open(path))
        else:
            print(f"⚠️ Missing image: {path}")

    return images


def extract_toc_with_llm(toc_pages, folder):
    """
    Single-call Vision LLM for all TOC pages
    """
    toc_images = load_toc_images(toc_pages, folder)

    if not toc_images:
        return [], 0.0

    print("\n🚀 Running LLM on all TOC pages (single call)...")

    result = parse_toc_multi(toc_images)

    entries = result.get("entries", [])
    confidence = result.get("confidence", 0)

    return entries, confidence

