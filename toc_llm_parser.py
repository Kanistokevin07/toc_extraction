import os
import json
import re
import base64
import boto3
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

MODEL_ID = "anthropic.claude-3-7-sonnet-20250219-v1:0"

client = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


def extract_json_from_response(text):
    text = re.sub(r"```json|```", "", text).strip()

    try:
        return json.loads(text)
    except:
        pass

    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception as e:
            print("⚠️ JSON invalid:", e)
            return None

    return None


def pil_to_base64(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def parse_toc_multi(images):

    PROMPT = """
You are extracting a Table of Contents (TOC) from textbook images.

Return STRICT JSON only.

----------------------------------------
GOAL
----------------------------------------
Build a hierarchical TOC with this structure:

- Chapters
- Sections
- Subsections

(Keep your entire prompt here exactly as before)

Return ONLY valid JSON.
"""

    try:

        content = [
            {
                "type": "text",
                "text": PROMPT
            }
        ]

        # Add every image
        for img in images:

            img_b64 = pil_to_base64(img)

            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_b64
                }
            })

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        }

        response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(
            response["body"].read()
        )

        text = response_body["content"][0]["text"].strip()

        result = extract_json_from_response(text)

        if result is None:
            print(text)
            return {
                "confidence": 0.3,
                "entries": []
            }

        if isinstance(result, list):
            result = {
                "entries": result,
                "confidence": 1.0
            }

        for entry in result.get("entries", []):
            entry.setdefault("number", "")
            entry.setdefault("title", "")
            entry.setdefault("page", -1)
            entry.setdefault("sections", [])

        return result

    except Exception as e:
        print("Claude Error:", e)
        return {
            "confidence": 0,
            "entries": []
        }