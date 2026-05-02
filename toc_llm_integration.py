from PIL import Image
import os
from toc_llm_parser import parse_toc_multi


def load_toc_images(toc_pages, folder="pages_clean"):
    images = []

    for p in toc_pages:
        path = os.path.join(folder, f"page_{int(p):03d}.png")

        if os.path.exists(path):
            images.append(Image.open(path))
        else:
            print(f"⚠️ Missing image: {path}")

    return images


def extract_toc_with_llm(images):
    """
    Takes list of PIL images and runs ONE LLM call
    """
    print("\n🚀 Running LLM on all TOC pages (single call)...")

    try:
        result = parse_toc_multi(images)

        entries = result.get("entries", [])
        confidence = result.get("confidence", 0)

        return {
            "entries": entries,
            "confidence": confidence
        }

    except Exception as e:
        print(f"❌ LLM error: {e}")

        return {
            "entries": [],
            "confidence": 0
        }