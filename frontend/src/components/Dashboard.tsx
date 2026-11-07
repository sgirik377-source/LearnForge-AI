import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Award,
  Clock,
  Trash2,
  RefreshCw,
  ListTodo,
  Layers,
  Sparkles,
  Compass,
  CheckCircle2,
  Eye,
  ShieldCheck,
  AlertTriangle,
  FileDown,
  FileSpreadsheet,
  Code
} from 'lucide-react';
import { LessonService } from '../services/api';
import type { LessonSummary, GenerationTask, LessonDetail } from '../types';
import { ResearchLibraryModal } from './research/ResearchLibraryModal';
import { StructuredLessonModal } from './lesson/StructuredLessonModal';
import { DualQCModal } from './qc/DualQCModal';

export const Dashboard: React.FC = () => {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [tasks, setTasks] = useState<GenerationTask[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [creating, setCreating] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);

  // Modals state
  const [selectedResearchLesson, setSelectedResearchLesson] = useState<LessonSummary | null>(null);
  const [viewingLesson, setViewingLesson] = useState<LessonDetail | null>(null);
  const [selectedQCLesson, setSelectedQCLesson] = useState<LessonDetail | null>(null);

  // Active generation task tracking
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [activeTask, setActiveTask] = useState<GenerationTask | null>(null);

  // Form State
  const [title, setTitle] = useState('');
  const [targetAudience, setTargetAudience] = useState('Undergraduate / Intermediate');
  const [difficultyLevel, setDifficultyLevel] = useState('Intermediate');
  const [duration, setDuration] = useState(45);
  const [objectives, setObjectives] = useState<string[]>([
    'Explain the fundamental architecture and working principles',
    'Analyze trade-offs and real-world failure modes'
  ]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [fetchedLessons, fetchedTasks] = await Promise.all([
        LessonService.getLessons(),
        LessonService.getTasks(),
      ]);
      setLessons(fetchedLessons);
      setTasks(fetchedTasks);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Poll active task status
  useEffect(() => {
    if (!activeTaskId) return;

    let isPolling = true;
    const poll = async () => {
      try {
        const task = await LessonService.getTaskStatus(activeTaskId);
        if (isPolling) {
          setActiveTask(task);
          if (task.status === 'COMPLETED' || task.status === 'FAILED') {
            await loadData();
          }
        }
      } catch (err) {
        console.error('Failed to poll task:', err);
      }
    };

    poll();
    const interval = setInterval(poll, 1500);
    return () => {
      isPolling = false;
      clearInterval(interval);
    };
  }, [activeTaskId]);

  const handleAddObjective = () => {
    setObjectives([...objectives, '']);
  };

  const handleObjectiveChange = (index: number, val: string) => {
    const updated = [...objectives];
    updated[index] = val;
    setObjectives(updated);
  };

  const handleRemoveObjective = (index: number) => {
    if (objectives.length > 1) {
      setObjectives(objectives.filter((_, i) => i !== index));
    }
  };

  const handleCreateDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setCreating(true);
    try {
      const validObjectives = objectives.filter(o => o.trim().length > 0);
      await LessonService.createDraft({
        title,
        target_audience: targetAudience,
        difficulty_level: difficultyLevel,
        estimated_duration_mins: Math.min(Number(duration), 45),
        learning_objectives: validObjectives.length > 0 ? validObjectives : ['Understand key concepts'],
      });
      setIsModalOpen(false);
      resetForm();
      await loadData();
    } catch (err) {
      console.error('Failed to create lesson draft:', err);
      alert('Error creating lesson. Please check backend connection.');
    } finally {
      setCreating(false);
    }
  };

  const handleGenerateLesson = async () => {
    if (!title.trim()) {
      alert('Please enter a lesson title.');
      return;
    }

    setGenerating(true);
    try {
      const validObjectives = objectives.filter(o => o.trim().length > 0);
      const res = await LessonService.generateLesson({
        title,
        target_audience: targetAudience,
        difficulty_level: difficultyLevel,
        estimated_duration_mins: Math.min(Number(duration), 45),
        learning_objectives: validObjectives.length > 0 ? validObjectives : ['Understand key concepts'],
      });
      setIsModalOpen(false);
      setActiveTaskId(res.task_id);
      resetForm();
    } catch (err: any) {
      console.error('Generation request failed:', err);
      alert('Failed to start lesson generation: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const resetForm = () => {
    setTitle('');
    setObjectives([
      'Explain the fundamental architecture and working principles',
      'Analyze trade-offs and real-world failure modes'
    ]);
  };

  const handleDeleteLesson = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this lesson?')) return;
    try {
      await LessonService.deleteLesson(id);
      setLessons(lessons.filter(l => l.id !== id));
    } catch (err) {
      console.error('Failed to delete lesson:', err);
    }
  };

  const handleOpenLesson = async (id: string) => {
    try {
      const detail = await LessonService.getLesson(id);
      setViewingLesson(detail);
    } catch (err) {
      console.error('Failed to load lesson detail:', err);
    }
  };

  const handleOpenQC = async (id: string) => {
    try {
      const detail = await LessonService.getLesson(id);
      setSelectedQCLesson(detail);
    } catch (err) {
      console.error('Failed to load lesson for QC:', err);
    }
  };

  // Calculations
  const totalLessons = lessons.length;
  const reviewedCount = lessons.filter(l => l.status === 'REVIEWED' || l.status === 'VERIFIED' || l.status === 'FULLY_REVIEWED').length;
  const generatedCount = lessons.filter(l => !['DRAFT', 'RESEARCHING', 'RESEARCH_FAILED'].includes(l.status)).length;

  return (
    <div className="space-y-8">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Curriculum Studio Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Build, review, and fact-check pedagogical lesson plans backed by external research.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh Dashboard"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-600/20 transition cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate New Lesson</span>
          </button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Modules</span>
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">{totalLessons}</span>
            <span className="text-xs text-slate-400 ml-2">stored in SQLite</span>
          </div>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Synthesized</span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">{generatedCount}</span>
            <span className="text-xs text-slate-400 ml-2">structured modules</span>
          </div>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Fully Reviewed</span>
            <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">{reviewedCount}</span>
            <span className="text-xs text-slate-400 ml-2">instructor verified</span>
          </div>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Tasks</span>
            <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">{tasks.length}</span>
            <span className="text-xs text-slate-400 ml-2">persisted tasks</span>
          </div>
        </div>
      </div>

      {/* Main Content Area: Lessons List */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <span>Lessons & Curricula</span>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
              {lessons.length}
            </span>
          </h2>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
            <p className="text-sm">Loading curricula from SQLite database...</p>
          </div>
        ) : lessons.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-400">
              <BookOpen className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">No lessons created yet</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Click &quot;Generate New Lesson&quot; to synthesize an evidence-grounded curriculum module.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-4 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium inline-flex items-center gap-1.5 transition cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Generate Structured Lesson</span>
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {lessons.map((lesson) => {
              const contentBearingStatuses = ['GENERATED', 'EDITED_PENDING_QC', 'REVIEWED', 'NEEDS_REVISION', 'VERIFIED'];
              const isGenerated = contentBearingStatuses.includes(lesson.status) || lesson.status === 'FULLY_REVIEWED';

              return (
                <div
                  key={lesson.id}
                  className="p-5 hover:bg-slate-800/30 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-white text-base truncate">{lesson.title}</span>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        v{lesson.current_version}
                      </span>
                      {/* Status Pill */}
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                          lesson.status === 'REVIEWED' || lesson.status === 'VERIFIED' || lesson.status === 'FULLY_REVIEWED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : lesson.status === 'NEEDS_REVISION'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : lesson.status === 'EDITED_PENDING_QC'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : lesson.status === 'GENERATED'
                            ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {lesson.status.replace(/_/g, ' ')}
                      </span>

                      {/* QC Score Badges */}
                      {lesson.factual_score !== null && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
                          lesson.factual_score >= 80
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}>
                          Factual: {lesson.factual_score}%
                        </span>
                      )}
                      {lesson.pedagogical_score !== null && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
                          lesson.pedagogical_score >= 80
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}>
                          Pedagogy: {lesson.pedagogical_score}%
                        </span>
                      )}
                      {lesson.is_qc_stale && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3 text-amber-400" /> Stale QC
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-xs text-slate-400 flex-wrap">
                      <span>Audience: {lesson.target_audience}</span>
                      <span>•</span>
                      <span>Level: {lesson.difficulty_level}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" /> {lesson.estimated_duration_mins}m
                      </span>
                    </div>
                  </div>

                  {/* Actions & QC */}
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* View Structured Lesson Button */}
                    {isGenerated && (
                      <button
                        onClick={() => handleOpenLesson(lesson.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition cursor-pointer"
                        title="View Complete Structured Lesson"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View</span>
                      </button>
                    )}

                    {/* Dual QC Button */}
                    {isGenerated && (
                      <button
                        onClick={() => handleOpenQC(lesson.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition cursor-pointer"
                        title="Open Independent Dual Quality Control Audit"
                      >
                        <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                        <span>
                          {['REVIEWED', 'NEEDS_REVISION', 'VERIFIED'].includes(lesson.status)
                            ? 'Re-run QC'
                            : 'Dual QC'}
                        </span>
                      </button>
                    )}

                    {/* Quick Exports */}
                    {isGenerated && (
                      <div className="flex items-center bg-slate-800/80 rounded-lg border border-slate-700/80 p-0.5">
                        <button
                          onClick={() => LessonService.downloadExport(lesson.id, 'pdf')}
                          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-700/60 rounded transition cursor-pointer"
                          title="Quick Export: PDF Document"
                        >
                          <FileDown className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => LessonService.downloadExport(lesson.id, 'docx')}
                          className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-700/60 rounded transition cursor-pointer"
                          title="Quick Export: Word Document (.docx)"
                        >
                          <FileSpreadsheet className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => LessonService.downloadExport(lesson.id, 'json')}
                          className="p-1.5 text-slate-400 hover:text-amber-400 hover:bg-slate-700/60 rounded transition cursor-pointer"
                          title="Quick Export: JSON Archive"
                        >
                          <Code className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}

                    {/* Research Sources Button */}
                    <button
                      onClick={() => setSelectedResearchLesson(lesson)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition cursor-pointer"
                      title="Open Multimodal Research Library"
                    >
                      <Compass className="w-3.5 h-3.5" />
                      <span>Research</span>
                    </button>

                    <button
                      onClick={(e) => handleDeleteLesson(lesson.id, e)}
                      className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition cursor-pointer"
                      title="Delete Lesson"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Persisted Background Tasks History Tray */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ListTodo className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Persisted SQLite Task History</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">Preserved across backend restarts</span>
        </div>

        {tasks.length === 0 ? (
          <p className="text-xs text-slate-500">No background pipeline executions recorded.</p>
        ) : (
          <div className="space-y-2">
            {tasks.slice(0, 8).map(task => (
              <div
                key={task.id}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      task.status === 'COMPLETED'
                        ? 'bg-emerald-400'
                        : task.status === 'FAILED'
                        ? 'bg-rose-500'
                        : 'bg-indigo-400 animate-pulse'
                    }`}
                  />
                  <span className="font-mono text-slate-300">{task.task_type}</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-slate-400 truncate max-w-sm">{task.current_step}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400 font-medium">{task.progress_percent}%</span>
                  <span className="text-slate-500 font-mono text-[11px]">
                    {new Date(task.created_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Active Generation Progress Modal */}
      {activeTaskId && activeTask && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <span>AI Lesson Generation Pipeline</span>
              </h2>
              {activeTask.status === 'COMPLETED' || activeTask.status === 'FAILED' ? (
                <button
                  onClick={() => {
                    setActiveTaskId(null);
                    setActiveTask(null);
                  }}
                  className="text-slate-400 hover:text-white text-xs cursor-pointer"
                >
                  ✕
                </button>
              ) : null}
            </div>

            <div className="space-y-4">
              {/* Progress Bar */}
              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium">
                  <span className="uppercase text-indigo-400">{activeTask.status}</span>
                  <span>{activeTask.progress_percent}%</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div
                    className={`h-full transition-all duration-500 ${
                      activeTask.status === 'COMPLETED'
                        ? 'bg-emerald-500'
                        : activeTask.status === 'FAILED'
                        ? 'bg-rose-500'
                        : 'bg-indigo-600'
                    }`}
                    style={{ width: `${activeTask.progress_percent}%` }}
                  />
                </div>
              </div>

              {/* Current Step Description */}
              <p className="text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800 leading-relaxed">
                {activeTask.current_step}
              </p>

              {/* Error Message if Failed */}
              {activeTask.error_message && (
                <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/50 text-xs text-rose-300">
                  <strong>Generation Error: </strong>
                  {activeTask.error_message}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2">
                {activeTask.status === 'COMPLETED' && activeTask.lesson_id && (
                  <button
                    onClick={() => {
                      const id = activeTask.lesson_id!;
                      setActiveTaskId(null);
                      setActiveTask(null);
                      handleOpenLesson(id);
                    }}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-md cursor-pointer"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Generated Lesson</span>
                  </button>
                )}

                {(activeTask.status === 'COMPLETED' || activeTask.status === 'FAILED') && (
                  <button
                    onClick={() => {
                      setActiveTaskId(null);
                      setActiveTask(null);
                    }}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium cursor-pointer"
                  >
                    Close
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Lesson Creation Wizard Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <span>Initialize Structured Lesson</span>
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDraft} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Lesson Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Distributed Consensus in Raft and Paxos"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Difficulty Level
                  </label>
                  <select
                    value={difficultyLevel}
                    onChange={(e) => setDifficultyLevel(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Max Duration (Minutes)
                  </label>
                  <input
                    type="number"
                    min="15"
                    max="45"
                    value={duration}
                    onChange={(e) => setDuration(Math.min(Number(e.target.value), 45))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                  <span className="text-[11px] text-slate-400 mt-0.5 block">Max duration 45 mins</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Target Audience
                </label>
                <input
                  type="text"
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-300 uppercase">
                    Learning Objectives
                  </label>
                  <button
                    type="button"
                    onClick={handleAddObjective}
                    className="text-xs text-indigo-400 hover:text-indigo-300 cursor-pointer"
                  >
                    + Add Objective
                  </button>
                </div>
                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                  {objectives.map((obj, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={obj}
                        onChange={(e) => handleObjectiveChange(i, e.target.value)}
                        placeholder={`Objective #${i + 1}`}
                        className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                      {objectives.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveObjective(i)}
                          className="text-slate-500 hover:text-rose-400 text-xs px-1 cursor-pointer"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-800">
                <button
                  type="submit"
                  disabled={creating}
                  className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium cursor-pointer"
                >
                  Create Empty Draft
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs font-medium cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleGenerateLesson}
                    disabled={generating}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium flex items-center gap-1.5 shadow-md shadow-indigo-600/20 cursor-pointer"
                  >
                    {generating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                    <span>Synthesize with Gemini</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Research Library Modal */}
      {selectedResearchLesson && (
        <ResearchLibraryModal
          lesson={selectedResearchLesson}
          onClose={() => {
            setSelectedResearchLesson(null);
            loadData();
          }}
        />
      )}

      {/* Structured Lesson Viewer & Editor Modal */}
      {viewingLesson && (
        <StructuredLessonModal
          lesson={viewingLesson}
          onClose={() => {
            setViewingLesson(null);
            loadData();
          }}
          onLessonUpdated={(updated) => {
            setViewingLesson(updated);
            loadData();
          }}
          onOpenQC={(id) => {
            setViewingLesson(null);
            handleOpenQC(id);
          }}
        />
      )}

      {/* Dual Quality Control Audit Modal */}
      {selectedQCLesson && (
        <DualQCModal
          lesson={selectedQCLesson}
          isOpen={Boolean(selectedQCLesson)}
          onClose={() => {
            setSelectedQCLesson(null);
            loadData();
          }}
          onQCUpdated={loadData}
        />
      )}
    </div>
  );
};
