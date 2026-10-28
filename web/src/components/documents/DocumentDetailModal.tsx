import React from 'react';
import { FileText, Calendar, Hash, HardDrive, CheckCircle } from 'lucide-react';
import { Modal } from '../common/Modal';
import { DocumentSummary } from '../../api/types';
import { LifecycleBadge, CategoryBadge } from '../common/Badge';

interface DocumentDetailModalProps {
  document: DocumentSummary | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  document,
  open,
  onOpenChange,
}) => {
  if (!document) return null;

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={document.filename}
      description={`Document ID: ${document.document_id}`}
    >
      <div className="space-y-4 pt-2 text-xs">
        {/* Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <CategoryBadge category={document.category} />
          <LifecycleBadge
            status={document.lifecycle_status}
            isSearchable={document.is_searchable}
          />
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="space-y-1">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              Document Type
            </span>
            <span className="text-slate-200 font-bold uppercase">{document.document_type}</span>
          </div>

          <div className="space-y-1">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5 text-cyan-400" />
              Chunks Generated
            </span>
            <span className="text-slate-200 font-bold">{document.chunk_count} Chunks</span>
          </div>

          <div className="space-y-1">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <HardDrive className="w-3.5 h-3.5 text-amber-400" />
              File Size
            </span>
            <span className="text-slate-200 font-bold">
              {(document.file_size_bytes / 1024).toFixed(1)} KB
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              Version
            </span>
            <span className="text-slate-200 font-bold">v{document.version}</span>
          </div>

          <div className="col-span-2 space-y-1 pt-1 border-t border-slate-800">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-purple-400" />
              First Ingested
            </span>
            <span className="text-slate-300 font-mono text-[11px] block">
              {document.first_ingested || 'N/A'}
            </span>
          </div>
        </div>

        {/* Searchability note */}
        <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-500/20 text-slate-300 leading-relaxed">
          {document.is_searchable ? (
            <p>
              ✅ This document is fully indexed in ChromaDB vector space and BM25 index. It actively participates in both Baseline dense search and Multi-Context hybrid retrieval.
            </p>
          ) : (
            <p className="text-amber-300">
              ⚠️ This document is not currently searchable. Only documents with verified state <code className="text-amber-200 font-bold">indexed</code> are queried by the RAG pipeline.
            </p>
          )}
        </div>
      </div>
    </Modal>
  );
};
