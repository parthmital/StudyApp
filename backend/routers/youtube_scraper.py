from fastapi import APIRouter, Body
from typing import List, Dict, Any
import yt_dlp

router = APIRouter()


@router.post("/search")
async def search_youtube(
    topic_chunks: List[Dict[str, Any]] = Body(...),
    max_results: int = 3,
):
    """
    Accepts a list of dicts with 'keywords' and 'headings' (optional 'chunk').
    Returns up to N unique YouTube videos per topic (no duplicates across topics).
    """
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "dump_single_json": True,
    }

    output = []
    seen_urls = set()

    for chunk in topic_chunks:
        chunk_id = chunk.get("chunk")
        topics = set((chunk.get("keywords") or []) + (chunk.get("headings") or []))

        for topic in topics:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_query = f"ytsearch{max_results}:{topic}"
                    result = ydl.extract_info(search_query, download=False)
                    videos = []

                    for vid in result.get("entries", []):
                        url = f"https://www.youtube.com/watch?v={vid['id']}"
                        if url in seen_urls:
                            continue

                        video_entry = {
                            "title": vid["title"],
                            "url": url,
                            "channel": vid.get("uploader", "Unknown"),
                            "duration": vid.get("duration"),
                            "thumbnail": vid.get("thumbnails", [{}])[0].get("url", ""),
                        }

                        videos.append(video_entry)
                        seen_urls.add(url)

                        # Stop early if we've collected enough videos
                        if len(videos) >= max_results:
                            break

                    output.append({"chunk": chunk_id, "topic": topic, "videos": videos})

            except Exception as e:
                output.append({"chunk": chunk_id, "topic": topic, "error": str(e)})

    return output
