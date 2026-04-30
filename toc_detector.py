import re
import json
import os


def score_page_as_toc(text):
    """
    Gives a score to a page based on how likely it is a TOC page.
    Higher score = more likely to be TOC.
    """
    score = 0
    reasons = []

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if not lines:
        return 0, []

    # Signal 1: dot leaders or spaced dots
    dot_lines = sum(1 for l in lines if re.search(r'\.{2,}', l))
    if dot_lines >= 3:
        score += 30
        reasons.append(f"dot leaders on {dot_lines} lines")

    # Signal 2: lines ending in a number (page numbers)
    page_num_lines = sum(1 for l in lines if re.search(r'\b\d{1,3}\s*[.,]?\s*$', l))
    if page_num_lines >= 5:
        score += 30
        reasons.append(f"{page_num_lines} lines ending in page number")

    # Signal 3: numbered section headings like 1.2 or 3.4.5
    section_lines = sum(1 for l in lines if re.match(r'^\d+\.\d+', l))
    if section_lines >= 3:
        score += 25
        reasons.append(f"{section_lines} numbered section lines")

    # Signal 4: keyword match
    full_text_lower = text.lower()
    keywords = ["table of contents", "contents", "detailed contents"]
    for kw in keywords:
        if kw in full_text_lower:
            score += 20
            reasons.append(f"keyword '{kw}' found")
            break

    # Signal 5: chapter headings
    chapter_lines = sum(1 for l in lines if re.match(r'^(chapter|\d+\.)\s', l, re.IGNORECASE))
    if chapter_lines >= 2:
        score += 15
        reasons.append(f"{chapter_lines} chapter heading lines")

    # Signal 6: penalize if page looks like body text
    # Body text has long sentences, TOC lines are short
    avg_line_len = sum(len(l) for l in lines) / len(lines)
    if avg_line_len > 80:
        score -= 20
        reasons.append("long lines (likely body text)")

    # Signal 7: noise lines like URLs, scanner watermarks
    noise_lines = sum(1 for l in lines if
        "camscanner" in l.lower() or
        "http" in l.lower() or
        "scanned by" in l.lower()
    )
    if noise_lines > 0:
        score -= 5 * noise_lines
        reasons.append(f"{noise_lines} noise lines detected")

    return score, reasons


def detect_toc_pages(ocr_results, score_threshold=40, skip_pages=1):
    """
    Scans all OCR'd pages and identifies which ones are TOC pages.

    Args:
        ocr_results     : dict of { page_number: text } from Module 3
        score_threshold : minimum score to consider a page as TOC
        skip_pages      : ignore first N pages (cover, copyright)

    Returns:
        list of page numbers identified as TOC pages
    """
    print(f"Scanning {len(ocr_results)} pages for TOC...\n")

    page_scores = {}

    for page_num, text in ocr_results.items():
        # Skip cover and copyright pages
        if int(page_num) <= skip_pages:
            print(f"  Page {page_num}: SKIPPED (cover/copyright)")
            continue

        score, reasons = score_page_as_toc(text)
        page_scores[page_num] = score

        if score >= score_threshold:
            print(f"  Page {page_num}: SCORE {score} ✓ TOC  — {', '.join(reasons)}")
        else:
            print(f"  Page {page_num}: SCORE {score}   not TOC")

    # Get pages above threshold
    toc_pages = [
        p for p, s in page_scores.items()
        if s >= score_threshold
    ]

    # TOC pages should be consecutive — filter out isolated high-scoring pages
    # that might be index pages at the back of the book
    if toc_pages:
        toc_pages = filter_consecutive(toc_pages)

    print(f"\nTOC pages detected: {toc_pages}")
    return toc_pages


def filter_consecutive(page_list):
    """
    Keeps only the first cluster of consecutive (or near-consecutive) pages.
    Removes false positives like index pages at the end of the book.
    """
    if not page_list:
        return []

    page_list = sorted([int(p) for p in page_list])
    first_cluster = [page_list[0]]

    for i in range(1, len(page_list)):
        # Allow gap of up to 2 pages (in case one TOC page scored low)
        if page_list[i] - page_list[i - 1] <= 2:
            first_cluster.append(page_list[i])
        else:
            break  # gap too large, stop — this is a new section

    return [str(p) for p in first_cluster]


def extract_toc_text(ocr_results, toc_pages):
    """
    Combines text from all detected TOC pages into one clean string.

    Args:
        ocr_results : dict of { page_number: text }
        toc_pages   : list of page numbers that are TOC

    Returns:
        combined TOC text as a single string
    """
    combined = []

    for page_num in toc_pages:
        text = ocr_results.get(page_num, "")

        # Remove noise lines
        clean_lines = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if any(noise in line.lower() for noise in [
                "camscanner", "scanned by", "http", "www.", ".com", ".github"
            ]):
                continue
            clean_lines.append(line)

        combined.append("\n".join(clean_lines))

    return "\n".join(combined)


# --- Test it ---
if __name__ == "__main__":
    # Load OCR results from Module 3
    json_path = "ocr_output/all_pages.json"

    if not os.path.exists(json_path):
        print(f"ERROR: {json_path} not found.")
        print("Run ocr_engine.py on full book first.")
        exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        ocr_results = json.load(f)

    # Detect TOC pages
    toc_pages = detect_toc_pages(ocr_results, score_threshold=40, skip_pages=1)

    if not toc_pages:
        print("\nNo TOC pages found. Try lowering score_threshold.")
    else:
        # Extract combined TOC text
        toc_text = extract_toc_text(ocr_results, toc_pages)

        # Save for next module
        with open("toc_raw.txt", "w", encoding="utf-8") as f:
            f.write(toc_text)

        print(f"\nTOC text saved to toc_raw.txt")
        print(f"\n--- Preview ---\n")
        print(toc_text[:500])