from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    auto_pipeline,
    topic_extractor,
    youtube_scraper,
    pyq_matcher,
)

app = FastAPI()


# Health check route
@app.get("/")
def ping():
    return {"status": "Backend is alive"}


# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular routers
app.include_router(auto_pipeline.router, prefix="/auto")
app.include_router(topic_extractor.router, prefix="/topics")
app.include_router(youtube_scraper.router, prefix="/youtube")
app.include_router(pyq_matcher.router, prefix="/pyq")
