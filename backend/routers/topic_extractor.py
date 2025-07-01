from fastapi import APIRouter, Body
from typing import List
import re
from keybert import KeyBERT

router = APIRouter()
kw_model = KeyBERT()


@router.post("/extract")
async def extract_topics(notes: List[str] = Body(...)):
    """
    Input: List of full LLM-generated notes (one per chunk).
    Output: Top keywords and uppercase section headers per chunk.
    """
    results = []
    for text in notes:
        # Extract top keywords using KeyBERT
        keywords = kw_model.extract_keywords(text, top_n=5)
        top_words = [kw for kw, _ in keywords]

        # Extract headings in ALL CAPS or Title Case
        headings = re.findall(r"(?:\n|^)([A-Z][A-Z\s]{3,})", text)
        headings = list(set([h.strip() for h in headings]))

        results.append({"keywords": top_words, "headings": headings})

    return results
