from fastapi import APIRouter, Body
from typing import Union, List, Dict, Any
import yaml
import re
import requests
import os
from dotenv import load_dotenv

router = APIRouter()

# === Load LLM Config ===
load_dotenv()
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
MAX_CHARS = 12000


# === LLM Utility ===
def call_llm(prompt: str) -> Union[List[str], Dict[str, Any]]:
    if len(prompt) > MAX_CHARS:
        prompt = prompt[:MAX_CHARS]
    try:
        response = requests.post(
            LLM_API_URL,
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()
        try:
            return yaml.safe_load(raw)
        except Exception:
            return {"error": "LLM returned invalid format", "raw": raw}
    except Exception as e:
        return {"error": str(e)}


# === Utilities ===
def clean_text(text: str) -> str:
    text = re.sub(r"\[\u2713\][^\n]*", "", text.strip())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def try_parse_yaml_wrapped_markdown(input_text: str) -> str:
    try:
        parsed = yaml.safe_load(input_text)
        if isinstance(parsed, str):
            return parsed
        elif isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
            return "\n\n".join(parsed)
    except yaml.YAMLError:
        pass
    return input_text


def build_prompt(text: str) -> str:
    return f"""
You are a highly precise and methodical extractor of educational topics for automated video scraping.

Input will be a chunk of educational or technical text, covering any subject. Your task is to extract a clean, flat list of unique, searchable topics — in the **exact order of appearance** — formatted as a JSON array, fully compatible with tools like yt-dlp.

Rules:
1. Do not group or club topics together. One topic per entry.
2. De-duplicate: if a topic appears multiple times with the same meaning, include it only once — in its first occurrence.
3. Be unambiguous: if the same problem/concept can be solved or interpreted using multiple methods (e.g., "0-1 Knapsack" via DP or Branch & Bound), include the method or technique explicitly (e.g., "0-1 Knapsack Problem – Dynamic Programming").
4. Use full, clear names for algorithms, techniques, or concepts. Avoid abbreviations unless they are globally standard (e.g., "KMP Algorithm" is okay).
5. Ensure each topic is a valid search term for YouTube scraping. If a topic is too vague (e.g., “Complexity”), rewrite it to be specific (e.g., “Computational Complexity Theory”).
6. Preserve the order of appearance from the input text.
7. Output only the final list as a JSON array of strings. Do not include explanations or extra formatting.

Now read the input text and return the extracted topic list in JSON format.

Text:
{text}
"""


# === Main Endpoint ===
@router.post("/extract")
async def extract_topics(
    notes: Union[str, List[str]] = Body(
        ..., description="YAML-wrapped markdown string or list of note chunks"
    )
):
    if isinstance(notes, str):
        notes = try_parse_yaml_wrapped_markdown(notes)

    if isinstance(notes, list) and all(isinstance(x, str) for x in notes):
        notes = "\n\n".join(notes)

    if not isinstance(notes, str):
        return {
            "error": "Invalid input type. Must be a YAML string or a list of strings."
        }

    text = clean_text(notes)
    prompt = build_prompt(text)
    print("🚀 Calling LLM for full document topic extraction...")

    llm_result = call_llm(prompt)

    if isinstance(llm_result, dict) and "error" in llm_result:
        print(f"❌ LLM failed: {llm_result['error']}")
        return {"topics": [], "error": llm_result["error"]}

    return {"topics": llm_result}
