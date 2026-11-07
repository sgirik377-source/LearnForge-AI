import re
import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from app.core.config import settings


class YouTubeProvider:
    """
    Dedicated YouTube Educational Video Provider.
    Retrieves video metadata, titles, channels, and URLs.
    Performs best-effort transcript extraction using youtube-transcript-api.
    Transcript retrieval failures are handled gracefully and never block the pipeline.
    """

    YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

    def __init__(self, api_key: Optional[str] = None, timeout_secs: float = 8.0):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.timeout_secs = timeout_secs

    async def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for educational lectures and tutorials.
        Falls back to public search scraping if API key is not configured.
        """
        video_metadata_list: List[Dict[str, Any]] = []

        if self.api_key:
            try:
                video_metadata_list = await self._search_via_api(query, max_results=max_results)
            except Exception:
                video_metadata_list = []

        # Graceful fallback when API key is missing or quota exceeded
        if not video_metadata_list:
            try:
                video_metadata_list = await self._search_public_fallback(query, max_results=max_results)
            except Exception:
                video_metadata_list = []

        if not video_metadata_list:
            return []

        results: List[Dict[str, Any]] = []

        # Process each video and attempt best-effort transcript retrieval
        for v in video_metadata_list[:max_results]:
            video_id = v.get("video_id")
            title = v.get("title", "Educational Video")
            channel = v.get("channel", "YouTube")
            desc = v.get("description", "")
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Best-effort transcript retrieval
            transcript_content = self._fetch_transcript_sync(video_id)

            if transcript_content:
                results.append({
                    "source_type": "youtube",
                    "title": title,
                    "url_or_identifier": video_url,
                    "author_or_channel": channel,
                    "is_content_accessible": True,
                    "preview_type": "transcript",
                    "extracted_content": transcript_content[:6000],  # Keep high-signal portion
                    "accessible_text_length": float(len(transcript_content)),
                    "key_takeaways": desc[:350] or transcript_content[:350] + "...",
                    "relevance_score": 0.92,
                    "verification_scope_note": "Verified spoken audio transcript retrieved via YouTube Transcript API.",
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                })
            else:
                results.append({
                    "source_type": "youtube",
                    "title": title,
                    "url_or_identifier": video_url,
                    "author_or_channel": channel,
                    "is_content_accessible": False,
                    "preview_type": "metadata_only",
                    "extracted_content": None,
                    "accessible_text_length": 0.0,
                    "key_takeaways": desc[:350] or "Video metadata record. No transcript available.",
                    "relevance_score": 0.70,
                    "verification_scope_note": "Transcript unavailable or disabled. Grounding limited to video metadata.",
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                })

        return results

    async def _search_via_api(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Query official YouTube Data API v3 search endpoint."""
        params = {
            "part": "snippet",
            "q": f"{query} lecture tutorial",
            "type": "video",
            "videoCaption": "any",
            "maxResults": max_results,
            "key": self.api_key
        }

        async with httpx.AsyncClient(timeout=self.timeout_secs) as client:
            resp = await client.get(self.YOUTUBE_SEARCH_URL, params=params)
            if resp.status_code != 200:
                return []

            data = resp.json()
            videos = []
            for item in data.get("items", []):
                vid = item.get("id", {}).get("videoId")
                snippet = item.get("snippet", {})
                if vid:
                    videos.append({
                        "video_id": vid,
                        "title": snippet.get("title", "Video Lecture"),
                        "channel": snippet.get("channelTitle", "YouTube Creator"),
                        "description": snippet.get("description", "")
                    })
            return videos

    async def _search_public_fallback(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Public search scraper fallback when no YouTube API key is provided.
        Parses initial search page or Invidious instance.
        """
        encoded = urllib.parse.quote_plus(f"{query} educational lecture")
        search_url = f"https://www.youtube.com/results?search_query={encoded}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

        async with httpx.AsyncClient(timeout=self.timeout_secs, follow_redirects=True) as client:
            resp = await client.get(search_url, headers=headers)
            if resp.status_code != 200:
                return []

            # Extract video IDs from standard youtube HTML results
            video_ids = re.findall(r"/watch\?v=([a-zA-Z0-9_-]{11})", resp.text)
            unique_ids = []
            for vid in video_ids:
                if vid not in unique_ids:
                    unique_ids.append(vid)
                if len(unique_ids) >= max_results:
                    break

            videos = []
            for vid in unique_ids:
                # Fetch actual video title and channel name via public YouTube oEmbed endpoint
                actual_title, actual_channel = await self._fetch_oembed_metadata(vid, client)
                videos.append({
                    "video_id": vid,
                    "title": actual_title or f"Video Tutorial on {query}",
                    "channel": actual_channel or "Educational Creator",
                    "description": f"Curated video lecture on {query}"
                })
            return videos

    async def _fetch_oembed_metadata(self, video_id: str, client: httpx.AsyncClient) -> tuple[Optional[str], Optional[str]]:
        """Fetch authentic title and channel name from YouTube oEmbed endpoint without API key."""
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = await client.get(oembed_url, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("title"), data.get("author_name")
        except Exception:
            pass
        return None, None

    def _fetch_transcript_sync(self, video_id: str) -> Optional[str]:
        """
        Attempt to retrieve transcript via youtube-transcript-api.
        Best-effort: handles any exception without failing.
        """
        try:
            # Try to fetch English transcript first
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
            if not transcript_list:
                return None

            lines = [entry.get("text", "") for entry in transcript_list if entry.get("text")]
            full_text = " ".join(lines)
            return full_text if len(full_text.strip()) > 50 else None
        except Exception:
            return None
