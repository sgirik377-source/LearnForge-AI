import asyncio
import uuid
from app.core.database import Base, engine, SessionLocal
from app.models.lesson import Lesson
from app.models.research_source import ResearchSource
from app.models.generation_task import GenerationTask
from app.services.research.aggregator import ResearchAggregator


class MockWebProvider:
    async def search(self, query: str, max_results: int = 3):
        return [
            {
                "source_type": "web",
                "title": "Introduction to Vector Embeddings",
                "url_or_identifier": "https://example.com/vector-embeddings",
                "author_or_channel": "example.com",
                "is_content_accessible": True,
                "preview_type": "full_text",
                "extracted_content": "A vector embedding represents words or objects in a dense continuous high-dimensional space.",
                "accessible_text_length": 86.0,
                "key_takeaways": "Core concept of dense mathematical embeddings.",
                "relevance_score": 0.95,
                "verification_scope_note": "Extracted via BeautifulSoup."
            },
            {
                "source_type": "web",
                "title": "Paywalled Academic Paper",
                "url_or_identifier": "https://paywall.org/article-101",
                "author_or_channel": "paywall.org",
                "is_content_accessible": False,
                "preview_type": "snippet",
                "extracted_content": None,
                "accessible_text_length": 0.0,
                "key_takeaways": "Abstract synopsis of academic research.",
                "relevance_score": 0.70,
                "verification_scope_note": "Metadata only: Page inaccessible (HTTP 403)"
            }
        ]


class MockBooksProvider:
    async def search(self, query: str, max_results: int = 3):
        return [
            {
                "source_type": "book",
                "title": "Speech and Language Processing (3rd ed.)",
                "url_or_identifier": "978-0131873216",
                "author_or_channel": "Dan Jurafsky, James H. Martin",
                "is_content_accessible": True,
                "preview_type": "snippet",
                "extracted_content": "Vector semantics can be represented by dense vectors produced by models like word2vec or BERT.",
                "accessible_text_length": 95.0,
                "key_takeaways": "Standard reference textbook for computational linguistics.",
                "relevance_score": 0.95,
                "verification_scope_note": "Verified search snippet indexed by Google Books."
            },
            {
                "source_type": "book",
                "title": "Foundations of Statistical Natural Language Processing",
                "url_or_identifier": "978-0262133609",
                "author_or_channel": "Christopher D. Manning",
                "is_content_accessible": False,
                "preview_type": "metadata_only",
                "extracted_content": None,
                "accessible_text_length": 0.0,
                "key_takeaways": "Classic text on statistical NLP fundamentals.",
                "relevance_score": 0.75,
                "verification_scope_note": "Metadata only (NO_PAGES). Content is copyrighted and inaccessible."
            }
        ]


class MockYouTubeProvider:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def search(self, query: str, max_results: int = 3):
        if self.should_fail:
            raise ConnectionError("YouTube API rate limit or network timeout")

        return [
            {
                "source_type": "youtube",
                "title": "Word Embeddings Explained Clearly",
                "url_or_identifier": "https://www.youtube.com/watch?v=mock_vid_1",
                "author_or_channel": "StatQuest with Josh Starmer",
                "is_content_accessible": True,
                "preview_type": "transcript",
                "extracted_content": "Welcome to StatQuest! Today we are talking about word embeddings and vectors in high dimensions...",
                "accessible_text_length": 98.0,
                "key_takeaways": "Video explaining vector math and cosine angles.",
                "relevance_score": 0.92,
                "verification_scope_note": "Verified spoken transcript retrieved via YouTube Transcript API."
            },
            {
                "source_type": "youtube",
                "title": "Deep Learning Lecture 12",
                "url_or_identifier": "https://www.youtube.com/watch?v=mock_vid_2",
                "author_or_channel": "MIT OpenCourseWare",
                "is_content_accessible": False,
                "preview_type": "metadata_only",
                "extracted_content": None,
                "accessible_text_length": 0.0,
                "key_takeaways": "University lecture recording on neural embeddings.",
                "relevance_score": 0.70,
                "verification_scope_note": "Transcript unavailable or disabled. Grounding limited to video metadata."
            }
        ]


def test_research_pipeline_deterministic():
    """Deterministic test for normalization, deduplication, citation tagging, and SQLite persistence."""
    print("\n--- [Test 1] Deterministic Multi-Provider Harvest ---")
    aggregator = ResearchAggregator(
        web_provider=MockWebProvider(),
        books_provider=MockBooksProvider(),
        youtube_provider=MockYouTubeProvider(should_fail=False)
    )

    result = asyncio.run(aggregator.harvest("Vector Embeddings", learning_objectives=["Understand cosine distance"]))
    sources = result["sources"]

    print(f"Total harvested sources: {result['total_count']}")
    print(f"Accessible sources: {result['accessible_count']}")
    print(f"Metadata-only sources: {result['metadata_only_count']}")

    assert result["total_count"] == 6
    assert result["accessible_count"] == 3
    assert result["metadata_only_count"] == 3
    assert len(result["provider_errors"]) == 0

    # Verify citation tags are sequential
    for i, s in enumerate(sources, start=1):
        assert s["citation_tag"] == f"[REF-{i}]"
        print(f"  {s['citation_tag']} ({s['source_type']}): '{s['title']}' | Accessible: {s['is_content_accessible']} ({s['preview_type']})")

    # Verify metadata vs accessible-content distinction (Requirement 1 & 2)
    book_meta = next(s for s in sources if s["title"] == "Foundations of Statistical Natural Language Processing")
    assert book_meta["is_content_accessible"] is False
    assert book_meta["preview_type"] == "metadata_only"
    assert book_meta["extracted_content"] is None
    assert "Metadata only (NO_PAGES)" in book_meta["verification_scope_note"]

    book_snippet = next(s for s in sources if s["title"] == "Speech and Language Processing (3rd ed.)")
    assert book_snippet["is_content_accessible"] is True
    assert book_snippet["preview_type"] == "snippet"
    assert book_snippet["extracted_content"] is not None

    # Verify YouTube missing transcript handling (Requirement 3)
    yt_no_transcript = next(s for s in sources if s["title"] == "Deep Learning Lecture 12")
    assert yt_no_transcript["is_content_accessible"] is False
    assert yt_no_transcript["preview_type"] == "metadata_only"
    assert yt_no_transcript["extracted_content"] is None

    yt_transcript = next(s for s in sources if s["title"] == "Word Embeddings Explained Clearly")
    assert yt_transcript["is_content_accessible"] is True
    assert yt_transcript["preview_type"] == "transcript"
    assert yt_transcript["extracted_content"] is not None

    print("Pass: Normalization, citation tags, and accessibility guarantees verified.")


def test_deduplication():
    """Test deduplication when providers return duplicate URLs or identifiers."""
    print("\n--- [Test 2] Deduplication Verification ---")
    aggregator = ResearchAggregator(
        web_provider=MockWebProvider(),
        books_provider=MockBooksProvider(),
        youtube_provider=MockYouTubeProvider(should_fail=False)
    )

    duplicate_list = [
        {"source_type": "web", "title": "Duplicated Article", "url_or_identifier": "https://example.com/same-url/"},
        {"source_type": "web", "title": "Duplicated Article 2", "url_or_identifier": "https://example.com/same-url"},
        {"source_type": "web", "title": "Distinct Article", "url_or_identifier": "https://example.com/distinct"}
    ]
    deduped = aggregator._deduplicate_sources(duplicate_list)
    assert len(deduped) == 2
    assert deduped[0]["title"] == "Duplicated Article"
    assert deduped[1]["title"] == "Distinct Article"
    print(f"Pass: 3 candidates with trailing slash variance deduplicated down to {len(deduped)}.")


def test_provider_fault_isolation():
    """Test that a failure in YouTube provider does not destroy Web or Books results."""
    print("\n--- [Test 3] Provider Fault Isolation ---")
    failing_aggregator = ResearchAggregator(
        web_provider=MockWebProvider(),
        books_provider=MockBooksProvider(),
        youtube_provider=MockYouTubeProvider(should_fail=True)
    )

    result = asyncio.run(failing_aggregator.harvest("Neural Networks"))
    sources = result["sources"]
    errors = result["provider_errors"]

    print(f"Harvest count with YouTube failing: {len(sources)}")
    print(f"Recorded provider errors: {errors}")

    assert len(sources) == 4  # 2 web + 2 books
    assert "youtube" in errors
    assert "rate limit or network timeout" in errors["youtube"]
    assert "web" not in errors
    assert "books" not in errors
    print("Pass: YouTube failure isolated; Web and Books successfully harvested.")


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_sqlite_persistence():
    """Test persisting harvested sources to SQLite database."""
    print("\n--- [Test 4] SQLite Database Persistence ---")
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestSession()

    lesson_id = str(uuid.uuid4())
    test_lesson = Lesson(
        id=lesson_id,
        title="Vector Space Modeling",
        learning_objectives=["Explain TF-IDF and embeddings"],
        target_audience="Undergraduate",
        difficulty_level="Intermediate",
        estimated_duration_mins=45,
        status="DRAFT"
    )
    db.add(test_lesson)
    db.commit()

    aggregator = ResearchAggregator(
        web_provider=MockWebProvider(),
        books_provider=MockBooksProvider(),
        youtube_provider=MockYouTubeProvider(should_fail=False)
    )
    harvest_result = asyncio.run(aggregator.harvest(test_lesson.title))

    saved_records = aggregator.persist_sources(
        lesson_id=lesson_id,
        sources=harvest_result["sources"],
        db=db,
        replace_existing=True
    )

    # Re-query from database
    persisted = db.query(ResearchSource).filter(ResearchSource.lesson_id == lesson_id).order_by(ResearchSource.citation_tag.asc()).all()
    assert len(persisted) == 6
    print(f"Successfully saved and retrieved {len(persisted)} research sources for lesson {lesson_id}.")

    # Verify field integrity
    first_record = persisted[0]
    assert first_record.citation_tag == "[REF-1]"
    assert first_record.source_type == "web"
    assert first_record.is_content_accessible is True
    assert first_record.extracted_content is not None

    # Clean up test lesson
    db.delete(test_lesson)
    db.commit()
    db.close()
    print("Pass: SQLite persistence verified and test data cleaned up.")


if __name__ == "__main__":
    test_research_pipeline_deterministic()
    test_deduplication()
    test_provider_fault_isolation()
    test_sqlite_persistence()
    print("\n>>> ALL PHASE 2 RESEARCH PIPELINE TESTS PASSED! <<<")
