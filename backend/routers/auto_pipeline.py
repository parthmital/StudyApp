from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import numpy as np
import torch
import easyocr
import re
import time
import json
import requests
import os
from pdf2image import convert_from_bytes
from dotenv import load_dotenv

router = APIRouter()

# === Load .env ===
load_dotenv()
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
MAX_CHARS = 12000

# === Setup OCR ===
USE_GPU = torch.cuda.is_available()
print(f"✅ EasyOCR initialized. Using GPU: {USE_GPU}")
reader = easyocr.Reader(["en"], gpu=USE_GPU, verbose=False)

# === Prompt Template ===
PROMPT_TEMPLATE = """
Create comprehensive, beginner-friendly notes based on the provided academic PDF. The notes should:

- Begin with first principles, clearly defining foundational concepts, theories, and methodologies for readers with no prior knowledge.
- Offer in-depth explanations of all topics, addressing every relevant detail thoroughly.
- Include step-by-step derivations, formulas, and diagrams where appropriate to illustrate key ideas and processes.
- Maintain an academic yet approachable tone, ensuring clarity and accessibility for beginners.
- Be well-structured with clear headings, subheadings, bullet points, and numbered lists for easy navigation.

=== BEGIN RAW CONTENT ===
{content}
=== END RAW CONTENT ===
""".strip()


# === Utilities ===
def clean_text(raw: str) -> str:
    text = re.sub(r"\f", "", raw)
    text = re.sub(r"Page\s*\d+(\s*of\s*\d+)?", "", text, flags=re.I)
    text = re.sub(r"^[\s_=\-•●◆■◼◾]{2,}$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def call_llm_stream(prompt: str):
    if len(prompt) > MAX_CHARS:
        print(f"⚠️ Prompt too long ({len(prompt)} chars), truncating to {MAX_CHARS}")
        prompt = prompt[:MAX_CHARS]

    try:
        with requests.post(
            LLM_API_URL,
            json={"model": LLM_MODEL, "prompt": prompt, "stream": True},
            stream=True,
            timeout=300,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        parsed = json.loads(line.decode("utf-8"))
                        token = parsed.get("response", "")
                        if token:
                            yield token
                    except Exception as e:
                        print(f"⚠️ Token decode error: {e}")
                        yield f"\n[Decode error] {e}\n"
    except Exception as e:
        print(f"❌ LLM API request failed: {e}")
        yield f"\n[LLM ERROR] {e}\n"


# === Main Endpoint ===
@router.post("/autonotes", response_class=StreamingResponse)
async def auto_generate_notes(file: UploadFile = File(...)):
    """
    Upload a PDF → OCR → Chunked → Streamed LLM notes in one call.
    All progress is logged to PowerShell.
    """
    try:
        print(f"➡️ Received file: {file.filename}")
        contents = await file.read()

        start_convert = time.time()
        images = convert_from_bytes(contents, dpi=96)
        print(
            f"🖼️ Converted to {len(images)} page(s) in {round(time.time() - start_convert, 2)}s"
        )

        cleaned_pages = []
        for idx, img in enumerate(images):
            print(f"🔍 OCR on page {idx + 1}...")
            img_np = np.array(img)
            ocr_start = time.time()

            try:
                ocr_result = reader.readtext(img_np)
                raw_text = "\n".join([line[1] for line in ocr_result])
                cleaned = clean_text(raw_text)
                cleaned_pages.append(cleaned)

                print(
                    f"✅ Page {idx + 1}: {len(ocr_result)} lines in {round(time.time() - ocr_start, 2)}s"
                )
            except Exception as e:
                print(f"❌ OCR failed on page {idx + 1}: {e}")
                cleaned_pages.append("")

        chunks = [cleaned_pages[i : i + 25] for i in range(0, len(cleaned_pages), 25)]
        print(f"📦 Split into {len(chunks)} chunk(s) of up to 25 pages each")

        def stream_output():
            for i, chunk in enumerate(chunks):
                print(f"🚀 Sending chunk {i+1} to LLM...")
                prompt = PROMPT_TEMPLATE.format(content="\n\n".join(chunk))
                yield f"\n\n=== Chunk {i+1} ===\n"

                llm_start = time.time()
                for token in call_llm_stream(prompt):
                    yield token
                llm_time = round(time.time() - llm_start, 2)

                print(f"✅ Done with chunk {i+1} in {llm_time}s")
                yield f"\n\n[✓] Done with chunk {i+1} in {llm_time}s\n"

        return StreamingResponse(stream_output(), media_type="text/plain")

    except Exception as e:
        print(f"❌ Auto-notes failed: {e}")
        return {"error": str(e)}
