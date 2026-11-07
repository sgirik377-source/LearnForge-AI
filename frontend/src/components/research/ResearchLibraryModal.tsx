import React, { useState, useEffect } from 'react';
import {
  Globe,
  Book,
  Video,
  ExternalLink,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ChevronDown,
  ChevronUp,
  Trash2,
  Sparkles,
  Info
} from 'lucide-react';
import { LessonService } from '../../services/api';
import type { LessonSummary, ResearchSource } from '../../types';

interface ResearchLibraryModalProps {
  lesson: LessonSummary;
  onClose: () => void;
}

export const ResearchLibraryModal: React.FC<ResearchLibraryModalProps> = ({ lesson, onClose }) => {
  const [sources, setSources] = useState<ResearchSource[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [harvesting, setHarvesting] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'all' | 'web' | 'book' | 'youtube'>('all');
  const [expandedContentId, setExpandedContentId] = useState<string | null>(null);
  const [providerErrors, setProviderErrors] = useState<Record<string, string>>({});
  const [notification, setNotification] = useState<string | null>(null);

  const fetchSources = async () => {
    setLoading(true);
    try {
      const data = await LessonService.getSources(lesson.id);
      setSources(data);
    } catch (err) {
      console.error('Failed to load sources:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, [lesson.id]);

  const handleHarvest = async () => {
    setHarvesting(true);
    setNotification(null);
    try {
      const res = await LessonService.harvestResearch(lesson.id, 3);
      setSources(res.sources);
      setProviderErrors(res.provider_errors || {});
      setNotification(
        `Successfully harvested ${res.total_harvested} sources (${res.accessible_count} with groundable text, ${res.metadata_only_count} metadata-only).`
      );
    } catch (err: any) {
      console.error('Harvesting failed:', err);
      alert('Research harvest failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setHarvesting(false);
    }
  };

  const handleDeleteSource = async (sourceId: string) => {
    if (!window.confirm('Remove this research source?')) return;
    try {
      await LessonService.deleteSource(lesson.id, sourceId);
      setSources(sources.filter((s) => s.id !== sourceId));
    } catch (err) {
      console.error('Failed to delete source:', err);
    }
  };

  const filteredSources = sources.filter((s) => {
    if (activeTab === 'all') return true;
    return s.source_type === activeTab;
  });

  const accessibleCount = sources.filter((s) => s.is_content_accessible).length;
  const metadataOnlyCount = sources.filter((s) => !s.is_content_accessible).length;

  const webCount = sources.filter((s) => s.source_type === 'web').length;
  const bookCount = sources.filter((s) => s.source_type === 'book').length;
  const youtubeCount = sources.filter((s) => s.source_type === 'youtube').length;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Phase 2 Research Harvester
              </span>
              <span className="text-xs text-slate-400">Lesson ID: {lesson.id.slice(0, 8)}...</span>
            </div>
            <h2 className="text-lg font-bold text-white mt-1 flex items-center gap-2">
              <span>{lesson.title}</span>
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleHarvest}
              disabled={harvesting}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium shadow-md shadow-indigo-600/20 transition cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${harvesting ? 'animate-spin' : ''}`} />
              <span>{harvesting ? 'Querying Web, Books & YouTube...' : 'Harvest Multimodal Research'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Metrics Banner */}
        <div className="bg-slate-950/40 px-6 py-3 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="text-slate-400">
              Total Sources: <strong className="text-white">{sources.length}</strong>
            </span>
            <span className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{accessibleCount} Groundable Content Excerpts</span>
            </span>
            <span className="flex items-center gap-1.5 text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-md border border-amber-500/20">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{metadataOnlyCount} Bibliographic / Metadata-Only</span>
            </span>
          </div>

          <div className="text-[11px] text-slate-400 flex items-center gap-1">
            <Info className="w-3 h-3 text-slate-400" />
            <span>Honest Accessibility Disclosure Active</span>
          </div>
        </div>

        {/* Status Notification */}
        {notification && (
          <div className="bg-indigo-950/40 border-b border-indigo-800/50 px-6 py-2.5 text-xs text-indigo-300 flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{notification}</span>
          </div>
        )}

        {/* Provider Errors Alert if any */}
        {Object.keys(providerErrors).length > 0 && (
          <div className="bg-amber-950/30 border-b border-amber-800/40 px-6 py-2 text-xs text-amber-300 flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>
              Provider notices: {Object.entries(providerErrors).map(([k, v]) => `${k.toUpperCase()} (${v})`).join('; ')}
            </span>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 px-6 pt-4 border-b border-slate-800 bg-slate-900">
          <button
            onClick={() => setActiveTab('all')}
            className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'all'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>All Sources</span>
            <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[11px]">{sources.length}</span>
          </button>

          <button
            onClick={() => setActiveTab('web')}
            className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'web'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Web Articles & Docs</span>
            <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[11px]">{webCount}</span>
          </button>

          <button
            onClick={() => setActiveTab('book')}
            className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'book'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Book className="w-3.5 h-3.5" />
            <span>Books & Textbooks</span>
            <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[11px]">{bookCount}</span>
          </button>

          <button
            onClick={() => setActiveTab('youtube')}
            className={`pb-3 px-3 text-xs font-medium border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'youtube'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>YouTube Lectures</span>
            <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[11px]">{youtubeCount}</span>
          </button>
        </div>

        {/* Sources List Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              <p className="text-sm">Loading research library from SQLite...</p>
            </div>
          ) : harvesting ? (
            <div className="p-12 text-center">
              <div className="w-12 h-12 bg-indigo-500/10 border border-indigo-500/30 rounded-full flex items-center justify-center mx-auto mb-3 text-indigo-400">
                <RefreshCw className="w-6 h-6 animate-spin" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200">Executing Multimodal Harvest</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Querying Web Articles via BeautifulSoup, Google Books / Open Library monographs, and fetching YouTube lecture transcripts.
              </p>
            </div>
          ) : filteredSources.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-400">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200">
                {sources.length === 0 ? 'No research sources collected yet' : 'No sources under this tab'}
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                {sources.length === 0
                  ? 'Click "Harvest Multimodal Research" above to automatically retrieve verified external materials.'
                  : 'Switch tabs or harvest fresh sources to populate this category.'}
              </p>
              {sources.length === 0 && (
                <button
                  onClick={handleHarvest}
                  className="mt-4 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium inline-flex items-center gap-1.5 cursor-pointer shadow-md"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Start Harvest Pipeline</span>
                </button>
              )}
            </div>
          ) : (
            filteredSources.map((source) => {
              const isExpanded = expandedContentId === source.id;

              return (
                <div
                  key={source.id}
                  className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 hover:border-slate-700/80 transition space-y-3"
                >
                  {/* Top Bar: Citation Tag, Source Type, Accessibility Badge */}
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                        {source.citation_tag}
                      </span>

                      <span className="flex items-center gap-1 text-xs text-slate-300 bg-slate-800/80 px-2 py-0.5 rounded">
                        {source.source_type === 'web' && <Globe className="w-3 h-3 text-blue-400" />}
                        {source.source_type === 'book' && <Book className="w-3 h-3 text-amber-400" />}
                        {source.source_type === 'youtube' && <Video className="w-3 h-3 text-rose-400" />}
                        <span className="capitalize">{source.source_type}</span>
                      </span>

                      {/* Accessibility status badge */}
                      {source.is_content_accessible ? (
                        <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>
                            {source.preview_type === 'transcript'
                              ? 'Spoken Transcript Verified'
                              : source.preview_type === 'snippet'
                              ? 'Search Snippet Verified'
                              : 'Full Text Extracted'}
                          </span>
                        </span>
                      ) : (
                        <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" />
                          <span>Metadata Only — No Full Text</span>
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {source.url_or_identifier && source.url_or_identifier.startsWith('http') && (
                        <a
                          href={source.url_or_identifier}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-slate-400 hover:text-indigo-400 flex items-center gap-1 bg-slate-900 px-2.5 py-1 rounded border border-slate-800 transition"
                        >
                          <span>Open Source</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                      <button
                        onClick={() => handleDeleteSource(source.id)}
                        className="p-1.5 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-900 transition cursor-pointer"
                        title="Delete Source"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Title & Author */}
                  <div>
                    <h3 className="font-semibold text-white text-sm">{source.title}</h3>
                    {source.author_or_channel && (
                      <p className="text-xs text-slate-400 mt-0.5">Author / Provider: {source.author_or_channel}</p>
                    )}
                  </div>

                  {/* Scope Note Callout */}
                  {source.verification_scope_note && (
                    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-300 flex items-start gap-2">
                      <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{source.verification_scope_note}</span>
                    </div>
                  )}

                  {/* Key Takeaways */}
                  {source.key_takeaways && (
                    <div className="text-xs text-slate-400 leading-relaxed bg-slate-950/40 p-2.5 rounded border border-slate-800/40">
                      <strong className="text-slate-300">Summary: </strong>
                      {source.key_takeaways}
                    </div>
                  )}

                  {/* Collapsible Extracted Content Drawer */}
                  {source.extracted_content && (
                    <div className="pt-1">
                      <button
                        onClick={() => setExpandedContentId(isExpanded ? null : source.id)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 cursor-pointer"
                      >
                        <span>{isExpanded ? 'Hide Raw Extracted Text' : 'Inspect Grounding Text'}</span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>

                      {isExpanded && (
                        <div className="mt-2 p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 max-h-48 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                          {source.extracted_content}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span>Sources persisted in SQLite and associated with lesson</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
