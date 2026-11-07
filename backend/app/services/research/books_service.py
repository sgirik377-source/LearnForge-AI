import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings


class GoogleBooksProvider:
    """
    Dedicated Books Provider.
    Primary: Google Books API (capturing volumeInfo, ISBN, and indexed snippets).
    Fallback: Open Library Open API (if Google Books returns 429 rate limit or quota exceeded).
    Strictly distinguishes accessible snippets from metadata-only records.
    Never fabricates excerpts or claims to have inspected inaccessible full text.
    """

    GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
    OPEN_LIBRARY_URL = "https://openlibrary.org/search.json"

    def __init__(self, api_key: Optional[str] = None, timeout_secs: float = 8.0):
        self.api_key = api_key or settings.GOOGLE_BOOKS_API_KEY
        self.timeout_secs = timeout_secs

    async def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search books for academic references and textbooks.
        Attempts Google Books first; automatically falls back to Open Library if rate-limited.
        """
        results: List[Dict[str, Any]] = []

        # 1. Attempt Google Books API
        try:
            results = await self._search_google_books(query, max_results)
        except Exception:
            results = []

        # 2. Fallback to Open Library if Google Books returned 0 results or hit 429 rate limit
        if not results:
            try:
                results = await self._search_open_library(query, max_results)
            except Exception:
                results = []

        return results

    async def _search_google_books(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Query Google Books API."""
        params: Dict[str, Any] = {
            "q": query,
            "maxResults": max_results,
            "printType": "books",
            "langRestrict": "en"
        }
        if self.api_key:
            params["key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout_secs) as client:
            resp = await client.get(self.GOOGLE_BOOKS_URL, params=params)
            if resp.status_code != 200:
                # E.g. 429 Rate Limit
                return []

            data = resp.json()
            items = data.get("items", [])
            results: List[Dict[str, Any]] = []

            for item in items:
                v_info = item.get("volumeInfo", {})
                access_info = item.get("accessInfo", {})
                search_info = item.get("searchInfo", {})

                title = v_info.get("title", "Untitled Work")
                authors = ", ".join(v_info.get("authors", [])) or "Unknown Author"
                publisher = v_info.get("publisher")
                pub_date = v_info.get("publishedDate")
                description = v_info.get("description", "")
                preview_url = v_info.get("previewLink") or v_info.get("infoLink")

                isbn = None
                for ident in v_info.get("industryIdentifiers", []):
                    if ident.get("type") in ("ISBN_13", "ISBN_10"):
                        isbn = ident.get("identifier")
                        break

                viewability = access_info.get("viewability", "UNKNOWN")
                raw_snippet = search_info.get("textSnippet")

                if raw_snippet:
                    cleaned_snippet = BeautifulSoup(raw_snippet, "html.parser").get_text(separator=" ", strip=True)
                    is_accessible = True
                    preview_type = "snippet"
                    extracted_content = f"Search Match Snippet from '{title}':\n\n\"{cleaned_snippet}\""
                    scope_note = (
                        f"Verified search snippet indexed by Google Books ({viewability}). "
                        "Verified against accessible search excerpt only."
                    )
                else:
                    is_accessible = False
                    preview_type = "metadata_only"
                    extracted_content = None
                    scope_note = (
                        f"Metadata only ({viewability}). Full text is copyrighted and inaccessible. "
                        "Claims cannot be verified against internal body text."
                    )

                source_author_str = f"{authors} ({publisher}, {pub_date})" if publisher else authors

                results.append({
                    "source_type": "book",
                    "title": title,
                    "url_or_identifier": isbn or preview_url or item.get("id"),
                    "author_or_channel": source_author_str,
                    "is_content_accessible": is_accessible,
                    "preview_type": preview_type,
                    "extracted_content": extracted_content,
                    "accessible_text_length": float(len(extracted_content)) if extracted_content else 0.0,
                    "key_takeaways": description[:400] + "..." if len(description) > 400 else description or "Bibliographic record.",
                    "relevance_score": 0.90 if is_accessible else 0.75,
                    "verification_scope_note": scope_note,
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                })

            return results

    async def _search_open_library(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Query Open Library Open API as resilient fallback for textbooks and academic monographs."""
        params = {
            "q": query,
            "limit": max_results,
            "mode": "everything"
        }

        async with httpx.AsyncClient(timeout=self.timeout_secs) as client:
            resp = await client.get(self.OPEN_LIBRARY_URL, params=params)
            if resp.status_code != 200:
                return []

            data = resp.json()
            docs = data.get("docs", [])
            results: List[Dict[str, Any]] = []

            for doc in docs[:max_results]:
                title = doc.get("title", "Academic Book")
                authors = ", ".join(doc.get("author_name", [])) or "Academic Author"
                publishers = ", ".join(doc.get("publisher", [])[:2])
                publish_year = str(doc.get("first_publish_year", ""))
                isbns = doc.get("isbn", [])
                isbn = isbns[0] if isbns else None
                key = doc.get("key", "")
                url = f"https://openlibrary.org{key}" if key else f"https://openlibrary.org/isbn/{isbn}" if isbn else None

                # Open Library has_fulltext check
                has_fulltext = doc.get("has_fulltext", False)

                author_meta = f"{authors} ({publishers}, {publish_year})" if publishers else f"{authors} ({publish_year})"

                results.append({
                    "source_type": "book",
                    "title": title,
                    "url_or_identifier": isbn or url or key,
                    "author_or_channel": author_meta,
                    "is_content_accessible": False,  # Open library returns metadata catalog records
                    "preview_type": "metadata_only",
                    "extracted_content": None,
                    "accessible_text_length": 0.0,
                    "key_takeaways": f"Bibliographic entry from Open Library catalog. Subjects: {', '.join(doc.get('subject', [])[:3])}",
                    "relevance_score": 0.85,
                    "verification_scope_note": "Open Library: Metadata catalog record. Full internal text not indexed for automated extraction.",
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                })

            return results
