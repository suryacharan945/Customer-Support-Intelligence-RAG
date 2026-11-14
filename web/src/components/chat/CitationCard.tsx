import React, { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, CheckCircle2, Bookmark, Layers, ExternalLink } from 'lucide-react';
import { Citation } from '../../api/types';
import { CategoryBadge } from '../common/Badge';
import { EvidenceDrawer } from './EvidenceDrawer';

interface CitationProps {
  supportingCitations: Citation[];
  candidateCitations?: Citation[];
  queryContext?: string;
}

export const CitationCard: React.FC<CitationProps> = ({
  supportingCitations,
  candidateCitations = [],
  queryContext,
}) => {
  const [expanded, setExpanded] = useState<boolean>(true);
  const [showCandidates, setShowCandidates] = useState<boolean>(false);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);

  if (!supportingCitations.length && !candidateCitations.length) {
    return null;
  }

  const handleOpenDrawer = (cite: Citation) => {
    setActiveCitation(cite);
    setDrawerOpen(true);
  };

  const getDocTypeIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return '📄 PDF';
    if (ext === 'md') return '📝 MD';
    if (ext === 'txt') return '📃 TXT';
    return '📁 DOC';
  };

  return (
    <div className="mt-4 rounded-xl border border-slate-700/60 bg-slate-900/60 overflow-hidden text-xs">
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left font-semibold text-slate-200 hover:bg-slate-800/40 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Bookmark className="w-4 h-4 text-cyan-400" />
          <span>Verified Supporting Evidence ({supportingCitations.length} Citations)</span>
        </span>
        <div className="flex items-center gap-2 text-slate-400">
          <span className="text-[11px] font-normal text-slate-400">
            {expanded ? 'Collapse' : 'Expand'}
          </span>
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Verified Citations List */}
      {expanded && (
        <div className="p-3 pt-0 space-y-2.5">
          {supportingCitations.map((cite, idx) => (
            <div
              key={`${cite.chunk_id || idx}_${idx}`}
              className="p-3 rounded-lg bg-[#151D32] border border-slate-700/60 space-y-1.5 hover:border-indigo-500/40 transition-all cursor-pointer group"
              onClick={() => handleOpenDrawer(cite)}
              title="Click to inspect verbatim retrieved excerpt in evidence drawer"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-bold text-slate-100 flex items-center gap-1.5 text-xs group-hover:text-cyan-300 transition-colors">
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="truncate max-w-[280px] sm:max-w-md">{cite.document_source}</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                    {getDocTypeIcon(cite.document_source)}
                  </span>
                </span>
                <div className="flex items-center gap-1.5">
                  {cite.category && <CategoryBadge category={cite.category} />}
                  <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/30">
                    <CheckCircle2 className="w-3 h-3" />
                    Verified
                  </span>
                  <button
                    type="button"
                    aria-label="Inspect evidence"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenDrawer(cite);
                    }}
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5 ml-1 px-1.5 py-0.5 rounded bg-indigo-500/10 hover:bg-indigo-500/20 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Inspect
                  </button>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 flex flex-wrap items-center gap-x-3 gap-y-1">
                <span>Location: {cite.page_or_section || 'Full Document'}</span>
                {cite.chunk_id && (
                  <span className="font-mono text-slate-500 text-[10px]">Chunk: {cite.chunk_id}</span>
                )}
                <span>Score: {Math.round(cite.relevance_score * 100)}%</span>
              </div>

              <div className="p-2 rounded bg-slate-900/90 border border-slate-800 text-slate-300 font-mono text-[11px] leading-relaxed line-clamp-3 group-hover:bg-slate-900 transition-colors">
                "{cite.snippet}"
              </div>
            </div>
          ))}

          {/* Optional background candidate passages */}
          {candidateCitations.length > supportingCitations.length && (
            <div className="mt-3 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowCandidates(!showCandidates)}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
              >
                <Layers className="w-3 h-3" />
                {showCandidates
                  ? 'Hide Uncited Candidate Contexts'
                  : `Show ${candidateCitations.length - supportingCitations.length} Additional Background Retrieved Chunks`}
              </button>

              {showCandidates && (
                <div className="mt-2 space-y-2 opacity-85">
                  {candidateCitations.map((cand, i) => (
                    <div
                      key={`cand_${i}`}
                      className="p-2.5 rounded bg-slate-950/70 border border-slate-800 text-[11px] space-y-1 hover:border-slate-700 cursor-pointer"
                      onClick={() => handleOpenDrawer(cand)}
                      title="Click to view candidate excerpt in drawer"
                    >
                      <div className="flex items-center justify-between text-slate-400">
                        <span className="font-medium text-slate-300">
                          [Candidate #{i + 1}] {cand.document_source} ({cand.page_or_section || 'Full Document'})
                        </span>
                        <span className="text-slate-500">
                          Score: {Math.round(cand.relevance_score * 100)}%
                        </span>
                      </div>
                      <p className="text-slate-400 font-mono text-[10px] truncate">{cand.snippet}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Slide-over Evidence Drawer */}
      <EvidenceDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        citation={activeCitation}
        query={queryContext}
      />
    </div>
  );
};
