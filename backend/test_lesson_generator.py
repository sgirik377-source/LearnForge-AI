import asyncio
import uuid
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.lesson import Lesson
from app.models.research_source import ResearchSource
from app.models.generation_task import GenerationTask
from app.schemas.lesson import StructuredLessonContent
from app.services.llm.lesson_generator import LessonGenerationService
from app.services.research.aggregator import ResearchAggregator


# =========================================================================
# Mock Gemini Responses for Deterministic Automated Testing
# =========================================================================

async def mock_gemini_http_lesson(prompt: str) -> Dict[str, Any]:
    """Mock Gemini response for Test 1: HTTP Requests and Responses."""
    return {
        "overview": "A foundational module exploring the Hypertext Transfer Protocol (HTTP), distinguishing request methods and response status codes.",
        "learning_objectives": [
            "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."
        ],
        "target_audience": "Undergraduate Computer Science",
        "difficulty_level": "Intermediate",
        "total_estimated_duration_mins": 40,
        "introduction_and_motivation": "Every web interaction relies on HTTP. Mastering requests and status codes is essential for building and debugging APIs.",
        "prerequisite_knowledge": [
            {"concept": "Client-Server Architecture", "brief_refresher": "Clients initiate communication and servers reply with resources."},
            {"concept": "Basic Networking", "brief_refresher": "IP addresses and TCP connections establish reliable streams."}
        ],
        "core_concepts": [
            {
                "title": "HTTP Methods: GET vs POST Semantics",
                "explanation": "GET requests are idempotent and retrieve data via URL query parameters, whereas POST transmits payloads in the request body to mutate state [REF-1].",
                "key_takeaway": "GET retrieves data without side effects; POST sends data to be processed.",
                "supporting_citation_tags": ["[REF-1]"],
                "estimated_minutes": 8
            },
            {
                "title": "Response Status Code Taxonomy",
                "explanation": "HTTP responses use 3-digit status codes: 2xx represents success, 4xx signals client-side errors, and 5xx indicates server-side faults [REF-2].",
                "key_takeaway": "2xx = OK, 4xx = Client mistake (e.g. 404), 5xx = Server crash (e.g. 500).",
                "supporting_citation_tags": ["[REF-2]"],
                "estimated_minutes": 7
            }
        ],
        "practical_examples": [
            {
                "title": "Inspecting a GET Request with Fetch",
                "scenario": "Querying a user profile endpoint",
                "code_or_walkthrough": "fetch('/api/users/123', { method: 'GET' })\n  .then(res => res.json())\n  .then(data => console.log(data));",
                "explanation": "Demonstrates sending a standard idempotent query and handling JSON.",
                "estimated_minutes": 5
            },
            {
                "title": "Submitting a Form with POST",
                "scenario": "Creating a new user account with JSON payload",
                "code_or_walkthrough": "fetch('/api/users', {\n  method: 'POST',\n  headers: { 'Content-Type': 'application/json' },\n  body: JSON.stringify({ name: 'Alice' })\n});",
                "explanation": "Demonstrates placing state mutations inside the HTTP body.",
                "estimated_minutes": 5
            }
        ],
        "real_world_applications": [
            {
                "domain": "RESTful API Engineering",
                "use_case": "Designing microservices for e-commerce checkouts",
                "trade_offs": "POST provides payload security over URLs but prevents caching compared to GET."
            },
            {
                "domain": "Web Application Security",
                "use_case": "Preventing accidental duplicate billing on payment retries",
                "trade_offs": "Using idempotency tokens alongside POST to guard against network timeouts."
            }
        ],
        "guided_exercises": [
            {
                "title": "Exercise 1: Classify HTTP Status Codes",
                "problem_statement": "Categorize the following codes: 201, 401, 404, 502, 503.",
                "hints": ["Check the first digit to determine success, client error, or server fault."],
                "solution": "201 is 2xx (Success: Created). 401 and 404 are 4xx (Client Error: Unauthorized, Not Found). 502 and 503 are 5xx (Server Error: Bad Gateway, Service Unavailable).",
                "estimated_minutes": 5
            }
        ],
        "knowledge_checks": [
            {
                "question": "Which HTTP method should be used to retrieve an existing article without modifying server state?",
                "question_type": "multiple_choice",
                "options": ["A) POST", "B) GET", "C) DELETE", "D) PATCH"],
                "correct_answer": "B) GET",
                "rationale": "GET is defined in RFC standards as safe and idempotent for resource retrieval.",
                "target_objective": "Explain GET and POST methods"
            },
            {
                "question": "An API client sends a malformed JSON payload. Which status code range must the server return?",
                "question_type": "multiple_choice",
                "options": ["A) 2xx Success", "B) 3xx Redirection", "C) 4xx Client Error", "D) 5xx Server Error"],
                "correct_answer": "C) 4xx Client Error (specifically 400 Bad Request)",
                "rationale": "Client syntax errors are categorized under 4xx.",
                "target_objective": "Distinguish between 2xx, 4xx, and 5xx categories"
            }
        ],
        "lesson_summary": "HTTP forms the backbone of web systems. Understanding GET vs POST semantics and 2xx/4xx/5xx status ranges ensures robust client-server communication.",
        "further_learning_resources": [
            "RFC 9110: HTTP Semantics",
            "MDN Web Docs: An Overview of HTTP"
        ],
        "references": [
            {
                "citation_tag": "[REF-1]",
                "title": "HTTP Methods Specification",
                "url_or_identifier": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods",
                "is_content_accessible": True,
                "verification_scope_note": "Verified web documentation."
            },
            {
                "citation_tag": "[REF-2]",
                "title": "HTTP Status Code Registry",
                "url_or_identifier": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
                "is_content_accessible": True,
                "verification_scope_note": "Verified web documentation."
            }
        ]
    }


async def mock_gemini_python_oop_lesson(prompt: str) -> Dict[str, Any]:
    """Mock Gemini response for Test 2: Python Object-Oriented Programming."""
    return {
        "overview": "A practical exploration of Python Object-Oriented Programming, covering class modeling, instantiation, and inheritance.",
        "learning_objectives": [
            "Explain classes and objects in Python and demonstrate inheritance with practical programming examples."
        ],
        "target_audience": "Undergraduate Software Engineering",
        "difficulty_level": "Intermediate",
        "total_estimated_duration_mins": 45,
        "introduction_and_motivation": "OOP enables software modularity and code reuse. Python treats everything as an object, making OOP central to its ecosystem.",
        "prerequisite_knowledge": [
            {"concept": "Python Functions and Scope", "brief_refresher": "Understanding parameter passing and variable scope."},
            {"concept": "Data Types and Dictionaries", "brief_refresher": "Familiarity with key-value mappings and references."}
        ],
        "core_concepts": [
            {
                "title": "Classes vs Objects in Python",
                "explanation": "A class defines a blueprint with attributes and methods, while an object is a concrete instance in memory instantiated with `__init__` [REF-1].",
                "key_takeaway": "Class = Blueprint; Object = Living instance.",
                "supporting_citation_tags": ["[REF-1]"],
                "estimated_minutes": 8
            },
            {
                "title": "Inheritance and Method Overriding",
                "explanation": "Inheritance allows child classes to derive attributes and behaviors from parent classes, invoking parent initializers using `super()` [REF-2].",
                "key_takeaway": "`class Child(Parent):` establishes an 'is-a' relationship.",
                "supporting_citation_tags": ["[REF-2]"],
                "estimated_minutes": 8
            }
        ],
        "practical_examples": [
            {
                "title": "Defining a Class with Constructor",
                "scenario": "Modeling a Bank Account",
                "code_or_walkthrough": "class BankAccount:\n    def __init__(self, owner, balance=0):\n        self.owner = owner\n        self.balance = balance\n\n    def deposit(self, amount):\n        self.balance += amount\n        return self.balance",
                "explanation": "Shows encapsulation of state and behavior inside a class.",
                "estimated_minutes": 7
            },
            {
                "title": "Demonstrating Single Inheritance with super()",
                "scenario": "Creating a SavingsAccount child class",
                "code_or_walkthrough": "class SavingsAccount(BankAccount):\n    def __init__(self, owner, balance=0, interest_rate=0.03):\n        super().__init__(owner, balance)\n        self.interest_rate = interest_rate\n\n    def apply_interest(self):\n        self.balance += self.balance * self.interest_rate\n        return self.balance",
                "explanation": "Demonstrates reusing parent initialization and adding specialized logic.",
                "estimated_minutes": 7
            }
        ],
        "real_world_applications": [
            {
                "domain": "Game Development",
                "use_case": "Modeling Character hierarchies (Player, NPC, Boss deriving from Entity)",
                "trade_offs": "Deep inheritance hierarchies can lead to fragile base class problems."
            },
            {
                "domain": "GUI Frameworks (e.g. PyQt / Tkinter)",
                "use_case": "Custom widgets subclassing base window components",
                "trade_offs": "Inheritance provides clear lifecycle hooks but requires strict signature compatibility."
            }
        ],
        "guided_exercises": [
            {
                "title": "Exercise 1: Implement an Animal Hierarchy",
                "problem_statement": "Create a base class `Vehicle` with `drive()`, and a subclass `ElectricCar` with `charge()`.",
                "hints": ["Remember to call `super().__init__()` if overriding constructor."],
                "solution": "class Vehicle:\n    def drive(self): return 'Vroom'\nclass ElectricCar(Vehicle):\n    def charge(self): return 'Charging battery'",
                "estimated_minutes": 6
            }
        ],
        "knowledge_checks": [
            {
                "question": "What is the purpose of `self` in Python instance methods?",
                "question_type": "multiple_choice",
                "options": [
                    "A) Refers to the global module",
                    "B) Explicit reference to the specific instance calling the method",
                    "C) Declares a private variable",
                    "D) Points to the parent class"
                ],
                "correct_answer": "B) Explicit reference to the specific instance calling the method",
                "rationale": "Python automatically passes the instance as the first argument to method calls.",
                "target_objective": "Explain classes and objects in Python"
            },
            {
                "question": "How does a child class invoke its parent class's constructor in Python 3?",
                "question_type": "multiple_choice",
                "options": [
                    "A) parent.__init__()",
                    "B) this.__super__()",
                    "C) super().__init__(*args)",
                    "D) base.init()"
                ],
                "correct_answer": "C) super().__init__(*args)",
                "rationale": "`super()` delegates method calls to the parent in the method resolution order (MRO).",
                "target_objective": "Demonstrate inheritance with practical programming examples"
            }
        ],
        "lesson_summary": "Classes and objects bundle state and behavior. Inheritance fosters clean code reuse through hierarchical specialization.",
        "further_learning_resources": [
            "Official Python Tutorial: Classes",
            "Fluent Python (O'Reilly) - Chapter on Object References"
        ],
        "references": [
            {
                "citation_tag": "[REF-1]",
                "title": "Python Object-Oriented Documentation",
                "url_or_identifier": "https://docs.python.org/3/tutorial/classes.html",
                "is_content_accessible": True,
                "verification_scope_note": "Official Python 3 documentation."
            },
            {
                "citation_tag": "[REF-2]",
                "title": "Inheritance in Python",
                "url_or_identifier": "https://realpython.com/inheritance-python-super/",
                "is_content_accessible": True,
                "verification_scope_note": "Verified tutorial guide."
            }
        ]
    }


# =========================================================================
# Test Suite
# =========================================================================

def setup_test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


def test_mandatory_case_1_http():
    """TEST 1: HTTP Requests and Responses."""
    print("\n--- [Phase 3 Test 1] Mandatory Scenario: HTTP Requests and Responses ---")
    db = setup_test_db()

    lesson_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    lesson = Lesson(
        id=lesson_id,
        title="HTTP Requests and Responses",
        learning_objectives=[
            "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."
        ],
        target_audience="Undergraduate Computer Science",
        difficulty_level="Intermediate",
        estimated_duration_mins=45,
        status="DRAFT"
    )
    db.add(lesson)

    # Attach two research sources
    src1 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        citation_tag="[REF-1]",
        title="HTTP Methods Specification",
        url_or_identifier="https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="GET requests are safe and idempotent. POST requests submit entity data to mutate state.",
        accessible_text_length=85.0
    )
    src2 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        citation_tag="[REF-2]",
        title="HTTP Status Code Registry",
        url_or_identifier="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="2xx indicates success. 4xx indicates client errors like 404. 5xx indicates server errors.",
        accessible_text_length=85.0
    )
    db.add(src1)
    db.add(src2)
    db.commit()

    service = LessonGenerationService()
    structured = asyncio.run(service.generate_lesson_pipeline(
        lesson_id=lesson_id,
        task_id=task_id,
        db=db,
        mock_generator_func=mock_gemini_http_lesson
    ))

    # Assertions
    assert structured.overview != ""
    assert len(structured.learning_objectives) == 1
    assert "GET and POST" in structured.learning_objectives[0]
    assert len(structured.core_concepts) >= 2
    assert len(structured.practical_examples) >= 2
    assert len(structured.guided_exercises) >= 1
    assert len(structured.knowledge_checks) >= 2
    assert structured.total_estimated_duration_mins <= 45

    # Check citation validation
    for concept in structured.core_concepts:
        for tag in concept.supporting_citation_tags:
            assert tag in ["[REF-1]", "[REF-2]"]

    # Verify SQLite persistence
    refreshed_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    assert refreshed_lesson.status == "GENERATED"
    assert refreshed_lesson.content_blocks["total_estimated_duration_mins"] <= 45

    refreshed_task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
    assert refreshed_task.status == "COMPLETED"
    assert refreshed_task.progress_percent == 100

    print("Pass: Scenario 1 generated, structured, duration <= 45m, and saved in SQLite.")


def test_mandatory_case_2_python_oop():
    """TEST 2: Python Object-Oriented Programming."""
    print("\n--- [Phase 3 Test 2] Mandatory Scenario: Python Object-Oriented Programming ---")
    db = setup_test_db()

    lesson_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    lesson = Lesson(
        id=lesson_id,
        title="Python Object-Oriented Programming",
        learning_objectives=[
            "Explain classes and objects in Python and demonstrate inheritance with practical programming examples."
        ],
        target_audience="Undergraduate Software Engineering",
        difficulty_level="Intermediate",
        estimated_duration_mins=45,
        status="DRAFT"
    )
    db.add(lesson)

    src1 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        citation_tag="[REF-1]",
        title="Python Classes Tutorial",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="Classes provide a means of bundling data and functionality together.",
        accessible_text_length=70.0
    )
    src2 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        citation_tag="[REF-2]",
        title="Inheritance and Super",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="Inheritance allows subclasses to reuse and extend superclass implementations.",
        accessible_text_length=75.0
    )
    db.add(src1)
    db.add(src2)
    db.commit()

    service = LessonGenerationService()
    structured = asyncio.run(service.generate_lesson_pipeline(
        lesson_id=lesson_id,
        task_id=task_id,
        db=db,
        mock_generator_func=mock_gemini_python_oop_lesson
    ))

    # Assertions
    assert "Python" in structured.overview
    assert len(structured.core_concepts) >= 2
    assert len(structured.practical_examples) >= 2
    assert "class SavingsAccount" in structured.practical_examples[1].code_or_walkthrough
    assert structured.total_estimated_duration_mins <= 45

    # Check persistence
    saved_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    assert saved_lesson.status == "GENERATED"
    assert "core_concepts" in saved_lesson.content_blocks

    print("Pass: Scenario 2 generated, inheritance demonstrated, and persisted in SQLite.")


def test_invalid_gemini_response_handling():
    """Verify robust error handling and task state update on invalid Gemini output."""
    print("\n--- [Phase 3 Test 3] Error Handling on Invalid Gemini Output ---")
    db = setup_test_db()

    lesson_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    lesson = Lesson(
        id=lesson_id,
        title="Faulty Output Test",
        learning_objectives=["Testing error boundaries"],
        status="DRAFT"
    )
    db.add(lesson)
    db.commit()

    async def mock_faulty_generator(prompt: str):
        # Missing required sections
        return {"garbage": True}

    service = LessonGenerationService()

    try:
        asyncio.run(service.generate_lesson_pipeline(
            lesson_id=lesson_id,
            task_id=task_id,
            db=db,
            mock_generator_func=mock_faulty_generator
        ))
        assert False, "Should have thrown a validation exception"
    except Exception as e:
        print(f"Caught expected validation error: {e}")

    task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
    assert task.status == "FAILED"
    assert task.error_message is not None
    print("Pass: Handled invalid Gemini output cleanly; task marked FAILED in SQLite.")


def test_hallucinated_citation_stripping():
    """Verify that hallucinated citation tags are stripped or corrected."""
    print("\n--- [Phase 3 Test 4] Citation Integrity Enforcement ---")
    db = setup_test_db()

    lesson_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    lesson = Lesson(
        id=lesson_id,
        title="Citation Stripping Test",
        learning_objectives=["Testing citation verification"],
        status="DRAFT"
    )
    db.add(lesson)

    # Only [REF-1] exists in DB and is accessible; [REF-2] is metadata only
    src1 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        citation_tag="[REF-1]",
        title="Accessible Source",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="Real accessible evidence"
    )
    src2 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="book",
        citation_tag="[REF-2]",
        title="Inaccessible Book",
        is_content_accessible=False,
        preview_type="metadata_only",
        extracted_content=None
    )
    db.add(src1)
    db.add(src2)
    db.commit()

    async def mock_hallucinating_generator(prompt: str):
        base = await mock_gemini_http_lesson(prompt)
        # Attempt to cite non-existent [REF-99] and inaccessible [REF-2]
        base["core_concepts"][0]["supporting_citation_tags"] = ["[REF-1]", "[REF-99]", "[REF-2]"]
        return base

    service = LessonGenerationService()
    structured = asyncio.run(service.generate_lesson_pipeline(
        lesson_id=lesson_id,
        task_id=task_id,
        db=db,
        mock_generator_func=mock_hallucinating_generator
    ))

    # [REF-99] (hallucinated) and [REF-2] (metadata-only) must be stripped
    tags = structured.core_concepts[0].supporting_citation_tags
    assert "[REF-99]" not in tags
    assert "[REF-2]" not in tags
    assert "[REF-1]" in tags
    print(f"Pass: Hallucinated [REF-99] and inaccessible [REF-2] stripped. Remaining: {tags}")


if __name__ == "__main__":
    test_mandatory_case_1_http()
    test_mandatory_case_2_python_oop()
    test_invalid_gemini_response_handling()
    test_hallucinated_citation_stripping()
    print("\n>>> ALL PHASE 3 LESSON GENERATION TESTS PASSED! <<<")
