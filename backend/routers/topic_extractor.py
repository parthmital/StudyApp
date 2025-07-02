from fastapi import APIRouter, Body
from typing import Union, List
import re
import yaml
from keybert import KeyBERT

router = APIRouter()
kw_model = KeyBERT()


def split_chunks_from_raw(raw: str) -> List[str]:
    raw = raw.replace("\r", "")
    chunks = re.split(r"=== Chunk \d+ ===", raw)
    return [c.strip() for c in chunks if c.strip()]


def clean_single_chunk(text: str) -> str:
    text = re.sub(r"\[✓\][^\n]*", "", text.strip())  # Fixes broken pattern
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def try_parse_yaml_wrapped_markdown(input_text: str) -> Union[str, List[str]]:
    """
    Attempts to parse a string as YAML.
    Returns:
    - str: if it's a long quoted markdown string
    - list[str]: if it's already split into chunks
    - fallback to raw string if YAML parse fails
    """
    try:
        parsed = yaml.safe_load(input_text)
        if isinstance(parsed, str):
            return parsed  # treat as raw markdown blob
        elif isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
            return parsed  # treat as chunks
    except yaml.YAMLError:
        pass
    return input_text  # fallback to raw string


@router.post("/extract")
async def extract_topics(
    notes: Union[str, List[str]] = Body(
        ..., description="YAML-wrapped markdown string or list of note chunks"
    )
):
    """
    Accepts:
    - A YAML-wrapped markdown string (users paste raw markdown wrapped in double quotes)
    - OR a YAML list of strings
    - OR a raw markdown string directly

    Returns:
    - Extracted keywords and heading candidates per chunk
    """

    if isinstance(notes, str):
        notes = try_parse_yaml_wrapped_markdown(notes)

    if isinstance(notes, str):
        print("⚙️ Detected raw markdown string — splitting into chunks...")
        chunks = split_chunks_from_raw(notes)
    elif isinstance(notes, list) and all(isinstance(x, str) for x in notes):
        print("📦 Detected list of note chunks.")
        chunks = notes
    else:
        return {
            "error": "Invalid input type. Must be a YAML string or a list of strings."
        }

    results = []
    for idx, raw_text in enumerate(chunks):
        text = clean_single_chunk(raw_text)

        kw_output = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=30,
        )
        keywords = [
            kw
            for kw, _ in kw_output
            if len(kw) > 4
            and not any(
                bad in kw.lower()
                for bad in ["chunk", "value", "data", "section", "done"]
            )
        ]
        keywords = list(dict.fromkeys(keywords))[:15]

        markdown = re.findall(r"(?m)^#{1,6}\s*(.+)$", text)
        bold = re.findall(r"\*\*(.*?)\*\*", text)
        filtered_bold = [
            b.strip()
            for b in bold
            if len(b.strip()) > 6 and b[0].isupper() and not re.search(r"\d", b)
        ]
        headings = list(dict.fromkeys(markdown + filtered_bold))

        results.append(
            {
                "chunk": idx + 1,
                "keywords": keywords,
                "headings": headings,
            }
        )

    return results
