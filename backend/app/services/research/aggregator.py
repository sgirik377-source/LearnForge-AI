import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.research_source import ResearchSource
from app.models.generation_task import GenerationTask
from app.services.research.web_service import WebResearchProvider
from app.services.research.books_service import GoogleBooksProvider
from app.services.research.youtube_service import YouTubeProvider


class ResearchAggregator:
    """
    Multimodal Research Aggregator.
    Coordinates concurrent queries across Web, Google Books, and YouTube providers.
    Enforces fault isolation, deduplication, citation tagging, and SQLite persistence.
    """

    def __init__(
        self,
        web_provider: Optional[WebResearchProvider] = None,
        books_provider: Optional[GoogleBooksProvider] = None,
        youtube_provider: Optional[YouTubeProvider] = None
    ):
        self.web_provider = web_provider or WebResearchProvider()
        self.books_provider = books_provider or GoogleBooksProvider()
        self.youtube_provider = youtube_provider or YouTubeProvider()

    async def harvest(
        self,
        query: str,
        learning_objectives: Optional[List[str]] = None,
        max_per_provider: int = 3
    ) -> Dict[str, Any]:
        """
        Execute research across all three providers with strict fault isolation.
        Failure of one provider does not affect or destroy other results.
        """
        web_query = query

        # Execute providers concurrently with return_exceptions=True
        results = await asyncio.gather(
            self._safe_search(self.web_provider, web_query, max_per_provider),
            self._safe_search(self.books_provider, query, max_per_provider),
            self._safe_search(self.youtube_provider, query, max_per_provider),
            return_exceptions=True
        )

        web_res = results[0] if isinstance(results[0], dict) else {"items": [], "error": str(results[0])}
        books_res = results[1] if isinstance(results[1], dict) else {"items": [], "error": str(results[1])}
        youtube_res = results[2] if isinstance(results[2], dict) else {"items": [], "error": str(results[2])}

        provider_errors = {}
        if web_res.get("error"):
            provider_errors["web"] = web_res["error"]
        if books_res.get("error"):
            provider_errors["books"] = books_res["error"]
        if youtube_res.get("error"):
            provider_errors["youtube"] = youtube_res["error"]

        raw_candidates: List[Dict[str, Any]] = (
            web_res.get("items", []) +
            books_res.get("items", []) +
            youtube_res.get("items", [])
        )

        # Deduplication by URL or unique identifier
        deduplicated = self._deduplicate_sources(raw_candidates)

        # Citation tagging ([REF-1], [REF-2], ...)
        tagged_sources = self._assign_citation_tags(deduplicated)

        return {
            "sources": tagged_sources,
            "total_count": len(tagged_sources),
            "accessible_count": sum(1 for s in tagged_sources if s.get("is_content_accessible")),
            "metadata_only_count": sum(1 for s in tagged_sources if not s.get("is_content_accessible")),
            "provider_errors": provider_errors
        }

    async def _safe_search(self, provider: Any, query: str, max_results: int) -> Dict[str, Any]:
        """Wrap provider call in exception boundary to ensure independent failure handling."""
        try:
            items = await provider.search(query, max_results=max_results)
            return {"items": items, "error": None}
        except Exception as e:
            return {"items": [], "error": str(e)}

    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entries based on normalized URL or identifier."""
        seen = set()
        unique = []
        for s in sources:
            identifier = (s.get("url_or_identifier") or s.get("title", "")).strip().lower()
            # Normalize trailing slashes
            if identifier.endswith("/"):
                identifier = identifier[:-1]

            if identifier and identifier not in seen:
                seen.add(identifier)
                unique.append(s)
        return unique

    def _assign_citation_tags(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign deterministic unique citation tags ([REF-1], [REF-2], etc.)."""
        tagged = []
        for idx, src in enumerate(sources, start=1):
            src_copy = dict(src)
            src_copy["citation_tag"] = f"[REF-{idx}]"
            tagged.append(src_copy)
        return tagged

    def persist_sources(
        self,
        lesson_id: str,
        sources: List[Dict[str, Any]],
        db: Session,
        replace_existing: bool = True
    ) -> List[ResearchSource]:
        """Persist normalized sources to SQLite database."""
        if replace_existing:
            db.query(ResearchSource).filter(ResearchSource.lesson_id == lesson_id).delete()

        db_records: List[ResearchSource] = []
        for s in sources:
            record = ResearchSource(
                id=str(uuid.uuid4()),
                lesson_id=lesson_id,
                source_type=s["source_type"],
                citation_tag=s["citation_tag"],
                title=s["title"],
                url_or_identifier=s.get("url_or_identifier"),
                author_or_channel=s.get("author_or_channel"),
                is_content_accessible=s.get("is_content_accessible", False),
                preview_type=s.get("preview_type", "snippet"),
                accessible_text_length=s.get("accessible_text_length", 0.0),
                extracted_content=s.get("extracted_content"),
                key_takeaways=s.get("key_takeaways"),
                relevance_score=s.get("relevance_score", 1.0),
                verification_scope_note=s.get("verification_scope_note")
            )
            db.add(record)
            db_records.append(record)

        db.commit()
        for r in db_records:
            db.refresh(r)
        return db_records
