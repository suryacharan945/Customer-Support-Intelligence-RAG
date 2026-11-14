import React, { useEffect } from 'react';
import { X, FileText, CheckCircle2, Bookmark, Layers, Hash, MapPin, Gauge, Copy, Check, Info } from 'lucide-react';
import { Citation } from '../../api/types';
import { CategoryBadge } from '../common/Badge';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  citation: Citation | null;
  query?: string;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  isOpen,
  onClose,
  citation,
  query,
}) => {
  const [copied, setCopied] = React.useState<boolean>(false);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !citation) {
    return null;
  }

  const handleCopy = () => {
    if (citation.snippet) {
      navigator.clipboard.writeText(citation.snippet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getDocTypeIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return '📄 PDF Document';
    if (ext === 'md') return '📝 Markdown Document';
    if (ext === 'txt') return '📃 Text Document';
    return '📁 Technical Document';
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden"
      aria-labelledby="evidence-drawer-title"
      role="dialog"
      aria-modal="true"
    >
      {/* Dimmed Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-[#0F172A] border-l border-slate-700/80 shadow-2xl flex flex-col text-slate-100">
          {/* Header */}
          <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-[#151D32]">
            <div className="space-y-1 pr-4">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold tracking-wider uppercase bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  {getDocTypeIcon(citation.document_source)}
                </span>
                <span className="text-xs text-slate-400">Verified Evidence Excerpt</span>
              </div>
              <h3
                id="evidence-drawer-title"
                className="text-base font-bold text-white leading-snug break-words"
              >
                {citation.document_source}
              </h3>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              aria-label="Close evidence drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Metadata Grid */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400" /> Location
                </span>
                <p className="font-semibold text-slate-200">
                  {citation.page_or_section || 'Full Document'}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                  <Hash className="w-3.5 h-3.5 text-cyan-400" /> Chunk Identifier
                </span>
                <p className="font-mono font-medium text-slate-200 text-[11px] truncate" title={citation.chunk_id || ''}>
                  {citation.chunk_id || 'Not specified'}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                  <Gauge className="w-3.5 h-3.5 text-emerald-400" /> Retrieval Relevance
                </span>
                <p className="font-semibold text-slate-200">
                  {Math.round(citation.relevance_score * 100)}% relevance score
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                  <Layers className="w-3.5 h-3.5 text-amber-400" /> Domain Category
                </span>
                <div>
                  <CategoryBadge category={citation.category || 'general'} />
                </div>
              </div>
            </div>

            {/* Verified Status Banner */}
            <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 flex items-start gap-3 text-xs">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                <span className="font-bold text-emerald-300 block">
                  Citation ID Validity Verified
                </span>
                <p className="text-emerald-200/80 leading-relaxed text-[11px]">
                  Verification Scope: Programmatically confirmed that this chunk ID, source filename, and location metadata exist in the retrieved candidate container and meet lexical overlap thresholds (&ge; 20%). Does not imply automated semantic claim verification or human-reviewed factual correctness.
                </p>
              </div>
            </div>

            {/* Verbatim Evidence Excerpt */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Bookmark className="w-3.5 h-3.5 text-indigo-400" />
                  Verbatim Retrieved Chunk Text
                </span>
                <button
                  type="button"
                  onClick={handleCopy}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 text-xs transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400 font-medium">Copied Excerpt</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Excerpt</span>
                    </>
                  )}
                </button>
              </div>

              {citation.snippet ? (
                <div className="p-4 rounded-xl bg-[#0B1020] border border-slate-800 text-slate-200 font-mono text-xs leading-relaxed whitespace-pre-wrap select-text">
                  {citation.snippet}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-slate-900/50 border border-dashed border-slate-800 text-slate-400 text-xs text-center">
                  No excerpt text was delivered in the citation payload. The citation metadata above is verified from knowledge base records.
                </div>
              )}
            </div>

            {/* Active Query Context (if provided) */}
            {query && (
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1 text-xs">
                <span className="text-[11px] text-slate-400 font-medium block">
                  Grounding Query Context
                </span>
                <p className="text-slate-200 italic font-sans text-xs">"{query}"</p>
              </div>
            )}

            {/* Methodological Provenance Note */}
            <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800/80 flex items-start gap-2.5 text-[11px] text-slate-400">
              <Info className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
              <p className="leading-relaxed">
                <strong>Methodology Note:</strong> Citation validation verifies chunk ID delivery, source metadata integrity, and lexical token containment ($\ge 20\%$ threshold). Semantic claim verification and factual correctness across novel domains remain subject to human verification.
              </p>
            </div>
          </div>

          {/* Drawer Footer */}
          <div className="p-4 border-t border-slate-800 bg-[#151D32] flex items-center justify-between text-xs text-slate-400">
            <span>Source: {citation.document_source}</span>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
