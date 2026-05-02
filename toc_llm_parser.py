from google import genai
import json
import re

client = genai.Client(api_key="AIzaSyCxXOm35Rj1lG93JdjEDhZJyeyDAq2aeqQ")

def parse_toc_multi(images):
    PROMPT = """
You are extracting a Table of Contents from book images.

STRICT RULES:
- Return ONLY valid JSON. No explanation, no markdown.
- Output must match this exact schema:

{
  "entries": [
    {
      "level": int,        # 1 = chapter, 2 = section, 3 = subsection
      "number": string,    # e.g. "1", "1.2", "2.3.1"
      "title": string,
      "page": int
    }
  ],
  "confidence": float
}

EXTRACTION RULES:
1. Detect hierarchy:
   - "1." → level 1
   - "1.2" → level 2
   - "1.2.3" → level 3

2. Extract number EXACTLY as seen (fix OCR mistakes if obvious)
3. Extract clean title (remove dots, noise, trailing symbols)
4. Extract correct page number (last number on line)
5. Ignore garbage lines, headers, footers

6. If a line has no clear number:
   - Still include it
   - Set "number": ""
   - Set level = 1

7. Do NOT hallucinate missing entries

8. Confidence:
   - 1.0 = perfect TOC
   - 0.7 = minor noise
   - <0.5 = unreliable

Return JSON only.
"""

    try:
        contents = [PROMPT] + images

        response = client.models.generate_content(
            model="gemini-2.5-flash",  # change if needed
            contents=contents
        )

        text = response.text.strip()

        try:
            return json.loads(text)
        except:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))

        print("⚠️ JSON parse failed")
        print(text)
        return {"confidence": 0.3, "entries": []}

    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return {"confidence": 0, "entries": []}