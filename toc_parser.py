import re
import json
import os


# ─────────────────────────────────────────────
# STEP 1 — Clean raw OCR text
# ─────────────────────────────────────────────

def fix_page_number(m):
    """
    Called by clean_ocr_text() to normalize page numbers at end of line.
    Replaces all 1-lookalikes and 0-lookalikes with correct digits.
    Strips anything non-numeric that remains.
    """
    page = m.group(0).strip()
    page = re.sub(r'[lIJ/\\|!]', '1', page)  # 1-lookalikes → 1
    page = re.sub(r'[oO]', '0', page)          # 0-lookalikes → 0
    page = re.sub(r'\]', '1', page)            # ] explicitly → 1
    page = re.sub(r'[^\d]', '', page)          # strip anything remaining
    return ' ' + page if page else ''

def clean_ocr_text(text):
    """
    Universal OCR cleaner — works for any book.
    No hardcoded patterns. Uses positional and contextual rules only.
    
    Core principle:
        We don't know WHICH character was misread.
        We DO know WHAT a valid TOC line looks like.
        So we fix based on position/context, not specific characters.
    """

    # Characters that visually resemble 1 in scanned fonts
    ONE_LIKE  = r'[1lIJ/\\\|!]'
    
    # Characters that visually resemble 0 in scanned fonts
    ZERO_LIKE = r'[0oO]'

    lines = text.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # ── STEP 1: Remove noise lines ────────────────────────────────
        # These are structural noise present in ANY scanned book
        # We detect by pattern, not by specific content
        noise_patterns = [
            r'^[^a-zA-Z0-9]{3,}$',      # line has only symbols — garbage
            r'^[a-zA-Z0-9]{1,2}$',      # single/double char lines — garbage
            r'^[ivxlcdmIVXLCDM\s]+$',   # only roman numerals — page header
            r'scanned\s*by',             # scanner watermark — any scanner
            r'https?://',               # URLs — any URL
            r'www\.',                   # URLs without http
            r'camscanner|scanbot|adobe\s*scan',  # known scanner apps
            r'^[,/\\;><~\s]+$',          # lines that are only punctuation/slashes
            r'^(LLL|lll|III|iii)',        # repeated character garbage
            r'^\W+$',                     # no alphanumeric at all
        ]
        if any(re.search(p, line, re.IGNORECASE) for p in noise_patterns):
            continue

        # ── STEP 2: Strip stray prefix characters ────────────────────
        # Any non-alphanumeric character at line start before a digit
        # is a scanning artifact — strip it universally
        # e.g. "> 1.4 Title", "| 2.3 Title", "= 3.1 Title"
        line = re.sub(r'^[^a-zA-Z0-9\d]+(?=\d)', '', line)

        # ── STEP 3: Fix section number at line start ──────────────────
        # A TOC line starting with a section number MUST look like:
        # digit(s) DOT digit(s) OR just digit(s) DOT
        # 
        # Positional rule: in "X.Y Title", X and Y must be digits
        # Replace any 1-lookalike or 0-lookalike in that position

        # Fix first token if it looks like X.Y or X.Y.Z
        # Step 3a: replace 1-lookalikes in section number position
        def fix_section_number(m):
            num = m.group(0)
            num = re.sub(ONE_LIKE,  '1', num)
            num = re.sub(ZERO_LIKE, '0', num)
            return num

        # Match section number at start: one or more digit-like chars + dot pattern
        line = re.sub(
            r'\s+[0-9lIJ/\\|!oO\]]{1,4}\s*[°;:,\'\s]*$',
            fix_page_number,
            line
        )

        # ── STEP 4: Fix page number at end of line ────────────────────
        # Positional rule: last token on a TOC line is ALWAYS a page number
        # Page numbers are ALWAYS digits (1-999 for any normal book)
        # So: replace all 1-lookalikes and 0-lookalikes in the last token

        # Fix space inside page number at end of line
# "15 7" → "157", "/ 92" → "192", "1 88" → "188"
# Pattern: digit(s) + space + digit(s) at end of line
# Only fix if total combined length is 2-3 digits (valid page number)
        def fix_split_page_number(m):
            combined = m.group(1).replace(' ', '')
            combined = re.sub(ONE_LIKE, '1', combined)
            combined = re.sub(ZERO_LIKE, '0', combined)
            return ' ' + combined  # leading space separates from title

        line = re.sub(
            r'\s+([0-9lIJ/\\|!\s]{1,5})\s*$',
            lambda m: fix_split_page_number(m)
            if len(m.group(1).replace(' ','')) <= 4
            else m.group(0),
            line
        )

        # ── STEP 5: Fix digits between digits ─────────────────────────
        # Contextual rule: if a lookalike sits BETWEEN two real digits,
        # it must be a digit too — applies in any number in any book
        # e.g. "1O5" → "105", "1l5" → "115"
        line = re.sub(r'(?<=\d)[oO](?=\d)', '0', line)
        line = re.sub(r'(?<=\d)[lIJ](?=\d)', '1', line)

        # ── STEP 6: Fix missing dot in section numbers ────────────────
        # Structural rule: a valid section number is X.Y not XY
        # If line starts with exactly 2 digits then space then capital letter
        # it's likely a missing dot — e.g. "79 Risk" → "7.9 Risk"
        # Only do this for 2-digit combos (safe) not 3+ (too risky)
        line = re.sub(
            r'^(\d)(\d)(\s+[A-Z])',
            lambda m: m.group(1) + '.' + m.group(2) + m.group(3),
            line
        )

        # ── STEP 7: Remove duplicate page number ─────────────────────
        # Structural rule: page number should appear only once at end
        # "10.1 Introduction 270 270" → "10.1 Introduction 270"
        # Works for any book — duplicate is always an OCR artifact
        line = re.sub(r'(\b\d{1,4})\s+\1\s*$', r'\1', line)

        # ── STEP 8: Normalize dot leaders ─────────────────────────────
        # Structural rule: dot leaders between title and page number
        # in any book — normalize to single space
        # "2.3 Title .......... 34" → "2.3 Title 34"
        line = re.sub(r'[.\s]{3,}(?=\d+\s*$)', ' ', line)

        # ── STEP 9: Normalize spaces ──────────────────────────────────
        line = re.sub(r'  +', ' ', line)
        line = line.strip()

        # ── STEP 10: Final validity check ─────────────────────────────
        # A valid TOC line must have at least one word AND end in a number
        # If it fails both — it's garbage, skip it
        has_word   = bool(re.search(r'[a-zA-Z]{2,}', line))
        ends_digit = bool(re.search(r'\d\s*$', line))

        if not has_word and not ends_digit:
            continue

        # Lines with no letters at all are garbage (symbols, numbers only)
        if not has_word:
            continue

        # Remove trailing noise characters from inside title area
        # e.g. "Cost Monitoring 250 °" → "Cost Monitoring 250"
        # e.g. "Instruction in the Best Methods 292 ;" → clean
        line = re.sub(r'\s+[°;,\'"\-]+\s*$', '', line)

        # Remove stray ] inside titles that weren't caught earlier
        # e.g. "The Spiral Model 9]" — the ] is mid-title not end
        # Only remove ] when surrounded by digits (confirmed misread)
        line = re.sub(r'(\d)\]', r'\g<1>1', line)

        cleaned.append(line)

    return "\n".join(cleaned)


# ─────────────────────────────────────────────
# STEP 2 — Extract page number from a line
# ─────────────────────────────────────────────

def extract_page_number(line):
    """
    Pulls the page number from end of a TOC line.
    Handles dots, spaces, commas between title and number.

    Examples:
        "1.2 Some Title .......... 34"  → 34
        "Conclusion 54"                 → 54
        "3.1 Introduction 58"           → 58
    """
    # Match number at end of line, possibly after dots/spaces/commas
    match = re.search(r'[.\s,]*(\d{1,4})\s*[,.]?\s*$', line)
    if match:
        return int(match.group(1))
    return None


# ─────────────────────────────────────────────
# STEP 3 — Detect the level of a TOC line
# ─────────────────────────────────────────────

def detect_level(line):
    """
    Detects level purely from the leading number pattern.
    Strips the section number cleanly before returning title.
    """

    # Level 3 — X.X.X
    match = re.match(r'^(\d+\.\d+\.\d+)\s+(.+)', line)
    if match:
        return 3, match.group(1), match.group(2).strip()

    # Level 2 — X.X
    match = re.match(r'^(\d+\.\d+)\s+(.+)', line)
    if match:
        return 2, match.group(1), match.group(2).strip()

    # Level 1 — single number + dot + space + title
    # CRITICAL: title must NOT start with a digit+dot again
    # that means it's a section being misread as chapter
    match = re.match(r'^(\d+)\.\s+(.+)', line)
    if match:
        title = match.group(2).strip()
        # If title starts with digit+dot → it's a section, not chapter
        # e.g. "2. 3. Project Portfolio" → skip, it's garbled
        if re.match(r'^\d+[\.\s]', title):
            return None, None, None
        return 1, match.group(1), title

    # Level 0 — special entries
    special = [
        'conclusion', 'preface', 'introduction', 'appendix',
        'index', 'further', 'exercise', 'annex', 'bibliography',
        'references', 'glossary', 'foreword', 'acknowledgement'
    ]
    if any(line.lower().startswith(s) for s in special):
        return 0, None, line.strip()

    return None, None, None


# ─────────────────────────────────────────────
# STEP 4 — Parse all TOC lines into structure
# ─────────────────────────────────────────────

def parse_toc(raw_text):
    """
    Master parser — takes raw TOC text and returns
    a structured list of entries.

    Works for any book regardless of formatting.

    Returns list of dicts:
    [
        {
            "level": 1,
            "number": "3",
            "title": "An Overview of Project Planning",
            "page": 58,
            "raw": "3. An Overview of Project Planning 58"
        },
        ...
    ]
    """

    # Step 1: Clean the text
    cleaned = clean_ocr_text(raw_text)

    entries = []
    lines = cleaned.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract page number first
        page = extract_page_number(line)

        # Remove the page number from end of line before detecting level
        line_no_page = re.sub(r'[.\s,]*\d{1,4}\s*[,.]?\s*$', '', line).strip()

        if not line_no_page:
            continue

        # Detect level
        level, number, title = detect_level(line_no_page)

        if level is None:
            # Could not classify — skip
            continue

        # Clean up title
        title = title.strip()
        # Remove trailing dots or dashes from title
        title = re.sub(r'[.\-_]+$', '', title).strip()

        if not title:
            continue

        entries.append({
            "level": level,
            "number": number,
            "title": title,
            "page": page,
            "raw": line
        })

    return entries


# ─────────────────────────────────────────────
# STEP 5 — Build page ranges
# ─────────────────────────────────────────────

def add_page_ranges(entries):
    """
    Adds page_end to each entry.
    Guarantees page_end is always >= page_start.
    """
    for i in range(len(entries)):
        current = entries[i]

        if current["page"] is None:
            current["page_end"] = None
            continue

        # Find next entry that has a valid page number
        next_page = None
        for j in range(i + 1, len(entries)):
            if entries[j]["page"] is not None:
                next_page = entries[j]["page"]
                break

        if next_page is not None:
            page_end = next_page - 1
            # Never let page_end go before page_start
            if page_end < current["page"]:
                page_end = current["page"]
            current["page_end"] = page_end
        else:
            current["page_end"] = None

    return entries

# ─────────────────────────────────────────────
# STEP 6 — Build nested hierarchy
# ─────────────────────────────────────────────

def build_hierarchy(entries):
    """
    Converts flat list into nested chapters → sections → subsections.

    Returns:
    [
        {
            "number": "1",
            "title": "Introduction",
            "page": 1,
            "page_end": 30,
            "sections": [
                {
                    "number": "1.1",
                    "title": "What is a Project",
                    "page": 2,
                    "page_end": 5,
                    "subsections": []
                }
            ]
        }
    ]
    """
    result = []
    current_chapter = None
    current_section = None

    for entry in entries:
        level = entry["level"]

        node = {
            "number": entry["number"],
            "title": entry["title"],
            "page": entry["page"],
            "page_end": entry.get("page_end")
        }

        if level == 1:
            node["sections"] = []
            result.append(node)
            current_chapter = node
            current_section = None

        elif level == 2:
            node["subsections"] = []
            if current_chapter is not None:
                current_chapter["sections"].append(node)
            else:
                # Section without a chapter — add at root
                result.append(node)
            current_section = node

        elif level == 3:
            if current_section is not None:
                current_section["subsections"].append(node)
            elif current_chapter is not None:
                current_chapter["sections"].append(node)

        elif level == 0:
            # Special entries go at root level
            result.append(node)

    return result


# ─────────────────────────────────────────────
# MAIN — Run full parser
# ─────────────────────────────────────────────

def parse_toc_file(input_file="toc_raw.txt", output_file="toc_parsed.json"):
    """
    Full pipeline: raw text → cleaned → parsed → JSON
    """
    if not os.path.exists(input_file):
        print(f"ERROR: {input_file} not found")
        return None

    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("Parsing TOC...\n")

    # Parse flat entries
    entries = parse_toc(raw_text)
    print(f"Found {len(entries)} TOC entries")

    # Add page ranges
    entries = add_page_ranges(entries)

    # Build hierarchy
    hierarchy = build_hierarchy(entries)
    print(f"Built {len(hierarchy)} top-level chapters/sections")

    # Save JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(hierarchy, f, indent=2, ensure_ascii=False)

    print(f"\nSaved → {output_file}")

    # Print preview
    print("\n--- Preview (first 3 chapters) ---\n")
    for chapter in hierarchy[:3]:
        print(f"Chapter {chapter['number']}: {chapter['title']} "
              f"(pages {chapter['page']}–{chapter.get('page_end', '?')})")
        for section in chapter.get("sections", [])[:3]:
            print(f"  {section['number']} {section['title']} "
                  f"(page {section['page']})")

    return hierarchy


if __name__ == "__main__":
    parse_toc_file(
        input_file="toc_raw.txt",
        output_file="toc_parsed.json"
    )