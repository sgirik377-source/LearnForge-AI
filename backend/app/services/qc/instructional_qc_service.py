import re
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.instructional_qc import InstructionalQCReport
from app.services.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class InstructionalQCService:
    """
    Independent Instructional Design & Pedagogical Quality Control Engine.
    Evaluates learning objective alignment, cognitive scaffolding, Bloom's Revised Taxonomy,
    practical examples, assessment coherence, and duration pacing.
    Produces criteria-based rubric scores and persists reports in SQLite.
    """

    SYSTEM_INSTRUCTION = (
        "You are LearnForge AI's Senior Pedagogical Quality Control Reviewer. "
        "Your mission is to perform an adversarial instructional design evaluation of lesson content.\n\n"
        "EVALUATION DIMENSIONS:\n"
        "1. OBJECTIVE ALIGNMENT: Does every section directly support the stated learning objectives?\n"
        "2. COGNITIVE SCAFFOLDING: Are prerequisite refreshers present? Does complexity progress naturally?\n"
        "3. BLOOM'S TAXONOMY: Identify the target cognitive level (Remember, Understand, Apply, Analyze, Evaluate, Create) "
        "and determine whether assessments match that depth.\n"
        "4. PRACTICAL APPLICATIONS & EXAMPLES: Are realistic examples and trade-offs provided?\n"
        "5. ASSESSMENT FIDELITY: Do knowledge checks rigorously test the learning objectives?\n"
        "6. DURATION PACING: Is total duration <= 45 minutes with balanced section allocations?\n"
        "7. STRUCTURED JSON: Respond strictly in valid JSON adhering to the specified schema."
    )

    BLOOM_VERB_MAP = {
        "remember": ["recall", "define", "list", "name", "identify", "state"],
        "understand": ["explain", "describe", "distinguish", "summarize", "interpret", "classify"],
        "apply": ["implement", "execute", "use", "demonstrate", "solve", "construct"],
        "analyze": ["compare", "contrast", "differentiate", "inspect", "debug", "categorize"],
        "evaluate": ["assess", "critique", "judge", "justify", "defend", "validate"],
        "create": ["design", "build", "formulate", "compose", "architect"]
    }

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client or GeminiClient()

    async def evaluate_lesson(
        self,
        lesson_id: str,
        db: Session,
        mock_evaluator_func: Optional[Any] = None
    ) -> InstructionalQCReport:
        """
        Executes independent instructional quality evaluation for a lesson.
        Persists report in SQLite and returns the InstructionalQCReport entity.
        """
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise ValueError(f"Lesson {lesson_id} not found.")

        if not lesson.content_blocks:
            raise ValueError(f"Lesson {lesson_id} has no generated content blocks to evaluate.")

        # 1. Perform Pedagogical Evaluation
        if mock_evaluator_func:
            eval_data = await mock_evaluator_func(lesson)
        elif self.gemini_client.is_available:
            try:
                eval_data = await self._evaluate_with_gemini(lesson)
            except Exception as e:
                logger.warning(f"Remote Gemini instructional evaluation failed ({e}). Falling back to algorithmic engine.")
                eval_data = self._evaluate_algorithmic(lesson)
        else:
            eval_data = self._evaluate_algorithmic(lesson)

        # 2. Extract and Validate Rubric Breakdown
        rubric_breakdown = eval_data.get("rubric_breakdown", [])
        
        # Calculate Weighted Pedagogical Score
        if rubric_breakdown:
            pedagogical_score = round(
                sum(c.get("weight", 0.0) * c.get("score", 0.0) for c in rubric_breakdown),
                1
            )
        else:
            pedagogical_score = eval_data.get("pedagogical_score", 75.0)

        pedagogical_score = max(0.0, min(100.0, pedagogical_score))

        # Status categorization
        if pedagogical_score >= 80.0:
            status = "PASSED"
        elif pedagogical_score >= 60.0:
            status = "NEEDS_IMPROVEMENT"
        else:
            status = "FAILED"

        # 3. Construct and Persist InstructionalQCReport in SQLite
        report = InstructionalQCReport(
            id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            lesson_version=lesson.current_version,
            status=status,
            pedagogical_score=pedagogical_score,
            bloom_alignment_score=eval_data.get("bloom_alignment_score", 85.0),
            clarity_score=eval_data.get("clarity_score", 85.0),
            scaffolding_score=eval_data.get("scaffolding_score", 85.0),
            assessment_fidelity_score=eval_data.get("assessment_fidelity_score", 85.0),
            engagement_score=eval_data.get("engagement_score", 85.0),
            target_bloom_level=eval_data.get("target_bloom_level", "Understand / Apply"),
            achieved_bloom_level=eval_data.get("achieved_bloom_level", "Apply"),
            bloom_verb_analysis=eval_data.get("bloom_verb_analysis", {}),
            rubric_breakdown=rubric_breakdown,
            strengths=eval_data.get("strengths", []),
            actionable_improvements=eval_data.get("actionable_improvements", []),
            executive_summary=eval_data.get("executive_summary", "Instructional design audit complete."),
            is_stale=False,
            stale_reason=None,
            generated_at=datetime.now(timezone.utc)
        )

        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info(f"Instructional QC Report generated for lesson {lesson_id}: score={pedagogical_score}, status={status}")
        return report

    async def _evaluate_with_gemini(self, lesson: Lesson) -> Dict[str, Any]:
        """Runs Gemini-powered instructional quality audit using official SDK."""
        prompt = (
            f"INSTRUCTIONAL REVIEW TARGET:\nTitle: {lesson.title}\n"
            f"Stated Learning Objectives: {lesson.learning_objectives}\n"
            f"Target Audience: {lesson.target_audience}\n"
            f"Difficulty: {lesson.difficulty_level}\n"
            f"Content Blocks JSON:\n{json.dumps(lesson.content_blocks, indent=2)}\n\n"
            "Evaluate pedagogical quality and output a JSON object strictly matching:\n"
            "{\n"
            "  'pedagogical_score': float,\n"
            "  'bloom_alignment_score': float,\n"
            "  'clarity_score': float,\n"
            "  'scaffolding_score': float,\n"
            "  'assessment_fidelity_score': float,\n"
            "  'engagement_score': float,\n"
            "  'target_bloom_level': str,\n"
            "  'achieved_bloom_level': str,\n"
            "  'bloom_verb_analysis': {'objectives_verbs': [str], 'assessment_verbs': [str]},\n"
            "  'rubric_breakdown': [\n"
            "    {'name': str, 'weight': float, 'score': float, 'description': str, 'evidence': str}\n"
            "  ],\n"
            "  'strengths': [str],\n"
            "  'actionable_improvements': [str],\n"
            "  'executive_summary': str\n"
            "}"
        )

        return await self.gemini_client.generate_structured_json(
            prompt=prompt,
            system_instruction=self.SYSTEM_INSTRUCTION,
            temperature=0.1
        )

    def _evaluate_algorithmic(self, lesson: Lesson) -> Dict[str, Any]:
        """
        Algorithmic rule-based pedagogical evaluation engine.
        Scores objectives, scaffolding, Bloom's taxonomy, examples, assessment, and duration.
        """
        blocks = lesson.content_blocks or {}
        if isinstance(lesson.learning_objectives, list):
            objectives_text = " ".join(lesson.learning_objectives)
        else:
            objectives_text = str(lesson.learning_objectives or "")
        prereqs = blocks.get("prerequisite_knowledge", [])
        concepts = blocks.get("core_concepts", [])
        examples = blocks.get("practical_examples", [])
        apps = blocks.get("real_world_applications", [])
        exercises = blocks.get("guided_exercises", [])
        checks = blocks.get("knowledge_checks", [])
        duration = blocks.get("total_estimated_duration_mins", lesson.estimated_duration_mins or 45)

        # 1. Objective Alignment Check (Weight 0.25)
        # Check if objective keywords appear in concepts and checks
        obj_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', objectives_text.lower()))
        concept_text = " ".join([c.get("title", "") + " " + c.get("explanation", "") for c in concepts]).lower()
        matched_obj_words = [w for w in obj_words if w in concept_text] if obj_words else []
        obj_coverage = (len(matched_obj_words) / len(obj_words)) if obj_words else 1.0

        if not objectives_text or objectives_text.strip() == "":
            obj_score = 30.0
            obj_evidence = "Missing explicit learning objectives; unable to verify instructional alignment."
        elif obj_coverage >= 0.7:
            obj_score = 95.0
            obj_evidence = f"Strong alignment: Core modules cover key objective terms ({len(matched_obj_words)}/{len(obj_words)} matched)."
        else:
            obj_score = 65.0
            obj_evidence = f"Partial alignment: Core modules lack coverage of some stated objective concepts."

        # 2. Cognitive Scaffolding & Prerequisites (Weight 0.20)
        has_prereqs = len(prereqs) > 0
        has_progression = len(concepts) >= 2
        if has_prereqs and has_progression:
            scaffold_score = 92.0
            scaffold_evidence = f"Includes {len(prereqs)} prerequisite refreshers and {len(concepts)} progressive core concept modules."
        elif has_progression:
            scaffold_score = 70.0
            scaffold_evidence = "Presents conceptual progression but lacks prerequisite refreshers for novice learners."
        else:
            scaffold_score = 45.0
            scaffold_evidence = "Poor scaffolding: Insufficient conceptual depth or lack of foundational prerequisites."

        # 3. Bloom's Taxonomy Alignment (Weight 0.15)
        assessment_text = " ".join([k.get("question", "") + " " + k.get("rationale", "") for k in checks])
        if not objectives_text or objectives_text.strip() == "":
            target_bloom = "Undefined (Missing Objectives)"
            achieved_bloom = self._detect_bloom_level(assessment_text) if checks else "None"
            bloom_score = 30.0
            bloom_evidence = "Cannot evaluate Bloom alignment: Stated learning objectives are missing or empty."
        else:
            target_bloom = self._detect_bloom_level(objectives_text)
            achieved_bloom = self._detect_bloom_level(assessment_text)

            if target_bloom == achieved_bloom:
                bloom_score = 94.0
                bloom_evidence = f"Target Bloom level ({target_bloom}) successfully matched by formative assessments ({achieved_bloom})."
            else:
                bloom_score = 80.0
                bloom_evidence = f"Minor taxonomy delta: Objectives target '{target_bloom}', whereas assessments evaluate '{achieved_bloom}'."

        # 4. Practical Examples & Real-World Applications (Weight 0.15)
        has_code_or_walkthrough = any(bool(e.get("code_or_walkthrough")) for e in examples)
        has_tradeoffs = any(bool(a.get("trade_offs")) for a in apps)
        if len(examples) >= 1 and has_code_or_walkthrough and has_tradeoffs:
            example_score = 95.0
            example_evidence = f"Features {len(examples)} concrete walk-through examples and explicit trade-off analyses in real-world contexts."
        elif len(examples) >= 1:
            example_score = 75.0
            example_evidence = f"Provides {len(examples)} examples, but lacks rigorous trade-off or edge-case analyses."
        else:
            example_score = 40.0
            example_evidence = "Lacks practical code or walk-through examples."

        # 5. Assessment & Knowledge Check Quality (Weight 0.15)
        valid_checks = [k for k in checks if (k.get("correct_answer") or k.get("correct_option")) and k.get("rationale")]
        if len(valid_checks) >= 2 and all(len(k.get("options", [])) >= 3 for k in valid_checks if k.get("question_type") == "multiple_choice"):
            assess_score = 93.0
            assess_evidence = f"Includes {len(valid_checks)} multi-choice checks with complete distractor sets and conceptual rationales."
        elif len(valid_checks) >= 1:
            assess_score = 70.0
            assess_evidence = "Assessments present but limited in question diversity or distractor depth."
        else:
            assess_score = 35.0
            assess_evidence = "Inadequate formative assessment: Missing interactive knowledge checks or explanations."

        # 6. Duration & Pacing Feasibility (Weight 0.10)
        if duration <= 45:
            duration_score = 100.0
            duration_evidence = f"Total estimated duration of {duration} minutes strictly satisfies the <= 45-minute hiring requirement."
        else:
            duration_score = max(0.0, 100.0 - (duration - 45) * 5.0)
            duration_evidence = f"Duration of {duration} minutes exceeds the mandatory 45-minute ceiling."

        # Rubric Breakdown
        rubric_breakdown = [
            {
                "name": "Learning Objective Alignment",
                "weight": 0.25,
                "score": obj_score,
                "description": "Evaluates coverage of stated learning goals across content modules.",
                "evidence": obj_evidence
            },
            {
                "name": "Cognitive Scaffolding & Prerequisites",
                "weight": 0.20,
                "score": scaffold_score,
                "description": "Reviews prerequisite refreshers and progressive concept complexity.",
                "evidence": scaffold_evidence
            },
            {
                "name": "Bloom's Revised Taxonomy Alignment",
                "weight": 0.15,
                "score": bloom_score,
                "description": "Assesses cognitive depth consistency between objectives and assessments.",
                "evidence": bloom_evidence
            },
            {
                "name": "Practical Examples & Real-World Grounding",
                "weight": 0.15,
                "score": example_score,
                "description": "Evaluates code snippets, scenarios, and trade-off considerations.",
                "evidence": example_evidence
            },
            {
                "name": "Assessment & Knowledge Check Coherence",
                "weight": 0.15,
                "score": assess_score,
                "description": "Reviews question quality, distractor plausibility, and answer rationales.",
                "evidence": assess_evidence
            },
            {
                "name": "Duration & Pacing Feasibility",
                "weight": 0.10,
                "score": duration_score,
                "description": "Ensures total learning duration respects cognitive load limits (<= 45 mins).",
                "evidence": duration_evidence
            }
        ]

        strengths = [
            r["name"] + ": " + r["evidence"]
            for r in rubric_breakdown if r["score"] >= 90.0
        ]
        actionable_improvements = [
            f"Improve {r['name']} (Score: {r['score']}): {r['evidence']}"
            for r in rubric_breakdown if r["score"] < 80.0
        ]

        summary = (
            f"Instructional Design audit completed for '{lesson.title}'. "
            f"Evaluation confirmed {target_bloom} cognitive depth with {len(concepts)} core modules, "
            f"{len(examples)} practical examples, and {len(checks)} formative assessment checkpoints."
        )

        return {
            "pedagogical_score": round(sum(r["weight"] * r["score"] for r in rubric_breakdown), 1),
            "bloom_alignment_score": bloom_score,
            "clarity_score": scaffold_score,
            "scaffolding_score": scaffold_score,
            "assessment_fidelity_score": assess_score,
            "engagement_score": example_score,
            "target_bloom_level": target_bloom,
            "achieved_bloom_level": achieved_bloom,
            "bloom_verb_analysis": {
                "target_level": target_bloom,
                "achieved_level": achieved_bloom
            },
            "rubric_breakdown": rubric_breakdown,
            "strengths": strengths,
            "actionable_improvements": actionable_improvements,
            "executive_summary": summary
        }

    def _detect_bloom_level(self, text: str) -> str:
        """Determines predominant Bloom's Taxonomy cognitive level from text."""
        text_lower = text.lower()
        counts = {}
        for level, verbs in self.BLOOM_VERB_MAP.items():
            counts[level] = sum(1 for v in verbs if re.search(r'\b' + v + r'\b', text_lower))
        
        # Default to "Understand" or highest count
        best_level = max(counts, key=counts.get)
        if counts[best_level] == 0:
            return "Understand"
        return best_level.capitalize()
