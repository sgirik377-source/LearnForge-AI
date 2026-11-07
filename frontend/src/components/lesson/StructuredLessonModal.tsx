import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  CheckCircle2,
  Clock,
  Code,
  HelpCircle,
  Lightbulb,
  ExternalLink,
  ChevronRight,
  Sparkles,
  FileText,
  Target,
  Edit3,
  History,
  Download,
  ShieldCheck,
  AlertTriangle,
  Save,
  Plus,
  Trash2,
  FileDown,
  FileSpreadsheet,
  Check
} from 'lucide-react';
import type { LessonDetail, LessonRevision } from '../../types';
import { LessonService } from '../../services/api';

interface StructuredLessonModalProps {
  lesson: LessonDetail;
  onClose: () => void;
  onLessonUpdated?: (updatedLesson: LessonDetail) => void;
  onOpenQC?: (lessonId: string) => void;
}

export const StructuredLessonModal: React.FC<StructuredLessonModalProps> = ({
  lesson: initialLesson,
  onClose,
  onLessonUpdated,
  onOpenQC
}) => {
  const [currentLesson, setCurrentLesson] = useState<LessonDetail>(initialLesson);
  const [mode, setMode] = useState<'view' | 'edit' | 'revisions'>('view');
  const [activeTab, setActiveTab] = useState<'concepts' | 'examples' | 'exercises' | 'quizzes' | 'references'>('concepts');

  // Quiz state
  const [selectedQuizAnswers, setSelectedQuizAnswers] = useState<Record<number, string>>({});
  const [revealedHints, setRevealedHints] = useState<Record<number, boolean>>({});
  const [revealedSolutions, setRevealedSolutions] = useState<Record<number, boolean>>({});

  // Export menu state
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Revision history state
  const [revisions, setRevisions] = useState<LessonRevision[]>([]);
  const [loadingRevisions, setLoadingRevisions] = useState(false);

  // Instructor Edit State
  const [editTitle, setEditTitle] = useState(currentLesson.title);
  const [editAudience, setEditAudience] = useState(currentLesson.target_audience);
  const [editDifficulty, setEditDifficulty] = useState(currentLesson.difficulty_level);
  const [editDuration, setEditDuration] = useState(currentLesson.estimated_duration_mins);
  const [editObjectives, setEditObjectives] = useState<string[]>([...currentLesson.learning_objectives]);
  const [editOverview, setEditOverview] = useState(currentLesson.content_blocks?.overview || '');
  const [editConcepts, setEditConcepts] = useState<any[]>(
    JSON.parse(JSON.stringify(currentLesson.content_blocks?.core_concepts || []))
  );
  const [editExamples, setEditExamples] = useState<any[]>(
    JSON.parse(JSON.stringify(currentLesson.content_blocks?.practical_examples || []))
  );
  const [editorNotes, setEditorNotes] = useState('Instructor refinement and curriculum tuning');
  const [savingEdit, setSavingEdit] = useState(false);
  const [saveSuccessNotice, setSaveSuccessNotice] = useState<string | null>(null);
  const [saveErrorNotice, setSaveErrorNotice] = useState<string | null>(null);

  // Sync state if initialLesson changes
  useEffect(() => {
    setCurrentLesson(initialLesson);
    setEditTitle(initialLesson.title);
    setEditAudience(initialLesson.target_audience);
    setEditDifficulty(initialLesson.difficulty_level);
    setEditDuration(initialLesson.estimated_duration_mins);
    setEditObjectives([...initialLesson.learning_objectives]);
    setEditOverview(initialLesson.content_blocks?.overview || '');
    setEditConcepts(JSON.parse(JSON.stringify(initialLesson.content_blocks?.core_concepts || [])));
    setEditExamples(JSON.parse(JSON.stringify(initialLesson.content_blocks?.practical_examples || [])));
  }, [initialLesson]);

  // Load revisions when switching to revisions tab
  useEffect(() => {
    if (mode === 'revisions') {
      loadRevisions();
    }
  }, [mode]);

  const loadRevisions = async () => {
    setLoadingRevisions(true);
    try {
      const revs = await LessonService.getRevisions(currentLesson.id);
      setRevisions(revs);
    } catch (err) {
      console.error('Failed to load revisions:', err);
    } finally {
      setLoadingRevisions(false);
    }
  };

  const content = currentLesson.content_blocks || {};
  const coreConcepts = content.core_concepts || [];
  const practicalExamples = content.practical_examples || [];
  const realWorldApps = content.real_world_applications || [];
  const guidedExercises = content.guided_exercises || [];
  const knowledgeChecks = content.knowledge_checks || [];
  const references = content.references || [];
  const prerequisites = content.prerequisite_knowledge || [];

  const handleSelectOption = (qIdx: number, option: string) => {
    setSelectedQuizAnswers({
      ...selectedQuizAnswers,
      [qIdx]: option
    });
  };

  // Edit Mode handlers
  const handleAddObjective = () => {
    setEditObjectives([...editObjectives, '']);
  };

  const handleObjectiveChange = (index: number, val: string) => {
    const updated = [...editObjectives];
    updated[index] = val;
    setEditObjectives(updated);
  };

  const handleRemoveObjective = (index: number) => {
    if (editObjectives.length > 1) {
      setEditObjectives(editObjectives.filter((_, i) => i !== index));
    }
  };

  const handleConceptChange = (index: number, field: string, val: any) => {
    const updated = [...editConcepts];
    updated[index] = { ...updated[index], [field]: val };
    setEditConcepts(updated);
  };

  const handleAddConcept = () => {
    setEditConcepts([
      ...editConcepts,
      {
        title: 'New Core Concept',
        explanation: 'Detailed explanation of this concept.',
        key_takeaway: 'Key takeaway summary.',
        supporting_citation_tags: [],
        estimated_minutes: 5
      }
    ]);
  };

  const handleRemoveConcept = (index: number) => {
    if (editConcepts.length > 1) {
      setEditConcepts(editConcepts.filter((_, i) => i !== index));
    }
  };

  const handleExampleChange = (index: number, field: string, val: any) => {
    const updated = [...editExamples];
    updated[index] = { ...updated[index], [field]: val };
    setEditExamples(updated);
  };

  const handleSaveRevision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editTitle.trim()) {
      setSaveErrorNotice('Title cannot be empty');
      return;
    }

    setSavingEdit(true);
    setSaveErrorNotice(null);
    setSaveSuccessNotice(null);

    try {
      const updatedContentBlocks = {
        ...currentLesson.content_blocks,
        overview: editOverview,
        learning_objectives: editObjectives.filter(o => o.trim().length > 0),
        core_concepts: editConcepts,
        practical_examples: editExamples
      };

      const updated = await LessonService.updateLesson(currentLesson.id, {
        title: editTitle,
        learning_objectives: editObjectives.filter(o => o.trim().length > 0),
        target_audience: editAudience,
        difficulty_level: editDifficulty,
        estimated_duration_mins: editDuration,
        content_blocks: updatedContentBlocks,
        editor_notes: editorNotes.trim() || 'Instructor editorial revision'
      });

      setCurrentLesson(updated);
      setSaveSuccessNotice(
        `Version ${updated.current_version} saved successfully in SQLite! Note: Previous QC reports are now marked STALE.`
      );
      if (onLessonUpdated) {
        onLessonUpdated(updated);
      }
      setTimeout(() => {
        setSaveSuccessNotice(null);
      }, 6000);
    } catch (err: any) {
      console.error('Failed to save lesson revision:', err);
      setSaveErrorNotice(err?.response?.data?.detail || 'Failed to save changes. Please try again.');
    } finally {
      setSavingEdit(false);
    }
  };

  const isStale = currentLesson.status === 'EDITED_PENDING_QC';

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-5xl w-full h-[94vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between gap-3">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                Structured Lesson
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                v{currentLesson.current_version}
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>Max 45m ({currentLesson.estimated_duration_mins}m)</span>
              </span>
              {isStale && (
                <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-amber-400" /> Stale QC
                </span>
              )}
            </div>
            <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight truncate">
              {currentLesson.title}
            </h1>
          </div>

          {/* Action Buttons in Header */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Mode Switcher */}
            <div className="flex items-center bg-slate-800/80 p-0.5 rounded-lg border border-slate-700 text-xs">
              <button
                onClick={() => setMode('view')}
                className={`px-3 py-1.5 rounded-md font-medium transition cursor-pointer flex items-center gap-1.5 ${
                  mode === 'view'
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">View</span>
              </button>
              <button
                onClick={() => setMode('edit')}
                className={`px-3 py-1.5 rounded-md font-medium transition cursor-pointer flex items-center gap-1.5 ${
                  mode === 'edit'
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Instructor Editor</span>
              </button>
              <button
                onClick={() => setMode('revisions')}
                className={`px-3 py-1.5 rounded-md font-medium transition cursor-pointer flex items-center gap-1.5 ${
                  mode === 'revisions'
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <History className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Revisions</span>
              </button>
            </div>

            {/* Re-run Dual QC button */}
            {onOpenQC && (
              <button
                onClick={() => onOpenQC(currentLesson.id)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition cursor-pointer"
                title="Open Dual Quality Control Audit"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                <span className="hidden md:inline">Audit QC</span>
              </button>
            )}

            {/* Export Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition cursor-pointer"
                title="Export Lesson with Verified QC Reports"
              >
                <Download className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Export</span>
              </button>

              {showExportMenu && (
                <div
                  className="absolute right-0 mt-2 w-52 bg-slate-900 border border-slate-700 rounded-xl shadow-xl z-50 py-1.5 divide-y divide-slate-800"
                  onMouseLeave={() => setShowExportMenu(false)}
                >
                  <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Full Package Exports
                  </div>
                  <div className="py-1">
                    <button
                      onClick={() => {
                        LessonService.downloadExport(currentLesson.id, 'pdf');
                        setShowExportMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 text-xs text-slate-200 hover:bg-slate-800 flex items-center gap-2 cursor-pointer transition"
                    >
                      <FileDown className="w-4 h-4 text-rose-400" />
                      <div>
                        <div className="font-medium text-white">PDF Document (.pdf)</div>
                        <div className="text-[10px] text-slate-400">Formatted lesson + Dual QC matrix</div>
                      </div>
                    </button>

                    <button
                      onClick={() => {
                        LessonService.downloadExport(currentLesson.id, 'docx');
                        setShowExportMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 text-xs text-slate-200 hover:bg-slate-800 flex items-center gap-2 cursor-pointer transition"
                    >
                      <FileSpreadsheet className="w-4 h-4 text-blue-400" />
                      <div>
                        <div className="font-medium text-white">Word Document (.docx)</div>
                        <div className="text-[10px] text-slate-400">Structured DOCX courseware</div>
                      </div>
                    </button>

                    <button
                      onClick={() => {
                        LessonService.downloadExport(currentLesson.id, 'json');
                        setShowExportMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 text-xs text-slate-200 hover:bg-slate-800 flex items-center gap-2 cursor-pointer transition"
                    >
                      <Code className="w-4 h-4 text-amber-400" />
                      <div>
                        <div className="font-medium text-white">JSON Archive (.json)</div>
                        <div className="text-[10px] text-slate-400">Machine-readable curriculum & QC</div>
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Stale Warning Banner (if lesson was edited) */}
        {isStale && (
          <div className="bg-amber-950/40 border-b border-amber-800/60 px-5 py-2.5 flex items-center justify-between gap-3 text-xs text-amber-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                <strong>Warning:</strong> Lesson content was edited (Version {currentLesson.current_version}). Prior QC verification reports are stale.
              </span>
            </div>
            {onOpenQC && (
              <button
                onClick={() => onOpenQC(currentLesson.id)}
                className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-medium transition cursor-pointer shrink-0"
              >
                Re-Run Dual QC Now
              </button>
            )}
          </div>
        )}

        {/* Save alerts */}
        {saveSuccessNotice && (
          <div className="bg-emerald-950/40 border-b border-emerald-800/60 px-5 py-2 flex items-center gap-2 text-xs text-emerald-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{saveSuccessNotice}</span>
          </div>
        )}

        {saveErrorNotice && (
          <div className="bg-rose-950/40 border-b border-rose-800/60 px-5 py-2 flex items-center gap-2 text-xs text-rose-300">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{saveErrorNotice}</span>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODE 1: VIEW LESSON */}
        {/* ========================================================================= */}
        {mode === 'view' && (
          <>
            {/* Overview & Stated Objectives Banner */}
            <div className="bg-slate-950/40 p-4 sm:p-5 border-b border-slate-800 space-y-3">
              {content.overview && (
                <p className="text-sm text-slate-300 leading-relaxed">
                  <strong className="text-white">Overview: </strong>
                  {content.overview}
                </p>
              )}

              <div className="flex flex-wrap gap-4 text-xs">
                <div className="flex-1 min-w-[280px] bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                  <span className="font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1 mb-1.5">
                    <Target className="w-3.5 h-3.5" /> Stated Learning Objectives
                  </span>
                  <ul className="space-y-1 text-slate-300">
                    {currentLesson.learning_objectives.map((obj, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <ChevronRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {prerequisites.length > 0 && (
                  <div className="flex-1 min-w-[280px] bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                    <span className="font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1 mb-1.5">
                      <Lightbulb className="w-3.5 h-3.5" /> Prerequisite Knowledge
                    </span>
                    <ul className="space-y-1 text-slate-300">
                      {prerequisites.map((p: any, i: number) => (
                        <li key={i} className="text-xs">
                          <strong className="text-slate-200">{p.concept}: </strong>
                          <span className="text-slate-400">{p.brief_refresher}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex items-center gap-2 px-6 pt-3 border-b border-slate-800 bg-slate-900 overflow-x-auto">
              <button
                onClick={() => setActiveTab('concepts')}
                className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                  activeTab === 'concepts'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Core Concepts ({coreConcepts.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('examples')}
                className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                  activeTab === 'examples'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Code className="w-3.5 h-3.5" />
                <span>Worked Examples ({practicalExamples.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('exercises')}
                className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                  activeTab === 'exercises'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Guided Exercises & Apps ({guidedExercises.length + realWorldApps.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('quizzes')}
                className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                  activeTab === 'quizzes'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Knowledge Checks ({knowledgeChecks.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('references')}
                className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                  activeTab === 'references'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Grounded References ({references.length})</span>
              </button>
            </div>

            {/* Tab Content Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* TAB 1: CORE CONCEPTS */}
              {activeTab === 'concepts' && (
                <div className="space-y-5">
                  {coreConcepts.map((concept: any, idx: number) => (
                    <div
                      key={idx}
                      className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-indigo-600/20 text-indigo-400 font-bold text-xs flex items-center justify-center">
                            {idx + 1}
                          </span>
                          <h3 className="text-base font-semibold text-white">{concept.title}</h3>
                        </div>
                        <span className="text-xs text-slate-400 flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                          <Clock className="w-3 h-3" /> {concept.estimated_minutes}m
                        </span>
                      </div>

                      <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                        {concept.explanation}
                      </p>

                      <div className="bg-indigo-950/30 border border-indigo-900/40 rounded-lg p-3 text-xs text-indigo-200 flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                        <div>
                          <strong className="text-white">Key Takeaway: </strong>
                          <span>{concept.key_takeaway}</span>
                        </div>
                      </div>

                      {concept.supporting_citation_tags && concept.supporting_citation_tags.length > 0 && (
                        <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80 text-xs text-slate-400">
                          <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
                            Research Citations:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {concept.supporting_citation_tags.map((tag: string, tIdx: number) => (
                              <span
                                key={tIdx}
                                className="font-mono text-[11px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* TAB 2: PRACTICAL EXAMPLES */}
              {activeTab === 'examples' && (
                <div className="space-y-6">
                  {practicalExamples.map((example: any, idx: number) => (
                    <div
                      key={idx}
                      className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="p-1 rounded bg-indigo-500/10 text-indigo-400">
                            <Code className="w-4 h-4" />
                          </span>
                          <h3 className="text-base font-semibold text-white">{example.title}</h3>
                        </div>
                        <span className="text-xs text-slate-400 flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                          <Clock className="w-3 h-3" /> {example.estimated_minutes}m
                        </span>
                      </div>

                      <div className="text-xs text-slate-300">
                        <strong className="text-slate-400">Scenario: </strong>
                        {example.scenario}
                      </div>

                      <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 overflow-x-auto">
                        <pre className="text-xs font-mono text-emerald-400 whitespace-pre-wrap leading-relaxed">
                          {example.code_or_walkthrough}
                        </pre>
                      </div>

                      <div className="text-xs text-slate-400 leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
                        <strong className="text-slate-300">Explanation & Insights: </strong>
                        {example.explanation}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* TAB 3: GUIDED EXERCISES & APPLICATIONS */}
              {activeTab === 'exercises' && (
                <div className="space-y-6">
                  {/* Guided Exercises */}
                  <div className="space-y-4">
                    <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                      <FileText className="w-4 h-4" /> Hands-On Guided Exercises
                    </h3>

                    {guidedExercises.map((exercise: any, idx: number) => (
                      <div
                        key={idx}
                        className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3"
                      >
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold text-white text-sm">
                            Exercise {idx + 1}: {exercise.title}
                          </h4>
                          <span className="text-xs text-slate-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {exercise.estimated_minutes}m
                          </span>
                        </div>

                        <p className="text-xs text-slate-300">{exercise.prompt}</p>

                        <div className="flex items-center gap-3 pt-2">
                          {exercise.hint && (
                            <button
                              onClick={() => setRevealedHints({ ...revealedHints, [idx]: !revealedHints[idx] })}
                              className="text-xs text-amber-400 hover:text-amber-300 transition cursor-pointer flex items-center gap-1"
                            >
                              <Lightbulb className="w-3.5 h-3.5" />
                              <span>{revealedHints[idx] ? 'Hide Hint' : 'Show Hint'}</span>
                            </button>
                          )}

                          {exercise.solution_walkthrough && (
                            <button
                              onClick={() => setRevealedSolutions({ ...revealedSolutions, [idx]: !revealedSolutions[idx] })}
                              className="text-xs text-indigo-400 hover:text-indigo-300 transition cursor-pointer flex items-center gap-1"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>{revealedSolutions[idx] ? 'Hide Solution' : 'Show Walkthrough'}</span>
                            </button>
                          )}
                        </div>

                        {revealedHints[idx] && exercise.hint && (
                          <div className="bg-amber-950/20 border border-amber-900/30 rounded-lg p-3 text-xs text-amber-200">
                            <strong>Hint: </strong>{exercise.hint}
                          </div>
                        )}

                        {revealedSolutions[idx] && exercise.solution_walkthrough && (
                          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 font-mono whitespace-pre-wrap">
                            <strong>Solution Walkthrough:</strong>
                            <div className="mt-1 text-slate-200">{exercise.solution_walkthrough}</div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Real World Applications */}
                  {realWorldApps.length > 0 && (
                    <div className="space-y-4 pt-4 border-t border-slate-800">
                      <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                        Industry Applications & Architectural Trade-offs
                      </h3>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {realWorldApps.map((app: any, idx: number) => (
                          <div
                            key={idx}
                            className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2 text-xs"
                          >
                            <span className="font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                              {app.domain}
                            </span>
                            <div className="text-slate-200 pt-1">
                              <strong>Use Case: </strong>{app.use_case}
                            </div>
                            <div className="text-slate-400">
                              <strong>Trade-offs & Constraints: </strong>{app.trade_offs}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: KNOWLEDGE CHECKS (INTERACTIVE QUIZZES) */}
              {activeTab === 'quizzes' && (
                <div className="space-y-5">
                  <div className="text-xs text-slate-400">
                    Test your understanding with these Bloom-aligned interactive knowledge checks:
                  </div>

                  {knowledgeChecks.map((q: any, qIdx: number) => {
                    const selected = selectedQuizAnswers[qIdx];
                    const hasAnswered = selected !== undefined;
                    const isCorrect = selected === q.correct_option;

                    return (
                      <div
                        key={qIdx}
                        className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-4"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <h4 className="text-sm font-semibold text-white">
                            {qIdx + 1}. {q.question}
                          </h4>
                          {hasAnswered && (
                            <span
                              className={`text-xs px-2.5 py-0.5 rounded-full font-medium flex items-center gap-1 ${
                                isCorrect
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              }`}
                            >
                              {isCorrect ? 'Correct' : 'Incorrect'}
                            </span>
                          )}
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {q.options &&
                            q.options.map((option: string, optIdx: number) => {
                              const isThisSelected = selected === option;
                              const isThisCorrect = option === q.correct_option;

                              let btnStyle = 'border-slate-800 bg-slate-900/60 text-slate-300 hover:bg-slate-800/80';
                              if (hasAnswered) {
                                if (isThisCorrect) {
                                  btnStyle = 'border-emerald-500 bg-emerald-950/40 text-emerald-200';
                                } else if (isThisSelected) {
                                  btnStyle = 'border-rose-500 bg-rose-950/40 text-rose-200';
                                }
                              }

                              return (
                                <button
                                  key={optIdx}
                                  onClick={() => handleSelectOption(qIdx, option)}
                                  className={`p-3 rounded-lg border text-xs text-left transition cursor-pointer flex items-center justify-between ${btnStyle}`}
                                >
                                  <span>{option}</span>
                                  {hasAnswered && isThisCorrect && (
                                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 ml-1" />
                                  )}
                                </button>
                              );
                            })}
                        </div>

                        {hasAnswered && (
                          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 text-xs space-y-1">
                            <div className="font-semibold text-white flex items-center gap-1.5">
                              <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
                              <span>Explanation & Rationale:</span>
                            </div>
                            <p className="text-slate-300 pl-5">{q.rationale}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* TAB 5: REFERENCES & GROUNDING */}
              {activeTab === 'references' && (
                <div className="space-y-4">
                  <div className="text-xs text-slate-400">
                    The following external sources were used to factually ground this synthesized lesson:
                  </div>

                  {references.map((ref: any, idx: number) => (
                    <div
                      key={idx}
                      className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 flex items-center justify-between gap-3"
                    >
                      <div className="space-y-1 flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                            {ref.citation_tag}
                          </span>
                          <h4 className="font-semibold text-white text-sm truncate">{ref.title}</h4>
                        </div>

                        {ref.verification_scope_note && (
                          <p className="text-xs text-slate-400">{ref.verification_scope_note}</p>
                        )}
                      </div>

                      <div className="flex items-center gap-3">
                        <span
                          className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium ${
                            ref.is_content_accessible
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}
                        >
                          {ref.is_content_accessible ? 'Content Verified' : 'Bibliographic Only'}
                        </span>

                        {ref.url_or_identifier && ref.url_or_identifier.startsWith('http') && (
                          <a
                            href={ref.url_or_identifier}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-slate-400 hover:text-indigo-400 p-1.5 rounded bg-slate-900 border border-slate-800 transition"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}

                  {content.lesson_summary && (
                    <div className="mt-6 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-1">
                      <h4 className="font-semibold text-white text-sm">Lesson Summary & Synthesis</h4>
                      <p className="leading-relaxed text-slate-400">{content.lesson_summary}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {/* ========================================================================= */}
        {/* MODE 2: INSTRUCTOR EDITING STUDIO */}
        {/* ========================================================================= */}
        {mode === 'edit' && (
          <form onSubmit={handleSaveRevision} className="flex-1 overflow-y-auto p-6 space-y-6">
            <div className="bg-indigo-950/20 border border-indigo-900/40 rounded-xl p-4 flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-indigo-400" />
                  <span>Instructor Review & Curriculum Tuning Studio</span>
                </h3>
                <p className="text-xs text-indigo-200">
                  Editing content increments the lesson version (to v{currentLesson.current_version + 1}), saves a persistent snapshot in SQLite, and marks QC reports STALE until re-run.
                </p>
              </div>

              <button
                type="submit"
                disabled={savingEdit}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs shadow-lg shadow-indigo-600/20 transition cursor-pointer shrink-0"
              >
                <Save className="w-4 h-4" />
                <span>{savingEdit ? 'Saving...' : `Save Revision (v${currentLesson.current_version + 1})`}</span>
              </button>
            </div>

            {/* Core Metadata Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Lesson Title</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Target Audience</label>
                <input
                  type="text"
                  value={editAudience}
                  onChange={(e) => setEditAudience(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Difficulty Level</label>
                <select
                  value={editDifficulty}
                  onChange={(e) => setEditDifficulty(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Estimated Duration (Max 45m)</label>
                <input
                  type="number"
                  min={10}
                  max={45}
                  value={editDuration}
                  onChange={(e) => setEditDuration(parseInt(e.target.value) || 45)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Overview */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Pedagogical Overview & Context</label>
              <textarea
                rows={3}
                value={editOverview}
                onChange={(e) => setEditOverview(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 leading-relaxed"
                placeholder="High-level lesson narrative..."
              />
            </div>

            {/* Learning Objectives */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5" /> Learning Objectives (Bloom-Aligned)
                </label>
                <button
                  type="button"
                  onClick={handleAddObjective}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Objective
                </button>
              </div>

              <div className="space-y-2">
                {editObjectives.map((obj, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="text-xs font-mono text-slate-500 w-5">{idx + 1}.</span>
                    <input
                      type="text"
                      value={obj}
                      onChange={(e) => handleObjectiveChange(idx, e.target.value)}
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                    {editObjectives.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveObjective(idx)}
                        className="p-1.5 text-slate-500 hover:text-rose-400 rounded hover:bg-slate-800 cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Core Concepts */}
            <div className="space-y-4 pt-4 border-t border-slate-800">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5" /> Core Concept Modules ({editConcepts.length})
                </label>
                <button
                  type="button"
                  onClick={handleAddConcept}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Concept Block
                </button>
              </div>

              <div className="space-y-4">
                {editConcepts.map((concept, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 flex-1">
                        <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 font-bold text-xs flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <input
                          type="text"
                          value={concept.title}
                          onChange={(e) => handleConceptChange(idx, 'title', e.target.value)}
                          className="flex-1 bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-sm text-white font-medium focus:outline-none focus:border-indigo-500"
                          placeholder="Concept Title"
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1 text-xs text-slate-400">
                          <Clock className="w-3 h-3" />
                          <input
                            type="number"
                            min={1}
                            max={25}
                            value={concept.estimated_minutes || 5}
                            onChange={(e) => handleConceptChange(idx, 'estimated_minutes', parseInt(e.target.value) || 5)}
                            className="w-12 bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-xs text-white text-center"
                          />
                          <span>m</span>
                        </div>
                        {editConcepts.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveConcept(idx)}
                            className="p-1 text-slate-500 hover:text-rose-400 rounded cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-slate-400">Explanation</label>
                      <textarea
                        rows={3}
                        value={concept.explanation}
                        onChange={(e) => handleConceptChange(idx, 'explanation', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-slate-400">Key Takeaway</label>
                      <input
                        type="text"
                        value={concept.key_takeaway}
                        onChange={(e) => handleConceptChange(idx, 'key_takeaway', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Practical Examples */}
            {editExamples.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <label className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Code className="w-3.5 h-3.5" /> Practical Examples ({editExamples.length})
                </label>

                <div className="space-y-4">
                  {editExamples.map((ex, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3"
                    >
                      <input
                        type="text"
                        value={ex.title}
                        onChange={(e) => handleExampleChange(idx, 'title', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-sm text-white font-medium focus:outline-none focus:border-indigo-500"
                        placeholder="Example Title"
                      />

                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold text-slate-400">Scenario</label>
                        <input
                          type="text"
                          value={ex.scenario}
                          onChange={(e) => handleExampleChange(idx, 'scenario', e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold text-slate-400">Code / Walkthrough</label>
                        <textarea
                          rows={4}
                          value={ex.code_or_walkthrough}
                          onChange={(e) => handleExampleChange(idx, 'code_or_walkthrough', e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono text-emerald-400 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Revision Note & Submit */}
            <div className="pt-4 border-t border-slate-800 space-y-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Revision Changelog / Instructor Notes
                </label>
                <input
                  type="text"
                  value={editorNotes}
                  onChange={(e) => setEditorNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. Added real-world caching section, updated RFC terminology"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setMode('view')}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs shadow-lg shadow-indigo-600/20 transition cursor-pointer"
                >
                  <Save className="w-4 h-4" />
                  <span>{savingEdit ? 'Saving...' : `Save Revision (v${currentLesson.current_version + 1})`}</span>
                </button>
              </div>
            </div>
          </form>
        )}

        {/* ========================================================================= */}
        {/* MODE 3: REVISION HISTORY TIMELINE */}
        {/* ========================================================================= */}
        {mode === 'revisions' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <History className="w-4 h-4 text-indigo-400" />
                  <span>Lesson Revision Audit Trail</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Complete immutable version history snapshotting each instructor modification in SQLite.
                </p>
              </div>
              <button
                onClick={loadRevisions}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition cursor-pointer"
              >
                Refresh Log
              </button>
            </div>

            {loadingRevisions ? (
              <div className="p-12 text-center text-slate-400 text-xs">
                Loading revision snapshots from database...
              </div>
            ) : revisions.length === 0 ? (
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-8 text-center">
                <History className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <h4 className="text-sm font-semibold text-slate-300">Initial Version (v1)</h4>
                <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                  No additional revisions saved yet. Use the Instructor Editor to create v2+ revisions with custom changelog notes.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {revisions.map((rev) => (
                  <div
                    key={rev.id}
                    className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          Revision v{rev.revision_number}
                        </span>
                        <span className="text-xs text-slate-400">
                          {new Date(rev.created_at).toLocaleString()}
                        </span>
                      </div>
                      {rev.revision_number === currentLesson.current_version && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                          Active Version
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-300 bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                      <strong className="text-white">Instructor Notes: </strong>
                      <span>{rev.editor_notes || 'No changelog notes provided'}</span>
                    </div>

                    {rev.content_blocks && rev.content_blocks.core_concepts && (
                      <div className="text-xs text-slate-400 flex items-center gap-2">
                        <span>Concepts in snapshot:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {rev.content_blocks.core_concepts.map((c: any, cIdx: number) => (
                            <span
                              key={cIdx}
                              className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px]"
                            >
                              {c.title || `Concept ${cIdx + 1}`}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs text-slate-400">
          <span>Target Audience: {currentLesson.target_audience} • Difficulty: {currentLesson.difficulty_level}</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition cursor-pointer"
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
};