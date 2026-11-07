import axios from 'axios';
import type {
  LessonSummary,
  LessonDetail,
  ResearchSource,
  FactualQCReport,
  InstructionalQCReport,
  DualQCResponse,
  QCSummaryResponse,
  LessonRevision,
  LessonUpdatePayload,
  GenerationTask
} from '../types';

const API_BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const LessonService = {
  getLessons: async (): Promise<LessonSummary[]> => {
    const res = await api.get<LessonSummary[]>('/lessons');
    return res.data;
  },

  getLesson: async (id: string): Promise<LessonDetail> => {
    const res = await api.get<LessonDetail>(`/lessons/${id}`);
    return res.data;
  },

  createDraft: async (data: {
    title: string;
    learning_objectives: string[];
    target_audience?: string;
    difficulty_level?: string;
    estimated_duration_mins?: number;
  }): Promise<LessonDetail> => {
    const res = await api.post<LessonDetail>('/lessons', data);
    return res.data;
  },

  generateLesson: async (data: {
    title: string;
    learning_objectives: string[];
    target_audience?: string;
    difficulty_level?: string;
    estimated_duration_mins?: number;
  }): Promise<{ status: string; task_id: string; lesson_id: string; message: string }> => {
    const res = await api.post('/lessons/generate', data);
    return res.data;
  },

  getTaskStatus: async (taskId: string): Promise<GenerationTask> => {
    const res = await api.get<GenerationTask>(`/tasks/${taskId}`);
    return res.data;
  },

  updateLesson: async (id: string, data: LessonUpdatePayload): Promise<LessonDetail> => {
    const res = await api.put<LessonDetail>(`/lessons/${id}`, data);
    return res.data;
  },

  deleteLesson: async (id: string): Promise<void> => {
    await api.delete(`/lessons/${id}`);
  },

  getSources: async (lessonId: string): Promise<ResearchSource[]> => {
    const res = await api.get<ResearchSource[]>(`/research/${lessonId}/sources`);
    return res.data;
  },

  harvestResearch: async (lessonId: string, maxPerProvider: number = 3): Promise<{
    status: string;
    task_id: string;
    total_harvested: number;
    accessible_count: number;
    metadata_only_count: number;
    provider_errors: Record<string, string>;
    sources: ResearchSource[];
  }> => {
    const res = await api.post(`/research/${lessonId}/harvest?max_per_provider=${maxPerProvider}`);
    return res.data;
  },

  deleteSource: async (lessonId: string, sourceId: string): Promise<void> => {
    await api.delete(`/research/${lessonId}/sources/${sourceId}`);
  },

  getFactualQC: async (lessonId: string): Promise<FactualQCReport> => {
    const res = await api.get<FactualQCReport>(`/qc/${lessonId}/factual`);
    return res.data;
  },

  runFactualQC: async (lessonId: string): Promise<FactualQCReport> => {
    const res = await api.post<FactualQCReport>(`/qc/${lessonId}/factual`);
    return res.data;
  },

  getInstructionalQC: async (lessonId: string): Promise<InstructionalQCReport> => {
    const res = await api.get<InstructionalQCReport>(`/qc/${lessonId}/instructional`);
    return res.data;
  },

  runInstructionalQC: async (lessonId: string): Promise<InstructionalQCReport> => {
    const res = await api.post<InstructionalQCReport>(`/qc/${lessonId}/instructional`);
    return res.data;
  },

  runDualQC: async (lessonId: string): Promise<DualQCResponse> => {
    const res = await api.post<DualQCResponse>(`/qc/${lessonId}/all`);
    return res.data;
  },

  getQCSummary: async (lessonId: string): Promise<QCSummaryResponse> => {
    const res = await api.get<QCSummaryResponse>(`/qc/${lessonId}/summary`);
    return res.data;
  },

  getRevisions: async (lessonId: string): Promise<LessonRevision[]> => {
    const res = await api.get<LessonRevision[]>(`/lessons/${lessonId}/revisions`);
    return res.data;
  },

  downloadExport: (lessonId: string, format: 'json' | 'pdf' | 'docx') => {
    window.open(`/api/v1/lessons/${lessonId}/export/${format}`, '_blank');
  },

  getTasks: async (): Promise<GenerationTask[]> => {
    const res = await api.get<GenerationTask[]>('/tasks');
    return res.data;
  },

  getHealth: async (): Promise<{ status: string; app_name: string; version: string; database: string }> => {
    const res = await api.get('/health');
    return res.data;
  }
};
