from fastapi import APIRouter, Query
from youtubesearchpython import VideosSearch

router = APIRouter()


@router.get("/search")
async def search_youtube(topic: str = Query(...)):
    try:
        search = VideosSearch(topic, limit=5)
        results = search.result()["result"]

        videos = [{"title": vid["title"], "url": vid["link"]} for vid in results]

        return videos
    except Exception as e:
        print("YouTube search failed:", e)
        return {"error": str(e)}