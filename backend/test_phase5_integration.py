"""
Phase 5 Comprehensive Integration Test Suite:
- End-to-End Instructor Workflow (Create -> Research -> Synthesize -> Dual QC)
- Instructor Review & Content Editing Studio
- Persistent Revision Snapshots in SQLite (lesson_revisions table)
- Stale QC Invalidation and Alerting
- Re-running Dual QC on Revision
- Multi-format Exports (PDF, DOCX, JSON) with claim-level matrices & rubric breakdowns
- Stale Export Notice Protection (never represent stale as current)
- Edge Cases & Error Handling (404s, 422s, duration limits)
"""

import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def make_request(method, path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data_bytes = resp.read()
            if "application/json" in content_type:
                return resp.status, json.loads(data_bytes.decode("utf-8")), resp.headers
            return resp.status, data_bytes, resp.headers
    except urllib.error.HTTPError as e:
        err_bytes = e.read()
        try:
            err_json = json.loads(err_bytes.decode("utf-8"))
            return e.code, err_json, e.headers
        except Exception:
            return e.code, err_bytes.decode("utf-8", errors="replace"), e.headers


def run_tests():
    print("=" * 70)
    print("PHASE 5: FINAL INTEGRATION & EXPORT VERIFICATION TEST SUITE")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = 0

    # -------------------------------------------------------------
    # TEST 1: Create Lesson Draft
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 1] Creating new curriculum draft...")
    create_payload = {
        "title": "Distributed Caching Strategies: Architecture and Invalidation",
        "learning_objectives": [
            "Explain cache-aside, read-through, and write-behind patterns",
            "Evaluate cache stampede mitigations including probabilistic early expiration",
            "Design cache coherence protocols for distributed microservices"
        ],
        "target_audience": "Senior Engineering Students / Post-Graduate",
        "difficulty_level": "Advanced",
        "estimated_duration_mins": 40
    }
    status, lesson_data, _ = make_request("POST", "/lessons", create_payload)
    assert status == 201, f"Expected 201, got {status}: {lesson_data}"
    lesson_id = lesson_data["id"]
    assert lesson_data["title"] == create_payload["title"]
    assert lesson_data["current_version"] == 1
    print(f"  [OK] Draft created with ID: {lesson_id} (Version {lesson_data['current_version']})")

    # Attach verified research corpus to test lesson in SQLite
    from app.core.database import SessionLocal
    from app.models.research_source import ResearchSource
    import uuid

    db_session = SessionLocal()
    s1 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        title="RFC 9111: HTTP Caching Standards & Consistency Models",
        url_or_identifier="https://www.rfc-editor.org/rfc/rfc9111",
        citation_tag="[RFC-CACHE-01]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="In cache-aside, the application code queries the cache directly and populates it upon cache miss. In read-through, the cache library is responsible for fetching from the backend database transparently. In write-behind caching, write operations are immediately acknowledged to the cache and asynchronously batched to disk persistence.",
        relevance_score=1.0
    )
    s2 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="web",
        title="ACM: Optimal Probabilistic Cache Expiration Algorithms",
        url_or_identifier="https://dl.acm.org/doi/10.1145/2783258.2783405",
        citation_tag="[PAPER-STAMPEDE-02]",
        is_content_accessible=True,
        preview_type="full_text",
        extracted_content="Cache stampede occurs when high concurrency causes simultaneous cache misses. Probabilistic early expiration (the XFetch algorithm) recomputes cached values before TTL expiration by evaluating an exponential distribution against computing delta time.",
        relevance_score=0.95
    )
    s3 = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson_id,
        source_type="book",
        title="Designing Data-Intensive Applications",
        url_or_identifier="ISBN: 9781449373320",
        citation_tag="[BOOK-SYS-03]",
        is_content_accessible=False,
        preview_type="metadata_only",
        extracted_content="",
        verification_scope_note="Bibliographic metadata record; Martin Kleppmann textbook.",
        relevance_score=0.9
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()
    db_session.close()
    print("  [OK] Attached 3 research sources (2 accessible full-text, 1 bibliographic metadata-only) to SQLite corpus.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 2: Populate Synthesized Content Blocks (Simulating Generator Output)
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 2] Simulating synthesized 12-section pedagogical content...")
    mock_content_blocks = {
        "overview": "Comprehensive deep-dive into distributed memory caching, consistency models, and cache stampede mitigations.",
        "learning_objectives": create_payload["learning_objectives"],
        "prerequisite_knowledge": [
            {"concept": "Key-Value Stores", "brief_refresher": "Redis and Memcached memory structures and O(1) lookups."},
            {"concept": "TCP/IP Latency", "brief_refresher": "Network round-trip latency overhead compared to L1/RAM access."}
        ],
        "core_concepts": [
            {
                "title": "Cache-Aside, Read-Through, and Write-Behind Patterns",
                "explanation": "In cache-aside, the application code queries the cache directly and populates it upon cache miss [RFC-CACHE-01]. In read-through, the cache library is responsible for fetching from the backend database transparently [RFC-CACHE-01]. In write-behind caching, write operations are immediately acknowledged to the cache and asynchronously batched to disk persistence [RFC-CACHE-01].",
                "key_takeaway": "Cache-aside gives resilient fault isolation; read-through encapsulates persistence logic; write-behind offers high-throughput write buffering.",
                "supporting_citation_tags": ["[RFC-CACHE-01]"],
                "estimated_minutes": 10
            },
            {
                "title": "Cache Stampede and Probabilistic Early Expiration",
                "explanation": "Cache stampede occurs when high concurrency causes simultaneous cache misses [PAPER-STAMPEDE-02]. Probabilistic early expiration (the XFetch algorithm) recomputes cached values before TTL expiration by evaluating an exponential distribution against computing delta time [PAPER-STAMPEDE-02].",
                "key_takeaway": "Probabilistic early expiration prevents database connection exhaustion without global distributed locks.",
                "supporting_citation_tags": ["[PAPER-STAMPEDE-02]"],
                "estimated_minutes": 12
            },
            {
                "title": "Distributed Cache Coherence Protocols",
                "explanation": "Cache coherence in distributed microservices avoids stale data across nodes [RFC-CACHE-01]. Change-data-capture (CDC) invalidation provides eventual coherence across distributed nodes without 2PC bottlenecks.",
                "key_takeaway": "Asynchronous invalidation bus maintains coherence across replicated nodes.",
                "supporting_citation_tags": ["[RFC-CACHE-01]"],
                "estimated_minutes": 8
            }
        ],
        "practical_examples": [
            {
                "title": "Redis Cache-Aside Pattern in Python",
                "scenario": "Handling product catalog reads with fallback to PostgreSQL.",
                "code_or_walkthrough": "def get_product(pid):\n    val = redis.get(f'product:{pid}')\n    if val:\n        return json.loads(val)\n    data = db.query(Product).filter_by(id=pid).first()\n    redis.setex(f'product:{pid}', 3600, json.dumps(data))\n    return data",
                "explanation": "Demonstrates deterministic TTL and serialization with database fallback.",
                "estimated_minutes": 8
            }
        ],
        "real_world_applications": [
            {
                "domain": "E-Commerce Black Friday Flash Sales",
                "use_case": "Mitigating product inventory hotspot contention.",
                "trade_offs": "Trade slight eventual consistency for zero database collapse."
            }
        ],
        "guided_exercises": [
            {
                "title": "Configure XFetch Beta Factor",
                "problem_statement": "Calculate optimal delta expiration for an item with 100ms computation time and 1000 QPS.",
                "hints": ["Use delta = -beta * compute_time * ln(random())."],
                "solution_walkthrough": "Set beta=1.0 for balanced early-recalculation probability.",
                "estimated_minutes": 5
            }
        ],
        "knowledge_checks": [
            {
                "question": "Which caching pattern relies on the application code to populate the cache on a miss?",
                "question_type": "multiple_choice",
                "options": ["A) Cache-Aside", "B) Write-Through", "C) Write-Behind", "D) Refresh-Ahead"],
                "correct_answer": "A) Cache-Aside",
                "rationale": "In cache-aside, application logic orchestrates the miss and subsequent cache population.",
                "target_objective": "Explain cache-aside, read-through, and write-behind patterns"
            },
            {
                "question": "How does the XFetch probabilistic early expiration algorithm mitigate cache stampedes?",
                "question_type": "multiple_choice",
                "options": [
                    "A) By acquiring a distributed global mutex lock across all worker nodes",
                    "B) By probabilistically recomputing hot keys before strict TTL expiration based on computation duration",
                    "C) By permanently caching values without any TTL expiration",
                    "D) By routing all cache misses directly to replica databases"
                ],
                "correct_answer": "B) By probabilistically recomputing hot keys before strict TTL expiration based on computation duration",
                "rationale": "XFetch uses an exponential random variable scaled by computation delta time to recompute the value before expiration, avoiding thundering herd contention.",
                "target_objective": "Evaluate cache stampede mitigations including probabilistic early expiration"
            }
        ],
        "references": [
            {
                "citation_tag": "[RFC-CACHE-01]",
                "title": "RFC 9111: HTTP Caching Standards & Consistency Models",
                "url_or_identifier": "https://www.rfc-editor.org/rfc/rfc9111",
                "is_content_accessible": True,
                "verification_scope_note": "HTTP Caching specification covering cache control directives."
            },
            {
                "citation_tag": "[PAPER-STAMPEDE-02]",
                "title": "ACM: Optimal Probabilistic Cache Expiration Algorithms",
                "url_or_identifier": "https://dl.acm.org/doi/10.1145/2783258.2783405",
                "is_content_accessible": True,
                "verification_scope_note": "Peer-reviewed paper introducing XFetch probabilistic expiration algorithm."
            },
            {
                "citation_tag": "[BOOK-SYS-03]",
                "title": "Designing Data-Intensive Applications",
                "url_or_identifier": "ISBN: 9781449373320",
                "is_content_accessible": False,
                "verification_scope_note": "Bibliographic metadata record; Martin Kleppmann textbook."
            }
        ],
        "lesson_summary": "Distributed caching reduces database pressure and latency when configured with proper TTL and early expiration mitigations."
    }

    update_payload = {
        "content_blocks": mock_content_blocks,
        "editor_notes": "Initial synthetic generation"
    }
    status, updated_lesson, _ = make_request("PUT", f"/lessons/{lesson_id}", update_payload)
    assert status == 200, f"Expected 200, got {status}: {updated_lesson}"
    print(f"  [OK] Lesson populated with {len(mock_content_blocks['core_concepts'])} core concepts and references.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 3: Run Initial Dual QC on Lesson
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 3] Running Independent Dual QC on initial version...")
    status, qc_resp, _ = make_request("POST", f"/qc/{lesson_id}/all")
    assert status == 200, f"Expected 200, got {status}: {qc_resp}"
    fact_qc = qc_resp.get("factual_qc")
    inst_qc = qc_resp.get("instructional_qc")
    assert fact_qc is not None, "Factual QC must not be None"
    assert inst_qc is not None, "Instructional QC must not be None"
    assert not fact_qc["is_stale"], "Fresh Factual QC must not be stale"
    assert not inst_qc["is_stale"], "Fresh Instructional QC must not be stale"
    print(f"  [OK] Factual QC Score: {fact_qc['factual_accuracy_score']}% (Status: {fact_qc['status']})")
    print(f"  [OK] Instructional QC Score: {inst_qc['pedagogical_score']}% (Status: {inst_qc['status']})")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 4: Instructor Editorial Review & Revision Snapshotting
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 4] Instructor edits lesson title, objectives, and concept explanation...")
    edit_payload = {
        "title": "Distributed Caching & Invalidation Architecture (Enterprise Edition)",
        "learning_objectives": [
            "Explain cache-aside, read-through, and write-behind patterns",
            "Evaluate cache stampede mitigations including probabilistic early expiration",
            "Design cache coherence protocols for distributed microservices",
            "Analyze two-phase commit vs Saga patterns during distributed cache invalidation"
        ],
        "target_audience": "Principal Architects & Senior Engineers",
        "difficulty_level": "Advanced",
        "estimated_duration_mins": 45,
        "editor_notes": "Instructor added 4th learning objective regarding distributed Saga invalidation."
    }
    status, edited_lesson, _ = make_request("PUT", f"/lessons/{lesson_id}", edit_payload)
    assert status == 200, f"Expected 200, got {status}: {edited_lesson}"
    assert edited_lesson["title"] == edit_payload["title"]
    assert edited_lesson["current_version"] == 3  # (1 draft -> 2 pop -> 3 edit)
    assert edited_lesson["status"] == "EDITED_PENDING_QC"
    print(f"  [OK] Lesson version incremented to v{edited_lesson['current_version']}")
    print(f"  [OK] Lesson status set to '{edited_lesson['status']}'")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 5: Verify Stale QC Invalidation Following Revision
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 5] Checking that previous QC reports are marked STALE...")
    status, qc_summary, _ = make_request("GET", f"/qc/{lesson_id}/summary")
    assert status == 200, f"Expected 200, got {status}: {qc_summary}"
    assert qc_summary["is_stale"] is True, "QC summary must report stale=True after editing"
    assert "Fresh verification required" in qc_summary["stale_reason"]
    assert qc_summary["factual_qc"]["is_stale"] is True
    assert qc_summary["instructional_qc"]["is_stale"] is True
    print(f"  [OK] QC Summary stale flag: {qc_summary['is_stale']}")
    print(f"  [OK] Stale reason: '{qc_summary['stale_reason']}'")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 6: Verify Revision Audit Trail in SQLite
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 6] Fetching revision history from SQLite...")
    status, revisions, _ = make_request("GET", f"/lessons/{lesson_id}/revisions")
    assert status == 200, f"Expected 200, got {status}: {revisions}"
    assert len(revisions) >= 2, f"Expected at least 2 revisions, got {len(revisions)}"
    latest_rev = revisions[0]  # ordered by revision_number desc
    assert latest_rev["revision_number"] == edited_lesson["current_version"]
    assert "Instructor added 4th learning objective" in latest_rev["editor_notes"]
    print(f"  [OK] Retrieved {len(revisions)} revisions from SQLite.")
    print(f"  [OK] Latest revision #{latest_rev['revision_number']}: '{latest_rev['editor_notes']}'")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 7: Stale Export Warning Protection
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 7] Testing JSON Export under STALE conditions...")
    status, export_data, _ = make_request("GET", f"/lessons/{lesson_id}/export/json")
    assert status == 200, f"Expected 200, got {status}: {export_data}"
    metadata = export_data["metadata"]
    assert metadata["is_stale"] is True, "Export metadata must flag is_stale=True"
    assert "WARNING: Lesson content was modified after QC evaluation" in metadata["stale_warning"], "Must include stale warning notice"
    print(f"  [OK] Stale notice stamped on export: '{metadata['stale_warning']}'")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 8: Re-running Dual QC on Revised Lesson
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 8] Re-running Dual QC to re-certify revised lesson v3...")
    status, re_qc, _ = make_request("POST", f"/qc/{lesson_id}/all")
    assert status == 200, f"Expected 200, got {status}: {re_qc}"
    assert not re_qc["factual_qc"]["is_stale"], "Re-run factual QC must not be stale"
    assert not re_qc["instructional_qc"]["is_stale"], "Re-run instructional QC must not be stale"
    assert re_qc["factual_qc"]["lesson_version"] == edited_lesson["current_version"]
    print(f"  [OK] Re-run Factual QC: {re_qc['factual_qc']['factual_accuracy_score']}% (stale={re_qc['factual_qc']['is_stale']})")
    print(f"  [OK] Re-run Instructional QC: {re_qc['instructional_qc']['pedagogical_score']}% (stale={re_qc['instructional_qc']['is_stale']})")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 9: Multi-Format Export - JSON Package Verification
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 9] Verifying Certified JSON Export Structure...")
    status, certified_json, _ = make_request("GET", f"/lessons/{lesson_id}/export/json")
    assert status == 200
    assert certified_json["metadata"]["is_stale"] is False
    assert certified_json["metadata"]["stale_warning"] is None
    assert "lesson" in certified_json
    assert "research_bibliography" in certified_json
    assert "quality_control" in certified_json
    assert certified_json["quality_control"]["factual_qc"] is not None
    assert certified_json["quality_control"]["instructional_qc"] is not None
    assert len(certified_json["lesson"]["learning_objectives"]) == 4
    print(f"  [OK] JSON Export contains all certified top-level packages.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 10: Multi-Format Export - PDF Binary Streaming Verification
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 10] Verifying PDF Binary Export Streaming...")
    status, pdf_bytes, headers = make_request("GET", f"/lessons/{lesson_id}/export/pdf")
    assert status == 200
    assert headers.get("Content-Type") == "application/pdf"
    assert "attachment;" in headers.get("Content-Disposition", "")
    assert pdf_bytes.startswith(b"%PDF-"), f"Invalid PDF header: {pdf_bytes[:10]}"
    assert len(pdf_bytes) > 5000, f"PDF too small ({len(pdf_bytes)} bytes)"
    print(f"  [OK] PDF exported successfully: {len(pdf_bytes):,} bytes with valid %PDF- header.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 11: Multi-Format Export - DOCX Binary Streaming Verification
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 11] Verifying DOCX Binary Export Streaming...")
    status, docx_bytes, headers = make_request("GET", f"/lessons/{lesson_id}/export/docx")
    assert status == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in headers.get("Content-Type", "")
    assert "attachment;" in headers.get("Content-Disposition", "")
    assert docx_bytes.startswith(b"PK\x03\x04"), f"Invalid DOCX zip header: {docx_bytes[:10]}"
    assert len(docx_bytes) > 20000, f"DOCX too small ({len(docx_bytes)} bytes)"
    print(f"  [OK] DOCX exported successfully: {len(docx_bytes):,} bytes with valid PK zip header.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 12: Edge Cases & Error Handling
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 12] Testing Edge Cases & Error Handling...")
    
    # Nonexistent lesson export
    status, not_found, _ = make_request("GET", "/lessons/nonexistent-uuid-1234/export/pdf")
    assert status == 404, f"Expected 404, got {status}"

    # Nonexistent lesson revisions
    status, not_found, _ = make_request("GET", "/lessons/nonexistent-uuid-1234/revisions")
    assert status == 404, f"Expected 404, got {status}"

    # Exceeding maximum allowed lesson duration (>45 mins)
    invalid_duration_payload = {
        "title": "Invalid Duration Lesson",
        "learning_objectives": ["Exceeding time constraints"],
        "estimated_duration_mins": 90
    }
    status, err_resp, _ = make_request("POST", "/lessons", invalid_duration_payload)
    assert status == 422, f"Expected 422 for duration > 45, got {status}"
    print(f"  [OK] 404 for invalid lesson IDs verified.")
    print(f"  [OK] 422 for duration > 45m rejected properly.")
    passed_tests += 1

    # Summary
    print("\n" + "=" * 70)
    print(f"ALL TESTS PASSED: {passed_tests}/{total_tests} (100% SUCCESS)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
