from fastapi import APIRouter, Body
from typing import Union, List
import re
from keybert import KeyBERT

router = APIRouter()
kw_model = KeyBERT()


def split_chunks_from_raw(raw: str) -> List[str]:
    """Splits raw LLM text by === Chunk X === headers."""
    raw = raw.replace("\r", "")
    chunks = re.split(r"=== Chunk \d+ ===", raw)
    chunks = [c.strip() for c in chunks if c.strip()]
    return chunks


def clean_single_chunk(text: str) -> str:
    """Cleans trailing '[✓] Done...' and extra newlines."""
    text = re.sub(r"\[✓\].*?s$", "", text.strip())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@router.post("/extract")
async def extract_topics(
    notes: Union[str, List[str]] = Body(
        ..., description="Raw LLM output as string OR cleaned list of note chunks"
    )
):
    """
    Accepts:
    - A single pasted raw string (LLM output with '=== Chunk X ===' and '[✓] Done...')
    - OR a list of cleaned note chunks

    Returns:
    - Keywords and section heading candidates for each chunk
    """
    if isinstance(notes, str):
        print("⚙️ Detected raw text input — splitting into chunks...")
        chunks = split_chunks_from_raw(notes)
    elif isinstance(notes, list):
        print("📦 Received list of note chunks.")
        chunks = notes
    else:
        return {"error": "Invalid input type. Must be string or list of strings."}

    results = []

    for idx, raw_text in enumerate(chunks):
        text = clean_single_chunk(raw_text)

        # === Keyword Extraction ===
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
                banned in kw.lower()
                for banned in ["chunk", "value", "data", "section", "done"]
            )
        ]
        keywords = list(dict.fromkeys(keywords))[:15]

        # === Heading Extraction ===
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
