# LearnForge AI — Evidence-Grounded Lesson Creation, Dual QC & Publishing Platform

**LearnForge AI** is an enterprise-grade AI curriculum synthesis and quality assurance platform built for the Kalvium hiring assignment. It empowers educators to transform educational objectives into rigorous, evidence-grounded instructional modules validated by **two independent, adversarial Quality Control (QC) engines**, reviewed and tuned by instructors, and published into production-ready **PDF, Word (DOCX), and JSON courseware packages**.

---

## 🌟 Core Architecture Principles

1. **Multimodal Research Grounding (Phase 2)**:
   - Harvests verifiable evidence across Web Search, Google Books / OpenLibrary, and YouTube Transcripts (best-effort).
   - **Strict Accessibility Distinction**: Explicitly distinguishes verified full-text excerpts from bibliographic metadata-only records (`preview_type: full_text | snippet | transcript | metadata_only`).
   - Grounded citations (`[REF-1]`, `[REF-2]`) tie claims directly to verifiable source text.

2. **Gemini-Powered Structured Synthesis (Phase 3)**:
   - Official Google Gen AI SDK (`google-genai` >= 1.0.0) with model configurable via `GEMINI_MODEL` (default: `gemini-2.5-flash`).
   - 12-section pedagogical model: Overview, Learning Objectives, Prerequisites, Core Concepts, Practical Examples, Real-World Applications, Guided Exercises, Interactive Knowledge Checks, References, and Summary.
   - Strict 45-minute maximum allocated duration constraint.

3. **Independent Dual Quality Control (Phase 4)**:
   - **QC Engine 1 — Factual & Research Accuracy**:
     - Extracts claims and evaluates against accessible sources: `VERIFIED`, `PARTIALLY_SUPPORTED`, `UNSUBSTANTIATED`, or `CONTRADICTED`.
     - Factual Score Formula: `max(0, min(100, round(0.6 * claim_verification_rate + 0.4 * citation_fidelity_score - (contradicted_count * 15.0), 1)))`.
     - **Strict Zero-Contradiction Enforcement**: Any direct contradiction (`contradicted_count >= 1`) unconditionally forces `FAILED` status.
     - Refuses metadata-only book records as evidence. Flags hallucinated citation tags (`[REF-99]`).
   - **QC Engine 2 — Instructional Quality & Pedagogy**:
     - 6-criterion pedagogical rubric: Learning Objective Alignment (25%), Scaffolding (20%), Bloom's Taxonomy Alignment (15%), Practical Examples (15%), Knowledge Checks & Assessment (15%), Duration Constraint <= 45m (10%).
     - Evaluates active Bloom verbs and cognitive progression.
   - Status Thresholds: Score >= 80.0% (`PASSED`), 60.0%–79.9% (`NEEDS_IMPROVEMENT`), < 60.0% (`FAILED`).

4. **Instructor Review, Editing & Revision Management (Phase 5)**:
   - Dedicated **Instructor Editing Studio**: Instructors can review and tune titles, objectives, durations, overview narratives, core concept explanations, and practical code examples.
   - **Persistent SQLite Revision Snapshots**: Every edit increments `current_version`, records a snapshot in `lesson_revisions` table with instructor changelog notes.
   - **Stale QC Invalidation & Alerting**: Any content edit immediately invalidates prior QC reports (`is_stale = True`), setting status to `EDITED_PENDING_QC` with an amber warning banner until re-verified.

5. **Multi-Format Lesson & QC Export Engine (Phase 5)**:
   - **PDF Document (`.pdf`)**: Formatted multi-page document rendered with ReportLab. Includes executive QC scorecards, 12-section curriculum, research bibliography, claim-level factual verification matrix, and pedagogical rubric tables.
   - **Microsoft Word (`.docx`)**: Structured document formatted with python-docx featuring styling callouts, code blocks, and assessment rationale sections.
   - **JSON Archive (`.json`)**: Machine-readable curriculum archive containing metadata, structured lesson blocks, research bibliography, factual QC audit, and pedagogical evaluation.
   - **Strict Stale-Status Protection**: Never represents stale QC as current or approved. Stale exports stamp a bold warning banner on the first page of the PDF, the top of the Word document, and in JSON metadata.

6. **Local-First SQLite Persistence**:
   - Zero heavyweight distributed infrastructure. Background tasks, lessons, sources, revisions, and QC audits are persisted in SQLite (`backend/learnforge.db`), surviving server restarts.

---

## 🏗️ Technology Stack

- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS v4 + Lucide Icons + Axios
- **Backend**: Python 3.12 + FastAPI + SQLAlchemy + SQLite + Pydantic v2 + ReportLab + python-docx
- **AI Orchestration**: Official Google Gen AI SDK (`google-genai==3.0.0`, `gemini-2.5-flash`) with structured JSON schema validation

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Copy .env.example to .env and configure your GEMINI_API_KEY
copy .env.example .env

# Run FastAPI development server
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at:
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/v1/health`

---

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend application will be accessible at:
- Web Application: `http://localhost:5173`

---

## 📂 Project Structure

```
LEANFORGE-AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── health.py        # Health probe and database connectivity
│   │   │   │   ├── lessons.py       # Lesson CRUD, revisions, and PDF/DOCX/JSON exports
│   │   │   │   ├── qc.py            # Factual & Instructional QC audits and summaries
│   │   │   │   ├── research.py      # Multimodal research harvesting and source management
│   │   │   │   └── tasks.py         # Persisted background task state and logs
│   │   │   └── api_router.py
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings & environment configuration
│   │   │   └── database.py          # SQLite engine and sessionmaker
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── lesson.py
│   │   │   ├── research_source.py
│   │   │   ├── factual_qc.py
│   │   │   ├── instructional_qc.py
│   │   │   ├── lesson_revision.py   # Immutable revision snapshots
│   │   │   └── generation_task.py
│   │   ├── schemas/                 # Pydantic v2 schemas and validation contracts
│   │   ├── services/
│   │   │   ├── export/
│   │   │   │   └── export_service.py       # PDF, DOCX, and JSON export compiler
│   │   │   ├── llm/
│   │   │   │   ├── gemini_client.py        # Official google-genai SDK client
│   │   │   │   └── lesson_generator.py     # 12-section structured synthesizer
│   │   │   ├── qc/
│   │   │   │   ├── factual_qc_service.py   # Claim verification & citation fidelity engine
│   │   │   │   └── instructional_qc_service.py # 6-criterion pedagogical rubric engine
│   │   │   ├── research/                   # Web, Google Books, and YouTube providers
│   │   │   └── tasks/                      # Background task tracking & polling
│   │   └── main.py                  # FastAPI application entrypoint and lifespan
│   ├── requirements.txt
│   ├── .env.example
│   ├── learnforge.db                # SQLite database
│   ├── test_research_pipeline.py    # Phase 2 test suite
│   ├── test_lesson_generator.py     # Phase 3 test suite
│   ├── test_dual_qc_pipeline.py     # Phase 4 test suite
│   └── test_phase5_integration.py   # Phase 5 integration & export test suite
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── lesson/
│   │   │   │   └── StructuredLessonModal.tsx # Viewer, Instructor Editor, Revisions & Exports
│   │   │   ├── qc/
│   │   │   │   └── DualQCModal.tsx           # Dual QC audit with claim filters & evidence quotes
│   │   │   ├── research/
│   │   │   │   └── ResearchLibraryModal.tsx  # Multimodal research inspection
│   │   │   ├── Navbar.tsx                    # Backend connectivity indicator
│   │   │   └── Dashboard.tsx                 # Curriculum management studio with quick exports
│   │   ├── services/
│   │   │   └── api.ts                        # Axios API client with export and revision methods
│   │   ├── types/
│   │   │   └── index.ts                      # TypeScript models and interfaces
│   │   ├── App.tsx
│   │   └── index.css                         # Tailwind CSS styling
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

---

## 🧪 Comprehensive Test Suite & Verification

All test suites execute against the local SQLite database and live API endpoints:

### 1. Research Pipeline Verification (Phase 2)
Tests multi-source harvesting across Web, Books, and YouTube, normalization, deduplication, citation tagging, accessible vs. metadata distinction, and provider fault isolation:
```bash
cd backend
python test_research_pipeline.py
```

### 2. Gemini Structured Lesson Generation (Phase 3)
Tests structured lesson generation using the official `google-genai` SDK, mandatory scenarios (HTTP Requests and Responses, Python OOP), Pydantic validation, citation integrity enforcement, and 45-minute duration ceilings:
```bash
cd backend
python test_lesson_generator.py
```

### 3. Independent Dual Quality Control (Phase 4)
Tests independent execution of Factual and Instructional QC engines, zero-contradiction enforcement, hallucinated citation detection, metadata-only citation rejection, 6-criterion pedagogical rubrics, and revision staleness invalidation:
```bash
cd backend
python test_dual_qc_pipeline.py
```

### 4. Final Integration, Revisions & Multi-Format Exports (Phase 5)
Tests end-to-end editorial lifecycle: creating draft $\to$ populating content $\to$ running Dual QC $\to$ instructor editing $\to$ verifying SQLite revision snapshot $\to$ asserting stale status & warning notices $\to$ re-certifying via Dual QC $\to$ validating PDF binary stream (`%PDF-`), DOCX stream (`PK\x03\x04`), and certified JSON export:
```bash
cd backend
python test_phase5_integration.py
```

### 5. Frontend Production Build Check
```bash
cd frontend
npm run build
```

---

## 📹 Demo Video Recording Checklist (5–7 Minutes)

When recording your presentation or product walk-through, follow this recommended journey:

1. **Dashboard & System Health (0:00 - 0:45)**:
   - Point out the real-time "FastAPI Online • SQLite Active" indicator in the header.
   - Show the Curriculum Studio dashboard with KPI metric cards and persisted SQLite tasks.
2. **Draft Creation & Multimodal Research Harvest (0:45 - 1:45)**:
   - Create a new lesson (e.g., "HTTP Requests and Responses" or "Distributed Caching").
   - Open the **Research Library** modal. Show harvested Web, Google Books, and YouTube sources.
   - Highlight the **Bibliographic Only vs. Content Verified** badges and note that book metadata is not treated as verified text.
3. **Gemini Synthesis & Structured Lesson Viewer (1:45 - 2:45)**:
   - Open the synthesized lesson. Walk through the 12-section structure: Stated Objectives, Prerequisites, Core Concepts with `[REF-1]` citation tags, Worked Examples, Guided Exercises, and Interactive Knowledge Checks.
   - Interact with a knowledge check question to demonstrate Bloom-aligned feedback and rationales.
4. **Independent Dual Quality Control Audit (2:45 - 4:00)**:
   - Open the **Dual QC** modal.
   - Show the **Factual Accuracy tab**: claim verification breakdown, claim status filters (Verified, Contradicted, Unsubstantiated), and click **View Evidence Quote** to reveal exact source grounding.
   - Switch to the **Instructional Quality tab**: inspect the 6-criterion rubric table, Bloom's Revised Taxonomy alignment, and actionable improvement recommendations.
5. **Instructor Review, Editing & Stale Alert (4:00 - 5:15)**:
   - Switch to the **Instructor Editor** tab inside the lesson modal.
   - Edit the lesson title or add an objective, enter a changelog note (e.g., "Clarified RFC 9110 terminology"), and click **Save Revision**.
   - Show the version increment (v1 $\to$ v2) and the **⚠️ Stale QC Warning Banner** alerting that prior reports no longer certify the modified text.
   - Open the **Revisions** tab to inspect the immutable historical snapshot in SQLite.
6. **Re-Auditing & Multi-Format Export (5:15 - 6:30)**:
   - Click **Re-Run Dual QC** to re-evaluate the revision and clear the stale warning.
   - Demonstrate the **Export** menu:
     - Download **PDF Document**: show the executive QC scorecard, curriculum text, and claim matrix.
     - Download **Word Document (.docx)**: show the styled courseware layout.
     - Download **JSON Archive**: show machine-readable metadata and verification scores.

---

## 📋 Final Submission Checklist

- [x] **Repository Cleanliness**: `.env`, `learnforge.db`, `.venv`, and `node_modules` are excluded via `.gitignore`.
- [x] **Zero Hardcoded Secrets**: All API keys configured via backend environment variables.
- [x] **Official Google Gen AI SDK**: Migrated to `from google import genai` (`google-genai==3.0.0`, `gemini-2.5-flash`).
- [x] **Multimodal Research**: Web, Google Books (with OpenLibrary fallback), and YouTube (with oEmbed metadata preservation).
- [x] **Pedagogical Structure**: Full 12-section model with 45-minute duration constraints.
- [x] **Dual Independent QC**: Factual claim-level verification and 6-criterion instructional rubric.
- [x] **Instructor Editing & Revisions**: Persistent SQLite revision snapshots with changelog notes.
- [x] **Stale Invalidation**: Editing invalidates QC; stale notices stamped on exports and banners.
- [x] **Export Engine**: Reliable streaming of PDF, DOCX, and JSON exports.
- [x] **100% Automated Test Pass Rate**: Phase 2, 3, 4, and 5 test suites passing.
- [x] **Production Build Clean**: TypeScript and Vite build passes with zero errors.
