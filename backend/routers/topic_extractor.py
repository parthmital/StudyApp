from fastapi import APIRouter, Body
from typing import List
import re
from keybert import KeyBERT

router = APIRouter()
kw_model = KeyBERT()


@router.post("/extract")
async def extract_topics(notes: List[str] = Body(...)):
    keywords_by_note = []
    for text in notes:
        # Run simple keyword extractor
        keywords = kw_model.extract_keywords(text, top_n=5)
        top_words = [kw for kw, _ in keywords]

        # Also attempt some regex based section splitting
        headings = re.findall(r"(?i)([A-Z][A-Z\s]{3,})", text)

        keywords_by_note.append(
            {"keywords": top_words, "headings": list(set(headings))}
        )

    return keywords_by_note