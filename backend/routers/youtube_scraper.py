from fastapi import APIRouter, Body
from typing import List
from youtubesearchpython import VideosSearch

router = APIRouter()


@router.post("/search")
async def search_youtube(topics: List[str] = Body(...), max_results: int = 3):
    """
    Accepts a list of topics and returns top N YouTube videos for each.
    """
    output = []

    for topic in topics:
        try:
            search = VideosSearch(topic, limit=max_results)
            result = search.result()["result"]
            videos = [
                {
                    "title": vid["title"],
                    "channel": vid["channel"]["name"],
                    "url": vid["link"],
                    "duration": vid["duration"],
                    "thumbnail": vid["thumbnails"][0]["url"],
                }
                for vid in result
            ]

            output.append({"topic": topic, "videos": videos})
        except Exception as e:
            output.append({"topic": topic, "error": str(e)})

    return output
