export type LessonStatus =
  | 'DRAFT'
  | 'RESEARCHING'
  | 'RESEARCH_FAILED'
  | 'GENERATING'
  | 'GENERATED'
  | 'GENERATION_FAILED'
  | 'EDITED_PENDING_QC'
  | 'REVIEWED'
  | 'NEEDS_REVISION'
  | 'VERIFIED'
  | 'FULLY_REVIEWED';

export interface LessonSummary {
  id: string;
  title: string;
  target_audience: string;
  difficulty_level: string;
  estimated_duration_mins: number;
  status: LessonStatus;
  current_version: number;
  created_at: string;
  updated_at: string;
  factual_score: number | null;
  pedagogical_score: number | null;
  is_qc_stale: boolean;
}

export interface LessonDetail {
  id: string;
  title: string;
  learning_objectives: string[];
  target_audience: string;
  difficulty_level: string;
  estimated_duration_mins: number;
  content_blocks: Record<string, any>;
  status: LessonStatus;
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface LessonUpdatePayload {
  title?: string;
  learning_objectives?: string[];
  target_audience?: string;
  difficulty_level?: string;
  estimated_duration_mins?: number;
  content_blocks?: Record<string, any>;
  editor_notes?: string;
}

export interface ResearchSource {
  id: string;
  lesson_id: string;
  source_type: 'web' | 'book' | 'youtube';
  citation_tag: string;
  title: string;
  url_or_identifier?: string;
  author_or_channel?: string;
  is_content_accessible: boolean;
  preview_type: 'full_text' | 'snippet' | 'metadata_only' | 'transcript';
  accessible_text_length: number;
  extracted_content?: string;
  key_takeaways?: string;
  relevance_score: number;
  verification_scope_note?: string;
  created_at: string;
}

export interface ClaimVerificationItem {
  claim: string;
  verdict: 'VERIFIED' | 'CONTRADICTED' | 'UNSUBSTANTIATED' | 'PARTIALLY_SUPPORTED';
  evidence_quote?: string;
  source_reference_tag?: string;
  confidence_score: number;
  recommended_correction?: string;
}

export interface FactualQCReport {
  id: string;
  lesson_id: string;
  lesson_version: number;
  status: 'PASSED' | 'NEEDS_IMPROVEMENT' | 'FAILED';
  factual_accuracy_score: number;
  claim_verification_rate: number;
  citation_fidelity_score: number;
  hallucination_penalty: number;
  total_claims_analyzed: number;
  verified_claims_count: number;
  partially_supported_count: number;
  unsubstantiated_count: number;
  contradicted_count: number;
  claim_verifications: ClaimVerificationItem[];
  hallucination_flags: any[];
  missing_citations: any[];
  executive_summary: string;
  recommended_corrections: string[];
  is_stale: boolean;
  stale_reason?: string;
  generated_at: string;
}

export interface RubricCriterion {
  name: string;
  weight: number;
  score: number;
  description: string;
  evidence: string;
}

export interface InstructionalQCReport {
  id: string;
  lesson_id: string;
  lesson_version: number;
  status: 'PASSED' | 'NEEDS_IMPROVEMENT' | 'FAILED';
  pedagogical_score: number;
  bloom_alignment_score: number;
  clarity_score: number;
  scaffolding_score: number;
  assessment_fidelity_score: number;
  engagement_score: number;
  target_bloom_level: string;
  achieved_bloom_level: string;
  bloom_verb_analysis: Record<string, any>;
  rubric_breakdown: RubricCriterion[];
  strengths: string[];
  actionable_improvements: string[];
  executive_summary: string;
  is_stale: boolean;
  stale_reason?: string;
  generated_at: string;
}

export interface GenerationTask {
  id: string;
  lesson_id?: string;
  task_type: string;
  status: 'PENDING' | 'RESEARCHING' | 'SYNTHESIZING' | 'QC_EVALUATION' | 'COMPLETED' | 'FAILED';
  current_step: string;
  progress_percent: number;
  error_message?: string;
  step_logs: Array<{
    timestamp: string;
    stage: string;
    message: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface DualQCResponse {
  status: string;
  message: string;
  factual_qc?: FactualQCReport;
  instructional_qc?: InstructionalQCReport;
}

export interface QCSummaryResponse {
  lesson_id: string;
  lesson_version: number;
  is_stale: boolean;
  stale_reason?: string;
  factual_qc?: FactualQCReport;
  instructional_qc?: InstructionalQCReport;
}

export interface LessonRevision {
  id: string;
  lesson_id: string;
  revision_number: number;
  content_blocks: Record<string, any>;
  editor_notes?: string;
  created_at: string;
}
