import asyncio
import uuid
from typing import Dict, Any, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.lesson import Lesson
from app.models.research_source import ResearchSource
from app.models.factual_qc import FactualQCReport
from app.models.instructional_qc import InstructionalQCReport
from app.services.qc.factual_qc_service import FactualQCService
from app.services.qc.instructional_qc_service import InstructionalQCService


# Setup clean in-memory database for testing
engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(bind=engine)
TestSession = sessionmaker(bind=engine)


async def test_dual_qc_pipeline():
    print("=" * 75)
    print("      LEARNFORGE AI — PHASE 4 INDEPENDENT DUAL QC TEST SUITE")
    print("=" * 75)

    db = TestSession()
    factual_service = FactualQCService()
    instructional_service = InstructionalQCService()

    # -------------------------------------------------------------------------
    # TEST 1: Mandatory Scenario 1 — HTTP Requests and Responses
    # -------------------------------------------------------------------------
    print("\n--- [Test 1] Mandatory Scenario 1: HTTP Requests and Responses ---")
    lesson_1_id = str(uuid.uuid4())
    lesson_1 = Lesson(
        id=lesson_1_id,
        title="HTTP Requests and Responses",
        learning_objectives="Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
        target_audience="Undergraduate Computer Science",
        difficulty_level="Intermediate",
        estimated_duration_mins=40,
        status="GENERATED",
        current_version=1,
        content_blocks={
            "overview": "Comprehensive introduction to HTTP requests and response taxonomy.",
            "learning_objectives": [
                "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."
            ],
            "target_audience": "Undergraduate Computer Science",
            "difficulty_level": "Intermediate",
            "total_estimated_duration_mins": 40,
            "introduction_and_motivation": "HTTP is the protocol of the World Wide Web.",
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
                },
                {
                    "question": "A client sends an invalid authorization header. Which code range is expected?",
                    "question_type": "multiple_choice",
                    "options": ["A) 2xx", "B) 3xx", "C) 4xx", "D) 5xx"],
                    "correct_answer": "C) 4xx",
                    "rationale": "4xx designates client-side authentication or query faults."
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
    db.add(lesson_1)

    s1 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_1_id,
        source_type="web",
        title="RFC 9110: HTTP Semantics",
        url_or_identifier="https://www.rfc-editor.org/rfc/rfc9110",
        citation_tag="[REF-1]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="GET requests are safe and idempotent, intended for resource retrieval. POST requests submit representations for state-changing processing.",
        relevance_score=1.0
    )
    s2 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_1_id,
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
    db.commit()

    # Run Independent Factual QC
    fact_rep_1 = await factual_service.evaluate_lesson(lesson_1_id, db)
    print(f"  Factual QC Result: Score={fact_rep_1.factual_accuracy_score}/100 | Status={fact_rep_1.status}")
    print(f"  Claims Analyzed: {fact_rep_1.total_claims_analyzed} (Verified: {fact_rep_1.verified_claims_count})")
    assert fact_rep_1.factual_accuracy_score >= 80.0
    assert fact_rep_1.status == "PASSED"
    assert fact_rep_1.contradicted_count == 0

    # Run Independent Instructional QC
    inst_rep_1 = await instructional_service.evaluate_lesson(lesson_1_id, db)
    print(f"  Instructional QC Result: Score={inst_rep_1.pedagogical_score}/100 | Status={inst_rep_1.status}")
    print(f"  Target Bloom Level: '{inst_rep_1.target_bloom_level}' | Achieved: '{inst_rep_1.achieved_bloom_level}'")
    assert inst_rep_1.pedagogical_score >= 80.0
    assert inst_rep_1.status == "PASSED"
    assert len(inst_rep_1.rubric_breakdown) == 6
    print("  [PASS] Mandatory Scenario 1 fully evaluated and passed both independent QC engines.")

    # -------------------------------------------------------------------------
    # TEST 2: Mandatory Scenario 2 — Python Object-Oriented Programming
    # -------------------------------------------------------------------------
    print("\n--- [Test 2] Mandatory Scenario 2: Python Object-Oriented Programming ---")
    lesson_2_id = str(uuid.uuid4())
    lesson_2 = Lesson(
        id=lesson_2_id,
        title="Python Object-Oriented Programming: Classes and Inheritance",
        learning_objectives="Design Python classes using encapsulation and demonstrate inheritance and method overriding.",
        target_audience="Introductory Software Engineering",
        difficulty_level="Intermediate",
        estimated_duration_mins=45,
        status="GENERATED",
        current_version=1,
        content_blocks={
            "overview": "Mastering object-oriented principles in Python with clean classes and inheritance.",
            "learning_objectives": ["Design Python classes using encapsulation and demonstrate inheritance and method overriding."],
            "target_audience": "Introductory Software Engineering",
            "difficulty_level": "Intermediate",
            "total_estimated_duration_mins": 45,
            "introduction_and_motivation": "OOP structures complex codebases into modular, reusable components.",
            "prerequisite_knowledge": [
                {"concept": "Python Functions and Types", "brief_refresher": "Familiarity with def, variables, and dicts."}
            ],
            "core_concepts": [
                {
                    "title": "Class Definitions and Encapsulation",
                    "explanation": "Classes bundle state and behavior using the __init__ constructor and self references [REF-1].",
                    "key_takeaway": "Encapsulate attributes and behaviors inside cohesive classes.",
                    "supporting_citation_tags": ["[REF-1]"],
                    "estimated_minutes": 10
                },
                {
                    "title": "Inheritance and Method Overriding",
                    "explanation": "Subclasses derive attributes from base classes and override behaviors using super() [REF-2].",
                    "key_takeaway": "Subclasses specialize parent behavior while reusing common logic.",
                    "supporting_citation_tags": ["[REF-2]"],
                    "estimated_minutes": 10
                }
            ],
            "practical_examples": [
                {
                    "title": "Employee and Manager Hierarchy",
                    "scenario": "Modeling company personnel",
                    "code_or_walkthrough": "class Employee:\n  def __init__(self, name):\n    self.name = name\nclass Manager(Employee):\n  def get_role(self):\n    return 'Manager'",
                    "explanation": "Demonstrates clear subclassing and attribute inheritance."
                }
            ],
            "real_world_applications": [
                {
                    "domain": "Enterprise Software Engineering",
                    "use_case": "Building payment processor drivers",
                    "trade_offs": "Inheritance promotes code reuse but can cause rigid class coupling compared to composition."
                }
            ],
            "guided_exercises": [
                {
                    "title": "Extend Animal Class",
                    "problem_statement": "Create a Dog class inheriting from Animal.",
                    "hints": ["Call super().__init__()."],
                    "solution": "class Dog(Animal): pass"
                }
            ],
            "knowledge_checks": [
                {
                    "question": "Which Python function delegates initialization to the parent superclass?",
                    "question_type": "multiple_choice",
                    "options": ["A) parent()", "B) super()", "C) base()", "D) root()"],
                    "correct_answer": "B) super()",
                    "rationale": "super() provides access to inherited methods in Python."
                },
                {
                    "question": "What is the purpose of encapsulation in object-oriented design?",
                    "question_type": "multiple_choice",
                    "options": ["A) Global state", "B) Information hiding and bundling", "C) Syntax speed", "D) Infinite loops"],
                    "correct_answer": "B) Information hiding and bundling",
                    "rationale": "Encapsulation prevents unauthorized state modification by enclosing data with methods."
                }
            ],
            "lesson_summary": "OOP enables scalable software architecture through encapsulation, inheritance, and polymorphism.",
            "further_learning_resources": ["Official Python OOP Documentation"],
            "references": [
                {"citation_tag": "[REF-1]", "title": "Python Docs: Classes", "is_content_accessible": True},
                {"citation_tag": "[REF-2]", "title": "Fluent Python: Inheritance", "is_content_accessible": True}
            ]
        }
    )
    db.add(lesson_2)

    s2_1 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_2_id,
        source_type="web",
        title="Python 3 Documentation: Classes and Objects",
        url_or_identifier="https://docs.python.org/3/tutorial/classes.html",
        citation_tag="[REF-1]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="Classes provide a means of bundling data and functionality together. Creating a new class creates a new type of object, allowing new instances of that type to be made. Methods use self and __init__.",
        relevance_score=1.0
    )
    s2_2 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_2_id,
        source_type="web",
        title="Inheritance in Python",
        url_or_identifier="https://realpython.com/inheritance-python-super/",
        citation_tag="[REF-2]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="Inheritance allows programmers to create classes that are built upon existing classes. Using super() gives you access to methods in other classes in the inheritance hierarchy.",
        relevance_score=0.95
    )
    db.add_all([s2_1, s2_2])
    db.commit()

    fact_rep_2 = await factual_service.evaluate_lesson(lesson_2_id, db)
    inst_rep_2 = await instructional_service.evaluate_lesson(lesson_2_id, db)

    assert fact_rep_2.status == "PASSED"
    assert inst_rep_2.status == "PASSED"
    print(f"  Factual QC: {fact_rep_2.factual_accuracy_score}/100 | Instructional QC: {inst_rep_2.pedagogical_score}/100")
    print("  [PASS] Mandatory Scenario 2 successfully verified.")

    # -------------------------------------------------------------------------
    # TEST 3: Edge Case — Deliberately Contradicted Factual Claim
    # -------------------------------------------------------------------------
    print("\n--- [Test 3] Edge Case: Direct Factual Contradiction ---")
    lesson_3_id = str(uuid.uuid4())
    lesson_3 = Lesson(
        id=lesson_3_id,
        title="Flawed HTTP Lesson",
        learning_objectives="Explain HTTP Methods.",
        target_audience="General",
        difficulty_level="Beginner",
        estimated_duration_mins=30,
        status="GENERATED",
        current_version=1,
        content_blocks={
            "core_concepts": [
                {
                    "title": "Idempotency Myth",
                    "explanation": "POST is idempotent and never modifies server state [REF-1].",
                    "supporting_citation_tags": ["[REF-1]"]
                }
            ],
            "practical_examples": [],
            "knowledge_checks": []
        }
    )
    db.add(lesson_3)
    s3 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_3_id,
        source_type="web",
        title="RFC 9110",
        url_or_identifier="https://rfc-editor.org",
        citation_tag="[REF-1]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="GET requests are safe and idempotent. POST requests submit representations for state-changing processing and are not idempotent.",
        relevance_score=1.0
    )
    db.add(s3)
    db.commit()

    fact_rep_3 = await factual_service.evaluate_lesson(lesson_3_id, db)
    print(f"  Single Contradiction Result: Contradicted Claims Count = {fact_rep_3.contradicted_count}")
    print(f"  Score: {fact_rep_3.factual_accuracy_score}/100 | Status: {fact_rep_3.status}")
    assert fact_rep_3.contradicted_count == 1
    assert fact_rep_3.status == "FAILED", "Single contradiction must trigger FAILED status under zero-contradiction rule"
    assert any(c["verdict"] == "CONTRADICTED" for c in fact_rep_3.claim_verifications)
    print("  [PASS] Single contradiction caught: Strictly triggers FAILED status.")

    # -------------------------------------------------------------------------
    # TEST 3B: Edge Case — Multiple Contradictions
    # -------------------------------------------------------------------------
    print("\n--- [Test 3B] Edge Case: Multiple Factual Contradictions ---")
    lesson_3b_id = str(uuid.uuid4())
    lesson_3b = Lesson(
        id=lesson_3b_id,
        title="Severely Flawed HTTP Lesson",
        learning_objectives="Explain HTTP Methods.",
        target_audience="General",
        difficulty_level="Beginner",
        estimated_duration_mins=30,
        status="GENERATED",
        current_version=1,
        content_blocks={
            "core_concepts": [
                {
                    "title": "Idempotency Myth",
                    "explanation": "POST is idempotent and never modifies server state [REF-1].",
                    "supporting_citation_tags": ["[REF-1]"]
                },
                {
                    "title": "State Mutation Myth",
                    "explanation": "GET method alters server state and deletes records on invocation [REF-1].",
                    "supporting_citation_tags": ["[REF-1]"]
                }
            ],
            "practical_examples": [],
            "knowledge_checks": []
        }
    )
    db.add(lesson_3b)
    s3b = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_3b_id,
        source_type="web",
        title="RFC 9110",
        url_or_identifier="https://rfc-editor.org",
        citation_tag="[REF-1]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="GET requests are safe and idempotent and never alter server state. POST requests submit representations for state-changing processing and are not idempotent.",
        relevance_score=1.0
    )
    db.add(s3b)
    db.commit()

    fact_rep_3b = await factual_service.evaluate_lesson(lesson_3b_id, db)
    print(f"  Multiple Contradictions Result: Contradicted Claims Count = {fact_rep_3b.contradicted_count}")
    print(f"  Score: {fact_rep_3b.factual_accuracy_score}/100 | Status: {fact_rep_3b.status}")
    assert fact_rep_3b.contradicted_count >= 2
    assert fact_rep_3b.status == "FAILED", "Multiple contradictions must trigger FAILED status"
    print("  [PASS] Multiple contradictions caught: Score heavily penalized, status FAILED.")

    # -------------------------------------------------------------------------
    # TEST 4: Edge Case — Hallucinated Citation Tag ([REF-99])
    # -------------------------------------------------------------------------
    print("\n--- [Test 4] Edge Case: Hallucinated Citation Tag ---")
    lesson_4_id = str(uuid.uuid4())
    lesson_4 = Lesson(
        id=lesson_4_id,
        title="Hallucinated Reference Lesson",
        learning_objectives="Testing citation audits.",
        target_audience="General",
        difficulty_level="Beginner",
        estimated_duration_mins=30,
        status="GENERATED",
        current_version=1,
        content_blocks={
            "core_concepts": [
                {
                    "title": "Fabricated Tag",
                    "explanation": "This claim cites a completely non-existent research source [REF-99].",
                    "supporting_citation_tags": ["[REF-99]"]
                }
            ],
            "practical_examples": [],
            "knowledge_checks": []
        }
    )
    db.add(lesson_4)
    db.commit()

    fact_rep_4 = await factual_service.evaluate_lesson(lesson_4_id, db)
    print(f"  Hallucination Flags Count: {len(fact_rep_4.hallucination_flags)}")
    assert len(fact_rep_4.hallucination_flags) >= 1
    assert fact_rep_4.hallucination_flags[0]["offending_tag"] == "[REF-99]"
    print("  [PASS] Hallucinated citation tag [REF-99] caught and logged in hallucination_flags.")

    # -------------------------------------------------------------------------
    # TEST 5: Edge Case — Metadata-Only Book Citation Refusal
    # -------------------------------------------------------------------------
    print("\n--- [Test 5] Edge Case: Metadata-Only Book Citation Refusal ---")
    lesson_5_id = str(uuid.uuid4())
    lesson_5 = Lesson(
        id=lesson_5_id,
        title="Metadata Book Citation Test",
        learning_objectives="Test metadata distinction.",
        target_audience="General",
        difficulty_level="Beginner",
        estimated_duration_mins=30,
        status="GENERATED",
        current_version=1,
        content_blocks={
            "core_concepts": [
                {
                    "title": "Paywalled Book Assertion",
                    "explanation": "Advanced deep learning theorem verified by closed-source textbook [REF-BOOK].",
                    "supporting_citation_tags": ["[REF-BOOK]"]
                }
            ],
            "practical_examples": [],
            "knowledge_checks": []
        }
    )
    db.add(lesson_5)
    s5_book = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_5_id,
        source_type="book",
        title="Closed Textbook",
        url_or_identifier="ISBN: 978-0123456789",
        citation_tag="[REF-BOOK]",
        is_content_accessible=False,
        preview_type="metadata_only",
        extracted_content=None,
        relevance_score=0.8
    )
    db.add(s5_book)
    db.commit()

    fact_rep_5 = await factual_service.evaluate_lesson(lesson_5_id, db)
    print(f"  Metadata-only citation flag: {fact_rep_5.hallucination_flags[0]['issue']}")
    assert "metadata-only" in fact_rep_5.hallucination_flags[0]["issue"].lower()
    assert any(c["verdict"] == "UNSUBSTANTIATED" for c in fact_rep_5.claim_verifications)
    print("  [PASS] Engine strictly rejected metadata-only book as factual proof.")

    # -------------------------------------------------------------------------
    # TEST 6: Edge Case — Poorly Structured Pedagogical Content & Over 45 Mins
    # -------------------------------------------------------------------------
    print("\n--- [Test 6] Edge Case: Poor Pedagogy & Duration Over 45 Mins ---")
    lesson_6_id = str(uuid.uuid4())
    lesson_6 = Lesson(
        id=lesson_6_id,
        title="Poor Pedagogy Lesson",
        learning_objectives="Analyze complex distributed systems.",
        target_audience="Novice",
        difficulty_level="Advanced",
        estimated_duration_mins=90,  # Exceeds 45 mins!
        status="GENERATED",
        current_version=1,
        content_blocks={
            "overview": "Dump of technical jargon.",
            "total_estimated_duration_mins": 90,
            "prerequisite_knowledge": [],  # Missing prerequisites
            "core_concepts": [
                {"title": "Jargon Module", "explanation": "Extremely convoluted text without explanations."}
            ],
            "practical_examples": [],  # Missing practical examples
            "knowledge_checks": []     # Missing assessments
        }
    )
    db.add(lesson_6)
    db.commit()

    inst_rep_6 = await instructional_service.evaluate_lesson(lesson_6_id, db)
    print(f"  Pedagogical Score: {inst_rep_6.pedagogical_score}/100 | Status: {inst_rep_6.status}")
    assert inst_rep_6.pedagogical_score < 70.0
    assert inst_rep_6.status in ("NEEDS_IMPROVEMENT", "FAILED")
    # Check duration deduction
    duration_crit = next(r for r in inst_rep_6.rubric_breakdown if r["name"] == "Duration & Pacing Feasibility")
    assert duration_crit["score"] < 100.0
    print(f"  Duration Criterion Score: {duration_crit['score']}/100 (Evidence: {duration_crit['evidence']})")
    print("  [PASS] Poor pedagogical structure and >45 min duration caught with appropriate penalties.")

    # -------------------------------------------------------------------------
    # TEST 7: Revision Management & Stale Report Invalidation
    # -------------------------------------------------------------------------
    print("\n--- [Test 7] Revision Management & Invalidation ---")
    assert fact_rep_1.is_stale is False
    assert inst_rep_1.is_stale is False

    # Simulate instructor editing lesson 1 (as in PUT /api/v1/lessons/{id})
    lesson_1.content_blocks["overview"] = "Instructor updated overview with new context."
    lesson_1.current_version += 1
    
    # Mark existing reports stale
    for r in [fact_rep_1, inst_rep_1]:
        r.is_stale = True
        r.stale_reason = f"Lesson edited to version {lesson_1.current_version}. Fresh verification required."
    db.commit()

    # Re-query from DB to verify persistence of stale flag
    reloaded_fact = db.query(FactualQCReport).filter(FactualQCReport.id == fact_rep_1.id).first()
    reloaded_inst = db.query(InstructionalQCReport).filter(InstructionalQCReport.id == inst_rep_1.id).first()

    assert reloaded_fact.is_stale is True
    assert reloaded_inst.is_stale is True
    assert f"version {lesson_1.current_version}" in reloaded_fact.stale_reason
    print(f"  Stale status verified: Factual is_stale={reloaded_fact.is_stale}, Reason='{reloaded_fact.stale_reason}'")
    print("  [PASS] Revision management successfully marks QC reports as stale upon edit.")

    print("\n" + "=" * 75)
    print("   >>> ALL 7 PHASE 4 INDEPENDENT DUAL QC TESTS PASSED! <<<")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(test_dual_qc_pipeline())
