# backend/routers/notes_generate.py

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from typing import List, Generator
import requests
import os
import logging
import time
import json
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()

router = APIRouter()

# === Configuration ===
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
MAX_CHARS = 12000

# === Logging ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logging.info(f"📦 Using LLM model '{LLM_MODEL}' at {LLM_API_URL}")

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


# === Call LLM with Streaming ===
def call_llm_stream(prompt: str) -> Generator[str, None, None]:
    """Streams tokens from local LLM server (e.g., Ollama)."""
    if len(prompt) > MAX_CHARS:
        logging.warning(f"⚠️ Prompt exceeds {MAX_CHARS} chars. Truncating.")
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
                        decoded = line.decode("utf-8")
                        parsed = json.loads(decoded)
                        token = parsed.get("response", "")
                        if token:
                            yield token
                    except Exception as e:
                        logging.warning(f"⚠️ Streaming decode error: {e}")
    except Exception as e:
        err = f"[LLM STREAM ERROR] {e}"
        logging.error(err)
        yield f"\n{err}\n"


# === /generate endpoint ===
@router.post("/generate", response_class=StreamingResponse)
async def generate_notes(pages: List[str] = Body(...)):
    """
    Input: OCR'd text pages (raw or cleaned).
    Output: Chunked + streamed LLM notes, live.
    """
    chunks = [pages[i : i + 25] for i in range(0, len(pages), 25)]

    def stream_all_chunks():
        for idx, chunk in enumerate(chunks):
            title = f"Chunk {idx + 1}"
            logging.info(f"🚀 {title} → Sending to LLM...")

            content = "\n\n".join(chunk)
            prompt = PROMPT_TEMPLATE.format(content=content)

            yield f"\n\n=== {title} ===\n"
            start_time = time.time()

            for token in call_llm_stream(prompt):
                yield token

            duration = round(time.time() - start_time, 2)
            yield f"\n\n[✓] Finished {title} in {duration}s\n"
            logging.info(f"✅ {title} completed in {duration}s")

    return StreamingResponse(stream_all_chunks(), media_type="text/plain")


# === Dummy testing endpoint ===
@router.get("/get_all")
async def get_all_notes():
    return [
        {"title": "Sample Note 1", "content": "This is a placeholder note."},
        {"title": "Sample Note 2", "content": "Another example entry."},
    ]
