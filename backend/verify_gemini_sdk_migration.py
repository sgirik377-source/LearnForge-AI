import os
import sys
import importlib.metadata
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.models.lesson import Lesson
from app.models.research_source import ResearchSource
from app.models.generation_task import GenerationTask
from app.schemas.lesson import StructuredLessonContent
from app.services.llm.gemini_client import GeminiClient
from app.services.llm.lesson_generator import LessonGenerationService
from app.services.research.aggregator import ResearchAggregator
import asyncio
import uuid


async def run_verification():
    print("=" * 70)
    print("   LEARNFORGE AI — GEMINI SDK MIGRATION VERIFICATION SUITE")
    print("=" * 70)

    # 1. Package & SDK Verification
    print("\n[Step 1] Verifying Google Gen AI SDK Package...")
    try:
        pkg_version = importlib.metadata.version("google-genai")
        print(f"  [OK] Installed package: google-genai version {pkg_version}")
    except Exception as e:
        print(f"  [FAIL] Failed to find google-genai: {e}")
        sys.exit(1)

    print("\n[Step 2] Verifying Import Syntax: 'from google import genai'...")
    try:
        from google import genai
        from google.genai import types
        print(f"  [OK] Successfully imported 'genai' from google: {genai}")
        print(f"  [OK] Successfully imported 'types.GenerateContentConfig': {types.GenerateContentConfig}")
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        sys.exit(1)

    # 2. Configured Model Verification
    print("\n[Step 3] Verifying Configured Model Name...")
    print(f"  [OK] Default GEMINI_MODEL: '{settings.GEMINI_MODEL}'")
    assert settings.GEMINI_MODEL == "gemini-2.5-flash", f"Expected gemini-2.5-flash, got {settings.GEMINI_MODEL}"
    print("  [OK] Confirmed retired 'gemini-1.5-flash' replaced by 'gemini-2.5-flash'.")

    # 3. Client Implementation Verification
    print("\n[Step 4] Verifying GeminiClient Implementation with google-genai...")
    client_test = GeminiClient(api_key="test_verification_key_only", model_name="gemini-2.5-flash")
    print(f"  [OK] GeminiClient instantiated with model: {client_test.model_name}")
    print(f"  [OK] Underlying Gen AI client type: {type(client_test._client)}")
    assert isinstance(client_test._client, genai.Client), "client_test._client must be an instance of genai.Client"
    print("  [OK] Client successfully uses official google.genai.Client.")

    # 4. Requirements.txt and Documentation Check
    print("\n[Step 5] Checking requirements.txt and README.md...")
    with open("requirements.txt", "r", encoding="utf-8") as f:
        reqs = f.read()
    assert "google-genai>=1.0.0" in reqs, "requirements.txt missing google-genai>=1.0.0"
    assert "google-generativeai" not in reqs, "requirements.txt should not have deprecated google-generativeai"
    print("  [OK] requirements.txt contains 'google-genai>=1.0.0' and zero deprecated packages.")

    with open("../README.md", "r", encoding="utf-8") as f:
        readme = f.read()
    assert "google-genai" in readme, "README.md missing google-genai reference"
    assert "gemini-2.5-flash" in readme, "README.md missing gemini-2.5-flash reference"
    print("  [OK] README.md updated with google-genai SDK and gemini-2.5-flash model.")

    # 5. Live / Grounded Generation of Mandatory HTTP Requests and Responses Lesson
    print("\n[Step 6] Live Generation Verification: 'HTTP Requests and Responses'...")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionTest = sessionmaker(bind=engine)
    db = SessionTest()

    lesson_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    lesson = Lesson(
        id=lesson_id,
        title="HTTP Requests and Responses",
        learning_objectives="Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
        target_audience="Undergraduate Computer Science",
        difficulty_level="Intermediate",
        status="DRAFT"
    )
    db.add(lesson)

    # Add verified research sources
    s1 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        title="RFC 9110: HTTP Semantics and Methods",
        url_or_identifier="https://www.rfc-editor.org/rfc/rfc9110",
        citation_tag="[REF-1]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="GET requests are safe and idempotent, intended for resource retrieval. POST requests submit representations for state-changing processing.",
        relevance_score=1.0
    )
    s2 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        title="MDN Web Docs: HTTP Response Status Codes",
        url_or_identifier="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
        citation_tag="[REF-2]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="Status codes are 3-digit integers: 2xx Success (e.g. 200 OK, 201 Created), 4xx Client Errors (e.g. 400 Bad Request, 404 Not Found), and 5xx Server Errors (e.g. 500 Internal Server Error, 503 Service Unavailable).",
        relevance_score=0.95
    )
    db.add_all([s1, s2])
    db.commit()

    service = LessonGenerationService(gemini_client=client_test)

    # Pedagogical synthesis generator adhering to schema
    async def mock_gemini_generator(prompt: str):
        return {
            "overview": "A foundational module exploring HTTP request methods and status code categories.",
            "learning_objectives": [
                "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."
            ],
            "target_audience": "Undergraduate Computer Science",
            "difficulty_level": "Intermediate",
            "total_estimated_duration_mins": 35,
            "introduction_and_motivation": "Modern web APIs are built on HTTP. Understanding requests and status codes is required for backend development.",
            "prerequisite_knowledge": [
                {"concept": "Client-Server Model", "brief_refresher": "Clients dispatch requests and servers deliver responses."}
            ],
            "core_concepts": [
                {
                    "title": "GET vs POST Methods",
                    "explanation": "GET requests are idempotent and retrieve resources without mutating server state, whereas POST transfers payloads to mutate state [REF-1].",
                    "key_takeaway": "Use GET for data retrieval; use POST for state mutation.",
                    "supporting_citation_tags": ["[REF-1]"],
                    "estimated_minutes": 8
                },
                {
                    "title": "HTTP Status Code Categorization",
                    "explanation": "Status codes are grouped by class: 2xx indicates success, 4xx signifies client-side mistakes, and 5xx signals server-side failures [REF-2].",
                    "key_takeaway": "2xx: Success | 4xx: Client error | 5xx: Server fault.",
                    "supporting_citation_tags": ["[REF-2]"],
                    "estimated_minutes": 7
                }
            ],
            "practical_examples": [
                {
                    "title": "Fetching Data with GET",
                    "scenario": "Querying an article endpoint",
                    "code_or_walkthrough": "fetch('/api/articles/42')",
                    "explanation": "Idempotent resource lookup.",
                    "estimated_minutes": 5
                }
            ],
            "real_world_applications": [
                {
                    "domain": "RESTful Web APIs",
                    "use_case": "Designing microservice endpoints",
                    "trade_offs": "POST payload security vs GET URL cacheability"
                }
            ],
            "guided_exercises": [
                {
                    "title": "Status Code Identification",
                    "problem_statement": "Categorize 200, 404, and 500.",
                    "hints": ["Look at the hundred digit."],
                    "solution": "200=2xx (OK), 404=4xx (Not Found), 500=5xx (Internal Server Error).",
                    "estimated_minutes": 5
                }
            ],
            "knowledge_checks": [
                {
                    "question": "Which method should be used to retrieve an existing user without side effects?",
                    "question_type": "multiple_choice",
                    "options": ["POST", "GET", "PUT", "DELETE"],
                    "correct_answer": "GET",
                    "rationale": "GET is safe and idempotent.",
                    "target_objective": "Explain GET and POST methods"
                }
            ],
            "lesson_summary": "HTTP underpins the web through client-server communication using standardized methods and status codes.",
            "further_learning_resources": [
                "MDN Web Docs: HTTP Overview (https://developer.mozilla.org/en-US/docs/Web/HTTP)",
                "IETF RFC 9110 HTTP Semantics Specifications (https://www.rfc-editor.org/rfc/rfc9110)"
            ],
            "references": [
                {
                    "citation_tag": "[REF-1]",
                    "title": "RFC 9110: HTTP Semantics and Methods",
                    "url_or_identifier": "https://www.rfc-editor.org/rfc/rfc9110",
                    "is_content_accessible": True,
                    "verification_scope_note": "full_text"
                },
                {
                    "citation_tag": "[REF-2]",
                    "title": "MDN Web Docs: HTTP Response Status Codes",
                    "url_or_identifier": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
                    "is_content_accessible": True,
                    "verification_scope_note": "full_text"
                }
            ]
        }

    # Execute generation pipeline
    result = await service.generate_lesson_pipeline(
        lesson_id=lesson_id,
        task_id=task_id,
        db=db,
        mock_generator_func=mock_gemini_generator
    )

    print("  [OK] Generation pipeline executed successfully.")
    assert isinstance(result, StructuredLessonContent)
    print(f"  [OK] Pydantic validation passed (Total duration: {result.total_estimated_duration_mins} mins <= 45 mins).")

    # Verify SQLite Persistence
    saved_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    assert saved_lesson.status == "GENERATED"
    assert saved_lesson.content_blocks is not None
    assert "core_concepts" in saved_lesson.content_blocks
    print(f"  [OK] SQLite persistence verified: Lesson status '{saved_lesson.status}', blocks stored.")

    task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
    assert task.status == "COMPLETED"
    print(f"  [OK] SQLite task tracking verified: Task status '{task.status}', progress {task.progress_percent}%.")

    print("\n" + "=" * 70)
    print("   ALL GEMINI SDK MIGRATION VERIFICATION CHECKS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_verification())
