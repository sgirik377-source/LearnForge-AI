import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Award,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Layers,
  ChevronDown,
  ChevronUp,
  X,
  AlertCircle,
  Check,
  BookOpen
} from 'lucide-react';
import type { LessonDetail, FactualQCReport, InstructionalQCReport } from '../../types';
import { LessonService } from '../../services/api';

interface DualQCModalProps {
  lesson: LessonDetail;
  isOpen: boolean;
  onClose: () => void;
  onQCUpdated?: () => void;
}

export const DualQCModal: React.FC<DualQCModalProps> = ({
  lesson,
  isOpen,
  onClose,
  onQCUpdated,
}) => {
  const [activeTab, setActiveTab] = useState<'factual' | 'instructional'>('factual');
  const [factualReport, setFactualReport] = useState<FactualQCReport | null>(null);
  const [instructionalReport, setInstructionalReport] = useState<InstructionalQCReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningQC, setRunningQC] = useState<boolean>(false);
  const [qcActionMessage, setQcActionMessage] = useState<string>('');
  const [claimFilter, setClaimFilter] = useState<string>('ALL');
  const [expandedClaimIdx, setExpandedClaimIdx] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && lesson?.id) {
      loadReports();
    }
  }, [isOpen, lesson?.id]);

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const summary = await LessonService.getQCSummary(lesson.id);
      setFactualReport(summary.factual_qc || null);
      setInstructionalReport(summary.instructional_qc || null);
    } catch (err: any) {
      console.error('Failed to load QC summary:', err);
      // Fallback: try individual gets
      try {
        const [fact, inst] = await Promise.allSettled([
          LessonService.getFactualQC(lesson.id),
          LessonService.getInstructionalQC(lesson.id)
        ]);
        if (fact.status === 'fulfilled') setFactualReport(fact.value);
        if (inst.status === 'fulfilled') setInstructionalReport(inst.value);
      } catch (e) {
        setError('No QC reports generated yet for this lesson.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRunDualQC = async () => {
    setRunningQC(true);
    setQcActionMessage('Executing Independent Dual QC Engines...');
    setError(null);
    try {
      const res = await LessonService.runDualQC(lesson.id);
      if (res.factual_qc) setFactualReport(res.factual_qc);
      if (res.instructional_qc) setInstructionalReport(res.instructional_qc);
      setQcActionMessage('Dual QC Completed successfully!');
      setTimeout(() => setQcActionMessage(''), 3000);
      onQCUpdated?.();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to execute Dual QC.');
      setQcActionMessage('');
    } finally {
      setRunningQC(false);
    }
  };

  const handleRunFactualOnly = async () => {
    setRunningQC(true);
    setQcActionMessage('Running Factual & Research Accuracy QC...');
    setError(null);
    try {
      const rep = await LessonService.runFactualQC(lesson.id);
      setFactualReport(rep);
      setQcActionMessage('Factual QC audit completed!');
      setTimeout(() => setQcActionMessage(''), 3000);
      onQCUpdated?.();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Factual QC failed.');
      setQcActionMessage('');
    } finally {
      setRunningQC(false);
    }
  };

  const handleRunInstructionalOnly = async () => {
    setRunningQC(true);
    setQcActionMessage('Running Instructional Quality & Pedagogy QC...');
    setError(null);
    try {
      const rep = await LessonService.runInstructionalQC(lesson.id);
      setInstructionalReport(rep);
      setQcActionMessage('Instructional QC evaluation completed!');
      setTimeout(() => setQcActionMessage(''), 3000);
      onQCUpdated?.();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Instructional QC failed.');
      setQcActionMessage('');
    } finally {
      setRunningQC(false);
    }
  };

  if (!isOpen) return null;

  const isAnyStale = Boolean(factualReport?.is_stale || instructionalReport?.is_stale);
  const staleReason = factualReport?.stale_reason || instructionalReport?.stale_reason;

  const filteredClaims = (factualReport?.claim_verifications || []).filter((item) => {
    if (claimFilter === 'ALL') return true;
    return item.verdict === claimFilter;
  });

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'PASSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> PASSED
          </span>
        );
      case 'NEEDS_IMPROVEMENT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> NEEDS IMPROVEMENT
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5 text-rose-600" /> FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
            NOT EVALUATED
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden border border-slate-200">
        
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-sm">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-slate-900">Dual Quality Control Audit</h2>
                <span className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-200 text-slate-700">
                  Revision v{lesson.current_version}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {lesson.title} · Adversarial Factual Verification & Pedagogical Scaffolding Inspection
              </p>
            </div>
          </div>

          {/* Action buttons & Close */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleRunDualQC}
              disabled={runningQC}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition flex items-center gap-1.5 shadow-xs disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${runningQC ? 'animate-spin' : ''}`} />
              Run Full Dual QC
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/50 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Progress or feedback banner */}
        {qcActionMessage && (
          <div className="bg-indigo-50 border-b border-indigo-100 px-6 py-2.5 flex items-center gap-2 text-xs font-medium text-indigo-700">
            <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
            {qcActionMessage}
          </div>
        )}

        {/* Stale Warning Banner (Revision Invalidation) */}
        {isAnyStale && (
          <div className="bg-amber-50 border-b border-amber-200 px-6 py-3 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs">
              <span className="font-bold text-amber-900">STALE QC REPORT DETECTED:</span>{' '}
              <span className="text-amber-800">
                {staleReason || `Lesson content was modified to version ${lesson.current_version}. The previous evaluations no longer certify the current text.`}
              </span>
              <span className="ml-2 font-semibold text-amber-900 underline cursor-pointer" onClick={handleRunDualQC}>
                Re-run Dual QC now
              </span>
            </div>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="bg-rose-50 border-b border-rose-200 px-6 py-2.5 flex items-center justify-between text-xs text-rose-700">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-500" />
              <span>{error}</span>
            </div>
            <button
              onClick={handleRunDualQC}
              className="font-semibold underline hover:text-rose-900"
            >
              Generate Reports
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 bg-white px-6">
          <button
            onClick={() => setActiveTab('factual')}
            className={`py-3 px-4 text-sm font-semibold border-b-2 transition flex items-center gap-2.5 ${
              activeTab === 'factual'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            QC-1: Factual & Research Accuracy
            {factualReport && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                factualReport.factual_accuracy_score >= 80 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {factualReport.factual_accuracy_score}%
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('instructional')}
            className={`py-3 px-4 text-sm font-semibold border-b-2 transition flex items-center gap-2.5 ${
              activeTab === 'instructional'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Award className="w-4 h-4" />
            QC-2: Instructional Design & Pedagogy
            {instructionalReport && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                instructionalReport.pedagogical_score >= 80 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {instructionalReport.pedagogical_score}%
              </span>
            )}
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50">
          {loading ? (
            <div className="py-20 text-center">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-600">Retrieving Quality Control reports...</p>
            </div>
          ) : activeTab === 'factual' ? (
            /* =========================================================================
               TAB 1: FACTUAL & RESEARCH ACCURACY QC
               ========================================================================= */
            factualReport ? (
              <div className="space-y-6">
                {/* Score Card Banner */}
                <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-5">
                  <div className="flex items-center gap-4">
                    <div className={`w-16 h-16 rounded-2xl flex flex-col items-center justify-center font-black text-2xl shadow-inner ${
                      factualReport.factual_accuracy_score >= 80
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : factualReport.factual_accuracy_score >= 60
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      {factualReport.factual_accuracy_score}
                      <span className="text-[10px] font-semibold text-slate-400 -mt-1">/ 100</span>
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-slate-900">Factual Accuracy Score</h3>
                        {getStatusBadge(factualReport.status)}
                      </div>
                      <p className="text-xs text-slate-500 mt-1 max-w-md">
                        {factualReport.executive_summary}
                      </p>
                    </div>
                  </div>

                  {/* Criteria Metrics Grid */}
                  <div className="grid grid-cols-3 gap-3 border-t md:border-t-0 md:border-l border-slate-100 pt-3 md:pt-0 md:pl-5 text-center">
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <div className="text-xs text-slate-500 font-medium">Claim Verification</div>
                      <div className="text-sm font-bold text-slate-800 mt-0.5">{factualReport.claim_verification_rate}%</div>
                    </div>
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <div className="text-xs text-slate-500 font-medium">Citation Fidelity</div>
                      <div className="text-sm font-bold text-slate-800 mt-0.5">{factualReport.citation_fidelity_score}%</div>
                    </div>
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <div className="text-xs text-slate-500 font-medium">Hallucinations</div>
                      <div className="text-sm font-bold text-rose-600 mt-0.5">{factualReport.hallucination_penalty} pts</div>
                    </div>
                  </div>

                  <div className="flex md:flex-col justify-end">
                    <button
                      onClick={handleRunFactualOnly}
                      disabled={runningQC}
                      className="px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition flex items-center gap-1.5"
                    >
                      <RefreshCw className={`w-3 h-3 ${runningQC ? 'animate-spin' : ''}`} />
                      Re-Audit Claims
                    </button>
                  </div>
                </div>

                {/* Verification Metrics Breakdown */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                    <div className="text-xs text-slate-500">Total Analyzed</div>
                    <div className="text-lg font-bold text-slate-900 mt-1">{factualReport.total_claims_analyzed}</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-emerald-100 bg-emerald-50/20 shadow-2xs">
                    <div className="text-xs text-emerald-700 font-medium">Verified</div>
                    <div className="text-lg font-bold text-emerald-700 mt-1">{factualReport.verified_claims_count}</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-blue-100 bg-blue-50/20 shadow-2xs">
                    <div className="text-xs text-blue-700 font-medium">Partially Supported</div>
                    <div className="text-lg font-bold text-blue-700 mt-1">{factualReport.partially_supported_count}</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-amber-100 bg-amber-50/20 shadow-2xs">
                    <div className="text-xs text-amber-700 font-medium">Unsubstantiated</div>
                    <div className="text-lg font-bold text-amber-700 mt-1">{factualReport.unsubstantiated_count}</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-rose-100 bg-rose-50/20 shadow-2xs">
                    <div className="text-xs text-rose-700 font-medium">Contradicted</div>
                    <div className="text-lg font-bold text-rose-700 mt-1">{factualReport.contradicted_count}</div>
                  </div>
                </div>

                {/* Hallucination / Citation Alert (if any) */}
                {factualReport.hallucination_flags?.length > 0 && (
                  <div className="bg-rose-50 border border-rose-200 rounded-xl p-4">
                    <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                      <AlertTriangle className="w-4 h-4 text-rose-600" />
                      Citation Anomalies & Hallucination Flags
                    </h4>
                    <div className="space-y-2">
                      {factualReport.hallucination_flags.map((flag, idx) => (
                        <div key={idx} className="bg-white p-2.5 rounded-lg border border-rose-200 text-xs">
                          <span className="font-semibold text-rose-800">[{flag.offending_tag || 'FLAG'}]:</span>{' '}
                          <span className="text-slate-700">{flag.issue}</span>
                          <div className="text-slate-500 italic mt-1">Claim: "{flag.claim}"</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Claim-Level Verification Matrix */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                  <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">Claim-Level Verification Matrix</h4>
                      <p className="text-xs text-slate-500">Every extracted factual claim cross-referenced with retrieved research excerpts.</p>
                    </div>

                    {/* Filter buttons */}
                    <div className="flex items-center gap-1.5 text-xs">
                      {['ALL', 'VERIFIED', 'PARTIALLY_SUPPORTED', 'UNSUBSTANTIATED', 'CONTRADICTED'].map((filter) => (
                        <button
                          key={filter}
                          onClick={() => setClaimFilter(filter)}
                          className={`px-2.5 py-1 rounded-md font-medium transition ${
                            claimFilter === filter
                              ? 'bg-slate-800 text-white'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                        >
                          {filter.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Claims List */}
                  <div className="divide-y divide-slate-100">
                    {filteredClaims.length === 0 ? (
                      <div className="p-8 text-center text-xs text-slate-500">
                        No claims match the selected filter.
                      </div>
                    ) : (
                      filteredClaims.map((item, idx) => {
                        const isExpanded = expandedClaimIdx === idx;
                        return (
                          <div key={idx} className="p-4 hover:bg-slate-50/80 transition">
                            <div
                              className="flex items-start justify-between gap-4 cursor-pointer"
                              onClick={() => setExpandedClaimIdx(isExpanded ? null : idx)}
                            >
                              <div className="space-y-1.5 flex-1">
                                <div className="flex items-center gap-2">
                                  {item.verdict === 'VERIFIED' && (
                                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800">
                                      VERIFIED
                                    </span>
                                  )}
                                  {item.verdict === 'PARTIALLY_SUPPORTED' && (
                                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 text-blue-800">
                                      PARTIALLY SUPPORTED
                                    </span>
                                  )}
                                  {item.verdict === 'UNSUBSTANTIATED' && (
                                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800">
                                      UNSUBSTANTIATED
                                    </span>
                                  )}
                                  {item.verdict === 'CONTRADICTED' && (
                                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800">
                                      CONTRADICTED
                                    </span>
                                  )}
                                  {item.source_reference_tag && (
                                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-700">
                                      {item.source_reference_tag}
                                    </span>
                                  )}
                                  <span className="text-[11px] text-slate-400">
                                    Confidence: {Math.round(item.confidence_score * 100)}%
                                  </span>
                                </div>
                                <p className="text-sm text-slate-800 font-medium leading-relaxed">
                                  "{item.claim}"
                                </p>
                              </div>

                              <button className="text-slate-400 hover:text-slate-600 mt-1">
                                {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                              </button>
                            </div>

                            {/* Expanded Details: Evidence Quote & Correction */}
                            {isExpanded && (
                              <div className="mt-3 pt-3 border-t border-slate-100 space-y-2 text-xs">
                                {item.evidence_quote ? (
                                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                                    <span className="font-semibold text-slate-700 block mb-1">
                                      Grounding Excerpt from Research Corpus:
                                    </span>
                                    <p className="text-slate-600 italic">"{item.evidence_quote}"</p>
                                  </div>
                                ) : (
                                  <div className="text-slate-400 italic">No direct research excerpt matched.</div>
                                )}

                                {item.recommended_correction && (
                                  <div className="bg-amber-50 p-2.5 rounded-lg border border-amber-200 text-amber-900">
                                    <span className="font-semibold block mb-0.5">Recommended Correction:</span>
                                    {item.recommended_correction}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

                {/* Recommended Corrections Section */}
                {factualReport.recommended_corrections?.length > 0 && (
                  <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                      Factual Remediation Recommendations
                    </h4>
                    <ul className="space-y-1.5 text-xs text-slate-700 list-disc list-inside">
                      {factualReport.recommended_corrections.map((rec, i) => (
                        <li key={i}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <h3 className="text-base font-bold text-slate-800">Factual QC Audit Not Yet Performed</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                  Run the factual verification engine to audit every claim in this lesson against your retrieved research sources.
                </p>
                <button
                  onClick={handleRunFactualOnly}
                  disabled={runningQC}
                  className="px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition"
                >
                  Run Factual QC Audit
                </button>
              </div>
            )
          ) : (
            /* =========================================================================
               TAB 2: INSTRUCTIONAL DESIGN & PEDAGOGY QC
               ========================================================================= */
            instructionalReport ? (
              <div className="space-y-6">
                {/* Score Card Banner */}
                <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-5">
                  <div className="flex items-center gap-4">
                    <div className={`w-16 h-16 rounded-2xl flex flex-col items-center justify-center font-black text-2xl shadow-inner ${
                      instructionalReport.pedagogical_score >= 80
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : instructionalReport.pedagogical_score >= 60
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      {instructionalReport.pedagogical_score}
                      <span className="text-[10px] font-semibold text-slate-400 -mt-1">/ 100</span>
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-slate-900">Pedagogical Design Score</h3>
                        {getStatusBadge(instructionalReport.status)}
                      </div>
                      <p className="text-xs text-slate-500 mt-1 max-w-md">
                        {instructionalReport.executive_summary}
                      </p>
                    </div>
                  </div>

                  {/* Bloom Taxonomy Card */}
                  <div className="bg-indigo-50/70 border border-indigo-100 rounded-xl p-3.5 text-xs text-indigo-900">
                    <div className="font-semibold text-indigo-700 mb-1 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5" />
                      Bloom's Revised Taxonomy Depth
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="px-2 py-0.5 bg-white border border-indigo-200 rounded text-[11px] font-bold text-indigo-800">
                        Target: {instructionalReport.target_bloom_level}
                      </span>
                      <span className="text-indigo-400">→</span>
                      <span className="px-2 py-0.5 bg-indigo-600 text-white rounded text-[11px] font-bold">
                        Achieved: {instructionalReport.achieved_bloom_level}
                      </span>
                    </div>
                  </div>

                  <div className="flex md:flex-col justify-end">
                    <button
                      onClick={handleRunInstructionalOnly}
                      disabled={runningQC}
                      className="px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition flex items-center gap-1.5"
                    >
                      <RefreshCw className={`w-3 h-3 ${runningQC ? 'animate-spin' : ''}`} />
                      Re-Evaluate Pedagogy
                    </button>
                  </div>
                </div>

                {/* Sub-Dimension Scores */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                    <div className="text-xs text-slate-500">Bloom Alignment</div>
                    <div className="text-lg font-bold text-slate-800 mt-1">{instructionalReport.bloom_alignment_score}%</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                    <div className="text-xs text-slate-500">Cognitive Scaffolding</div>
                    <div className="text-lg font-bold text-slate-800 mt-1">{instructionalReport.scaffolding_score}%</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                    <div className="text-xs text-slate-500">Clarity & Sequencing</div>
                    <div className="text-lg font-bold text-slate-800 mt-1">{instructionalReport.clarity_score}%</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                    <div className="text-xs text-slate-500">Assessment Fidelity</div>
                    <div className="text-lg font-bold text-slate-800 mt-1">{instructionalReport.assessment_fidelity_score}%</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                    <div className="text-xs text-slate-500">Real-World Relevance</div>
                    <div className="text-lg font-bold text-slate-800 mt-1">{instructionalReport.engagement_score}%</div>
                  </div>
                </div>

                {/* Detailed Criteria-Based Rubric Breakdown */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                  <div className="p-4 border-b border-slate-200 bg-slate-50/50">
                    <h4 className="text-sm font-bold text-slate-900">Transparent Rubric Evaluation Breakdown</h4>
                    <p className="text-xs text-slate-500">Individual criteria weighted to compute the overall pedagogical design score.</p>
                  </div>

                  <div className="divide-y divide-slate-100">
                    {instructionalReport.rubric_breakdown?.map((criterion, idx) => (
                      <div key={idx} className="p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <h5 className="text-sm font-bold text-slate-800">{criterion.name}</h5>
                            <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                              Weight: {Math.round(criterion.weight * 100)}%
                            </span>
                          </div>
                          <div className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            criterion.score >= 80 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                          }`}>
                            {criterion.score} / 100
                          </div>
                        </div>

                        <p className="text-xs text-slate-500">{criterion.description}</p>

                        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs text-slate-700">
                          <span className="font-semibold text-slate-800 block mb-0.5">Evidence & Observation:</span>
                          {criterion.evidence}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Pedagogical Strengths & Actionable Improvements */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
                    <h4 className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Check className="w-4 h-4 text-emerald-600" />
                      Key Pedagogical Strengths
                    </h4>
                    <ul className="space-y-1.5 text-xs text-slate-700 list-disc list-inside">
                      {instructionalReport.strengths?.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
                    <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <BookOpen className="w-4 h-4 text-indigo-600" />
                      Actionable Improvements
                    </h4>
                    <ul className="space-y-1.5 text-xs text-slate-700 list-disc list-inside">
                      {instructionalReport.actionable_improvements?.map((imp, i) => (
                        <li key={i}>{imp}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                <Award className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <h3 className="text-base font-bold text-slate-800">Instructional Quality QC Not Yet Performed</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                  Evaluate learning objective alignment, Bloom's Revised Taxonomy, cognitive scaffolding, and pacing.
                </p>
                <button
                  onClick={handleRunInstructionalOnly}
                  disabled={runningQC}
                  className="px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition"
                >
                  Run Instructional QC Evaluation
                </button>
              </div>
            )
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <div>
            Lesson Status: <span className="font-semibold text-slate-800">{lesson.status}</span> · Revision {lesson.current_version}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 transition"
          >
            Close Audit Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
