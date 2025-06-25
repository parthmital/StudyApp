from fastapi import APIRouter, Body
from typing import List
import random

router = APIRouter()


@router.post("/generate")
async def generate_notes(pages: List[str] = Body(...)):
    # Simulate generation logic (replace with DeepSeek/Ollama later)
    notes = []
    for i, content in enumerate(pages):
        notes.append(
            {
                "title": f"Chunk {i+1}",
                "content": f"Auto-generated notes from OCR content:\n{content[:300]}...",
            }
        )
    return notes


@router.get("/get_all")
async def get_all_notes():
    # Placeholder for storing/fetching processed notes
    return [
        {"title": "Sample Note 1", "content": "This is a dummy note."},
        {"title": "Sample Note 2", "content": "Another placeholder."},
    ]