from fastapi import APIRouter, Body
from typing import List
import requests  # Use this for LMStudio/Ollama/DeepSeek API
import os

router = APIRouter()

# 🧠 Main LLM prompt
PROMPT_TEMPLATE = """Create comprehensive, beginner-friendly notes based on the provided academic PDF. The notes should:

- Begin with first principles, clearly defining foundational concepts, theories, and methodologies for readers with no prior knowledge.
- Offer in-depth explanations of all topics, addressing every relevant detail thoroughly.
- Include step-by-step derivations, formulas, and diagrams where appropriate to illustrate key ideas and processes.
- Maintain an academic yet approachable tone, ensuring clarity and accessibility for beginners.
- Be well-structured with clear headings, subheadings, bullet points, and numbered lists for easy navigation.

=== BEGIN RAW CONTENT ===
{content}
=== END RAW CONTENT ===
"""

# 🧰 Configurable LLM endpoint
LLM_ENDPOINT = os.getenv(
    "LLM_API_URL", "http://localhost:11434/api/generate"
)  # Adjust as needed


def call_llm(prompt: str) -> str:
    """Call LLM via local API (e.g., Ollama, DeepSeek, LMStudio)."""
    try:
        res = requests.post(
            LLM_ENDPOINT,
            json={
                "prompt": prompt,
                "model": "deepseek-coder:6.7b",  # or whatever model you use
                "temperature": 0.7,
                "max_tokens": 2048,
                "stream": False,
            },
            timeout=60,
        )
        res.raise_for_status()
        return res.json().get("response") or res.text
    except Exception as e:
        return f"[LLM ERROR] {str(e)}"


@router.post("/generate")
async def generate_notes(pages: List[str] = Body(...)):
    chunks = [pages[i : i + 25] for i in range(0, len(pages), 25)]  # ~25-page chunks
    results = []

    for i, chunk in enumerate(chunks):
        combined_text = "\n\n".join(chunk)
        prompt = PROMPT_TEMPLATE.format(content=combined_text)
        print(f"🚀 Generating notes for chunk {i+1}...")
        notes = call_llm(prompt)
        results.append(
            {
                "title": f"Chunk {i+1}",
                "content": notes.strip(),
            }
        )

    return results


@router.get("/get_all")
async def get_all_notes():
    # Still mock
    return [
        {"title": "Sample Note 1", "content": "This is a dummy note."},
        {"title": "Sample Note 2", "content": "Another placeholder."},
    ]
