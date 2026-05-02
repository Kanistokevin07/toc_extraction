from google import genai
import json
import re
from dotenv import load_dotenv
import os

def extract_json_from_response(text):
    # Remove markdown fences first
    text = re.sub(r'```json|```', '', text).strip()

    # Try full parse again
    try:
        return json.loads(text)
    except:
        pass

    # Try extracting JSON array OR object
    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print("⚠️ JSON still invalid:", e)
            return None
    
    print("❌ No JSON found in LLM response")
    return None

load_dotenv()

API_KEY = os.getenv("API_KEY")

client = genai.Client(api_key=API_KEY)

def parse_toc_multi(images):
    PROMPT = """
You are extracting a Table of Contents (TOC) from textbook images.

Return STRICT JSON only.

----------------------------------------
GOAL
----------------------------------------
Build a hierarchical TOC with this structure:

- Chapters (e.g., "CHAPTER 2 ARRAYS")
- Sections (e.g., "2.1", "2.2")
- Subsections (e.g., "4.11.1")

----------------------------------------
OUTPUT FORMAT
----------------------------------------

[
  {
    "number": "2",
    "title": "ARRAYS",
    "page": 40,
    "page_end": null,
    "sections": [
      {
        "number": "2.1",
        "title": "Axiomatization",
        "page": 40,
        "page_end": null,
        "subsections": []
      }
    ]
  }
]

----------------------------------------
STRICT RULES
----------------------------------------

1. CHAPTER DETECTION
- Lines like "CHAPTER 2 ARRAYS" MUST become a top-level node:
  {
    "number": "2",
    "title": "ARRAYS"
  }

2. SECTION ATTACHMENT
- "2.1", "2.2", etc MUST belong to Chapter 2
- NEVER attach sections under "Exercises" or "References"

3. EXERCISES / REFERENCES
- These are standalone entries
- They MUST NOT contain sections inside them

Correct:
{
  "title": "Exercises",
  "page": 36
}

Wrong:
"Exercises" → contains 2.1 ❌

4. SUBSECTIONS
- "4.11.1" belongs under "4.11"

5. PAGE NUMBERS
- Extract integer page numbers only
- Fix OCR errors (e.g., "4l" → 41)

6. NUMBER FIELD
- Must always exist
- If no number → use ""

7. NO HALLUCINATION
- Do NOT invent structure
- Use only visible text

8. CLEAN TEXT
- Remove dots, noise, OCR garbage

----------------------------------------
CRITICAL RULE
----------------------------------------
NEVER group a new chapter under previous headings like:
- Exercises
- References

A new chapter ALWAYS starts a new top-level object.

----------------------------------------

Return ONLY valid JSON.
"""

    try:
        contents = [PROMPT] + images

        response = client.models.generate_content(
            model="gemini-2.5-flash",  # change if needed
            contents=contents
        )

        text = response.text.strip()

        result = extract_json_from_response(text)

        if result is None:
            print("⚠️ JSON parse failed")
            print(text)
            return {"confidence": 0.3, "entries": []}

        # Normalize if LLM returned a list
        if isinstance(result, list):
            result = {
                "entries": result,
                "confidence": 1.0
            }

        # Safety defaults
        for entry in result.get("entries", []):
            entry.setdefault("number", "")
            entry.setdefault("title", "")
            entry.setdefault("page", -1)
            entry.setdefault("sections", [])

        return result

    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return {"confidence": 0, "entries": []}