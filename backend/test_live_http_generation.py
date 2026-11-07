"""
Test fresh, live, research-grounded lesson generation with Google Gemini.
Topic: HTTP Requests and Responses (Mandatory Scenario 1)
Validates live synthesis, Pydantic parsing, citation enforcement, duration constraint, and SQLite persistence.
"""

import asyncio
import uuid
import sys
from app.core.database import SessionLocal
from app.models.lesson import Lesson
from app.models.research_source import ResearchSource
from app.models.generation_task import GenerationTask
from app.services.llm.lesson_generator import LessonGenerationService
from app.services.llm.gemini_client import GeminiClient


async def test_live_http_generation():
    print("=" * 70)
    print("   LEARNFORGE AI — LIVE GEMINI LESSON GENERATION TEST")
    print("   Topic: HTTP Requests and Responses (Mandatory Scenario)")
    print("=" * 70)

    db = SessionLocal()
    lesson_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    try:
        # 1. Create Lesson record
        print("\n[1] Creating lesson draft in SQLite...")
        lesson = Lesson(
            id=lesson_id,
            title="HTTP Requests and Responses",
            learning_objectives=[
                "Explain the client-server request-response lifecycle and message syntax",
                "Distinguish between GET and POST method semantics and idempotency",
                "Classify HTTP response status codes into 2xx, 4xx, and 5xx categories"
            ],
            target_audience="Undergraduate Computer Science / Web Developers",
            difficulty_level="Intermediate",
            estimated_duration_mins=40,
            status="DRAFT",
            current_version=1,
            content_blocks={}
        )
        db.add(lesson)

        # 2. Attach authentic research sources from Phase 2 corpus
        print("[2] Attaching verified Phase 2 research corpus...")
        s1 = ResearchSource(
            id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            source_type="web",
            title="RFC 9110: HTTP Semantics and Request Methods",
            url_or_identifier="https://www.rfc-editor.org/rfc/rfc9110",
            citation_tag="[REF-1]",
            is_content_accessible=True,
            preview_type="full_text",
            extracted_content=(
                "HTTP is a stateless request-response protocol. The GET method requests transfer of a current selected "
                "representation for the target resource. GET is defined as safe and idempotent. The POST method requests "
                "that the target resource process the representation enclosed in the request body to perform resource-specific "
                "processing or state changes."
            ),
            relevance_score=1.0
        )
        s2 = ResearchSource(
            id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            source_type="web",
            title="RFC 9110: HTTP Response Status Codes and Semantics",
            url_or_identifier="https://www.rfc-editor.org/rfc/rfc9110#status.codes",
            citation_tag="[REF-2]",
            is_content_accessible=True,
            preview_type="full_text",
            extracted_content=(
                "The 3-digit status code indicates result of the attempt to understand and satisfy the request. "
                "2xx (Successful): The request was successfully received, understood, and accepted. "
                "4xx (Client Error): The client seems to have erred, such as syntax errors or unauthorized access. "
                "5xx (Server Error): The server failed to fulfill an apparently valid request."
            ),
            relevance_score=0.98
        )
        s3 = ResearchSource(
            id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            source_type="book",
            title="Data Communications and Networking (5th Edition)",
            url_or_identifier="ISBN: 9780073376226",
            citation_tag="[REF-3]",
            is_content_accessible=False,
            preview_type="metadata_only",
            extracted_content="",
            verification_scope_note="Behrouz Forouzan textbook. Bibliographic record.",
            relevance_score=0.85
        )
        db.add_all([s1, s2, s3])
        db.commit()
        print("    - Added [REF-1] (Web, Accessible full_text)")
        print("    - Added [REF-2] (Web, Accessible full_text)")
        print("    - Added [REF-3] (Book, Metadata-only bibliographic record)")

        # 3. Execute live lesson generation pipeline with Gemini
        print("\n[3] Triggering LessonGenerationService with live Gemini API...")
        client = GeminiClient()
        service = LessonGenerationService(gemini_client=client)

        structured_lesson = await service.generate_lesson_pipeline(
            lesson_id=lesson_id,
            task_id=task_id,
            db=db
        )

        # 4. Verify Synthesis Output
        print("\n[4] Validating Synthesized Lesson Structure:")
        print(f"    - Title: '{lesson.title}'")
        print(f"    - Overview: '{structured_lesson.overview[:100]}...'")
        print(f"    - Duration Allocated: {structured_lesson.total_estimated_duration_mins} mins (Max 45m)")
        assert structured_lesson.total_estimated_duration_mins <= 45, "Duration exceeded 45 minutes!"
        print(f"    - Core Concepts: {len(structured_lesson.core_concepts)} modules")
        assert len(structured_lesson.core_concepts) >= 2, "Expected at least 2 core concepts"
        for idx, concept in enumerate(structured_lesson.core_concepts, 1):
            print(f"      * Concept {idx}: '{concept.title}' ({concept.estimated_minutes}m) | Citations: {concept.supporting_citation_tags}")
        
        print(f"    - Practical Examples: {len(structured_lesson.practical_examples)}")
        print(f"    - Real-World Applications: {len(structured_lesson.real_world_applications)}")
        print(f"    - Guided Exercises: {len(structured_lesson.guided_exercises)}")
        print(f"    - Knowledge Checks: {len(structured_lesson.knowledge_checks)}")
        assert len(structured_lesson.knowledge_checks) >= 1, "Expected at least 1 knowledge check"

        # 5. Verify Persistence in SQLite
        print("\n[5] Verifying SQLite Database Persistence:")
        db.refresh(lesson)
        task = db.query(GenerationTask).filter_by(id=task_id).first()
        print(f"    - Lesson status in SQLite: {lesson.status}")
        assert lesson.status == "GENERATED", f"Expected GENERATED, got {lesson.status}"
        print(f"    - GenerationTask status in SQLite: {task.status}")
        assert task.status == "COMPLETED", f"Expected COMPLETED, got {task.status}"
        print(f"    - GenerationTask progress: {task.progress_percent}%")

        print("\n" + "=" * 70)
        print(">>> LIVE HTTP LESSON GENERATION TEST PASSED SUCCESSFULLY! <<<")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n[FAIL] Live lesson generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = asyncio.run(test_live_http_generation())
    if not success:
        sys.exit(1)
