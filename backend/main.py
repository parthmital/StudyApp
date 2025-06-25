# == backend/main.py ==
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    pdf_ocr,
    notes_generator,
    topic_extractor,
    youtube_scraper,
    pyq_matcher,
)

app = FastAPI()

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular routers
app.include_router(pdf_ocr.router, prefix="/ocr")
app.include_router(notes_generator.router, prefix="/notes")
app.include_router(topic_extractor.router, prefix="/topics")
app.include_router(youtube_scraper.router, prefix="/youtube")
app.include_router(pyq_matcher.router, prefix="/pyq")