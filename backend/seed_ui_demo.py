import uuid
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.lesson import Lesson
from app.models.research_source import ResearchSource
from app.models.factual_qc import FactualQCReport
from app.models.instructional_qc import InstructionalQCReport


def seed():
    db = SessionLocal()
    try:
        # Clear existing test lessons if needed
        # Create Lesson 1: HTTP Requests and Responses
        l1_id = "http-demo-lesson-1"
        existing = db.query(Lesson).filter(Lesson.id == l1_id).first()
        if existing:
            db.delete(existing)
            db.commit()

        l1 = Lesson(
            id=l1_id,
            title="HTTP Requests and Responses",
            learning_objectives=["Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."],
            target_audience="Undergraduate Computer Science",
            difficulty_level="Intermediate",
            estimated_duration_mins=40,
            status="GENERATED",
            current_version=1,
            content_blocks={
                "overview": "A foundational module exploring the Hypertext Transfer Protocol (HTTP), distinguishing request methods and response status codes.",
                "learning_objectives": ["Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."],
                "target_audience": "Undergraduate Computer Science",
                "difficulty_level": "Intermediate",
                "total_estimated_duration_mins": 40,
                "introduction_and_motivation": "Every web interaction relies on HTTP. Mastering requests and status codes is essential for building and debugging APIs.",
                "prerequisite_knowledge": [
                    {"concept": "Client-Server Architecture", "brief_refresher": "Clients initiate queries; servers respond."}
                ],
                "core_concepts": [
                    {
                        "title": "HTTP Methods: GET vs POST Semantics",
                        "explanation": "GET requests are idempotent and retrieve data via URL parameters, whereas POST transmits payloads to mutate state [REF-1].",
                        "key_takeaway": "GET is safe/idempotent; POST mutates server state.",
                        "supporting_citation_tags": ["[REF-1]"],
                        "estimated_minutes": 8
                    },
                    {
                        "title": "Response Status Code Taxonomy",
                        "explanation": "HTTP status codes categorize responses: 2xx represents success, 4xx signals client-side errors, and 5xx indicates server-side faults [REF-2].",
                        "key_takeaway": "2xx=OK, 4xx=Client Error, 5xx=Server Fault.",
                        "supporting_citation_tags": ["[REF-2]"],
                        "estimated_minutes": 7
                    }
                ],
                "practical_examples": [
                    {
                        "title": "Fetching Data via GET",
                        "scenario": "User profile retrieval",
                        "code_or_walkthrough": "fetch('/api/user/101', { method: 'GET' })",
                        "explanation": "Demonstrates idempotent read without mutating database state."
                    }
                ],
                "real_world_applications": [
                    {
                        "domain": "RESTful Microservices",
                        "use_case": "Order checkout processing",
                        "trade_offs": "POST payload security vs GET URL cacheability."
                    }
                ],
                "guided_exercises": [
                    {
                        "title": "Classify Status Codes",
                        "problem_statement": "Categorize 201, 404, 500.",
                        "hints": ["Check first digit."],
                        "solution": "201=2xx, 404=4xx, 500=5xx."
                    }
                ],
                "knowledge_checks": [
                    {
                        "question": "Which HTTP method should be used for read-only operations without side effects?",
                        "question_type": "multiple_choice",
                        "options": ["A) POST", "B) GET", "C) PATCH", "D) PUT"],
                        "correct_answer": "B) GET",
                        "rationale": "GET is defined as safe and idempotent for retrieving resources."
                    }
                ],
                "lesson_summary": "HTTP standardizes client-server interactions with explicit request methods and status taxonomy.",
                "further_learning_resources": ["RFC 9110 Standards"],
                "references": [
                    {"citation_tag": "[REF-1]", "title": "RFC 9110 HTTP Semantics", "is_content_accessible": True},
                    {"citation_tag": "[REF-2]", "title": "MDN Status Codes", "is_content_accessible": True}
                ]
            }
        )
        db.add(l1)

        s1 = ResearchSource(
            id=str(uuid.uuid4()),
            lesson_id=l1_id,
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
            lesson_id=l1_id,
            source_type="web",
            title="MDN Web Docs: Status Codes",
            url_or_identifier="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
            citation_tag="[REF-2]",
            is_content_accessible=True,
            preview_type="full_text",
            extracted_content="2xx indicates success. 4xx indicates client error such as malformed requests. 5xx indicates server failure.",
            relevance_score=0.95
        )
        db.add_all([s1, s2])

        # Factual QC Report
        fact_1 = FactualQCReport(
            id=str(uuid.uuid4()),
            lesson_id=l1_id,
            lesson_version=1,
            status="PASSED",
            factual_accuracy_score=100.0,
            claim_verification_rate=100.0,
            citation_fidelity_score=100.0,
            hallucination_penalty=0.0,
            total_claims_analyzed=4,
            verified_claims_count=4,
            partially_supported_count=0,
            unsubstantiated_count=0,
            contradicted_count=0,
            claim_verifications=[
                {
                    "claim": "GET requests are idempotent and retrieve data via URL parameters [REF-1].",
                    "verdict": "VERIFIED",
                    "evidence_quote": "GET requests are safe and idempotent, intended for resource retrieval. POST requests submit representations for state-changing processing.",
                    "source_reference_tag": "[REF-1]",
                    "confidence_score": 0.98,
                    "recommended_correction": None
                },
                {
                    "claim": "POST transmits payloads to mutate state [REF-1].",
                    "verdict": "VERIFIED",
                    "evidence_quote": "POST requests submit representations for state-changing processing.",
                    "source_reference_tag": "[REF-1]",
                    "confidence_score": 0.96,
                    "recommended_correction": None
                },
                {
                    "claim": "HTTP status codes categorize responses: 2xx represents success [REF-2].",
                    "verdict": "VERIFIED",
                    "evidence_quote": "2xx indicates success. 4xx indicates client error such as malformed requests. 5xx indicates server failure.",
                    "source_reference_tag": "[REF-2]",
                    "confidence_score": 0.95,
                    "recommended_correction": None
                },
                {
                    "claim": "4xx signals client-side errors, and 5xx indicates server-side faults [REF-2].",
                    "verdict": "VERIFIED",
                    "evidence_quote": "4xx indicates client error such as malformed requests. 5xx indicates server failure.",
                    "source_reference_tag": "[REF-2]",
                    "confidence_score": 0.95,
                    "recommended_correction": None
                }
            ],
            hallucination_flags=[],
            missing_citations=[],
            executive_summary="Factual QC Audit confirmed 100% verification fidelity. All 4 claims are strictly substantiated by RFC 9110 and MDN documentation.",
            recommended_corrections=[],
            is_stale=False,
            stale_reason=None,
            generated_at=datetime.now(timezone.utc)
        )
        db.add(fact_1)

        # Instructional QC Report
        inst_1 = InstructionalQCReport(
            id=str(uuid.uuid4()),
            lesson_id=l1_id,
            lesson_version=1,
            status="PASSED",
            pedagogical_score=87.0,
            bloom_alignment_score=94.0,
            clarity_score=90.0,
            scaffolding_score=92.0,
            assessment_fidelity_score=93.0,
            engagement_score=85.0,
            target_bloom_level="Understand",
            achieved_bloom_level="Understand",
            bloom_verb_analysis={"target": "Understand", "achieved": "Understand"},
            rubric_breakdown=[
                {
                    "name": "Learning Objective Alignment",
                    "weight": 0.25,
                    "score": 95.0,
                    "description": "Evaluates coverage of stated learning goals across content modules.",
                    "evidence": "Strong alignment: Core modules cover GET/POST methods and 2xx/4xx/5xx status taxonomy."
                },
                {
                    "name": "Cognitive Scaffolding & Prerequisites",
                    "weight": 0.20,
                    "score": 92.0,
                    "description": "Reviews prerequisite refreshers and progressive concept complexity.",
                    "evidence": "Includes prerequisite refresher on client-server architecture and builds from methods to status codes."
                },
                {
                    "name": "Bloom's Revised Taxonomy Alignment",
                    "weight": 0.15,
                    "score": 94.0,
                    "description": "Assesses cognitive depth consistency between objectives and assessments.",
                    "evidence": "Target Bloom level (Understand) matched by formative assessment checkpoints."
                },
                {
                    "name": "Practical Examples & Real-World Grounding",
                    "weight": 0.15,
                    "score": 90.0,
                    "description": "Evaluates code snippets, scenarios, and trade-off considerations.",
                    "evidence": "Demonstrates GET fetch query and discusses POST caching vs URL security trade-offs."
                },
                {
                    "name": "Assessment & Knowledge Check Coherence",
                    "weight": 0.15,
                    "score": 93.0,
                    "description": "Reviews question quality, distractor plausibility, and answer rationales.",
                    "evidence": "Knowledge check includes multiple-choice question with 4 distinct options and conceptual rationale."
                },
                {
                    "name": "Duration & Pacing Feasibility",
                    "weight": 0.10,
                    "score": 100.0,
                    "description": "Ensures total learning duration respects cognitive load limits (<= 45 mins).",
                    "evidence": "Total estimated duration of 40 minutes strictly satisfies the <= 45-minute ceiling."
                }
            ],
            strengths=[
                "Exceptional alignment between RFC 9110 specifications and core conceptual definitions.",
                "Cognitive scaffolding clearly differentiates safe/idempotent queries from state-mutating requests."
            ],
            actionable_improvements=[
                "Consider adding a curl command walkthrough alongside fetch for backend CLI clarity."
            ],
            executive_summary="Pedagogical design verified. The lesson exhibits cohesive scaffolding, active retrieval checkpoints, and strictly respects the 45-minute duration limit.",
            is_stale=False,
            stale_reason=None,
            generated_at=datetime.now(timezone.utc)
        )
        db.add(inst_1)

        # Create Lesson 2: Stale QC Demo Lesson
        l2_id = "stale-qc-demo-lesson-2"
        existing2 = db.query(Lesson).filter(Lesson.id == l2_id).first()
        if existing2:
            db.delete(existing2)
            db.commit()

        l2 = Lesson(
            id=l2_id,
            title="Python Object-Oriented Programming (Instructor Edited)",
            learning_objectives=["Design Python classes with inheritance and method overriding."],
            target_audience="Software Engineering Students",
            difficulty_level="Intermediate",
            estimated_duration_mins=45,
            status="EDITED_PENDING_QC",
            current_version=2,
            content_blocks={
                "overview": "Module updated with new advanced composition examples.",
                "total_estimated_duration_mins": 45,
                "core_concepts": [
                    {"title": "Classes and Inheritance", "explanation": "Classes bundle state and behavior.", "supporting_citation_tags": []}
                ]
            }
        )
        db.add(l2)

        fact_2 = FactualQCReport(
            id=str(uuid.uuid4()),
            lesson_id=l2_id,
            lesson_version=1,
            status="PASSED",
            factual_accuracy_score=90.0,
            claim_verification_rate=90.0,
            citation_fidelity_score=90.0,
            hallucination_penalty=0.0,
            total_claims_analyzed=3,
            verified_claims_count=3,
            partially_supported_count=0,
            unsubstantiated_count=0,
            contradicted_count=0,
            claim_verifications=[],
            hallucination_flags=[],
            missing_citations=[],
            executive_summary="Previous version 1 audit passed.",
            recommended_corrections=[],
            is_stale=True,
            stale_reason="Lesson edited to version 2. Fresh verification required before presenting as fully reviewed.",
            generated_at=datetime.now(timezone.utc)
        )
        db.add(fact_2)

        inst_2 = InstructionalQCReport(
            id=str(uuid.uuid4()),
            lesson_id=l2_id,
            lesson_version=1,
            status="PASSED",
            pedagogical_score=85.0,
            bloom_alignment_score=85.0,
            clarity_score=85.0,
            scaffolding_score=85.0,
            assessment_fidelity_score=85.0,
            engagement_score=85.0,
            target_bloom_level="Apply",
            achieved_bloom_level="Apply",
            bloom_verb_analysis={},
            rubric_breakdown=[],
            strengths=[],
            actionable_improvements=[],
            executive_summary="Previous version 1 audit passed.",
            is_stale=True,
            stale_reason="Lesson edited to version 2. Fresh evaluation required before presenting as fully reviewed.",
            generated_at=datetime.now(timezone.utc)
        )
        db.add(inst_2)

        db.commit()
        print("Seed complete: HTTP Requests & Responses (Passed QC) and Python OOP (Stale QC) inserted.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
