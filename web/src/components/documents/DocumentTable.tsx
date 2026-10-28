import React, { useState } from 'react';
import { Search, Filter, Trash2, Eye, FileText, AlertTriangle } from 'lucide-react';
import { DocumentSummary } from '../../api/types';
import { LifecycleBadge, CategoryBadge } from '../common/Badge';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';
import { DocumentDetailModal } from './DocumentDetailModal';
import { apiClient } from '../../api/client';

interface DocumentTableProps {
  documents: DocumentSummary[];
  onRefresh: () => void;
  loading?: boolean;
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents,
  onRefresh,
  loading = false,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedDoc, setSelectedDoc] = useState<DocumentSummary | null>(null);
  const [detailOpen, setDetailOpen] = useState<boolean>(false);
  const [deleteDoc, setDeleteDoc] = useState<DocumentSummary | null>(null);
  const [deleting, setDeleting] = useState<boolean>(false);
  const [deleteError, setDeleteError] = useState<string>('');

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || doc.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const handleDelete = async () => {
    if (!deleteDoc) return;
    setDeleting(true);
    setDeleteError('');

    try {
      await apiClient.deleteDocument(deleteDoc.document_id);
      setDeleteDoc(null);
      onRefresh();
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete document');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="rounded-2xl bg-[#151D32] border border-slate-700/70 shadow-xl overflow-hidden">
      {/* Table Controls */}
      <div className="p-4 border-b border-slate-700/70 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/40">
        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by filename..."
            className="w-full text-xs bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-full sm:w-auto"
          >
            <option value="all">All Categories</option>
            <option value="product_manual">product_manual</option>
            <option value="troubleshooting">troubleshooting</option>
            <option value="warranty">warranty</option>
            <option value="faq">faq</option>
          </select>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-700/80">
            <tr>
              <th className="py-3 px-4">Document Filename</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4">Lifecycle Status</th>
              <th className="py-3 px-4">Chunks</th>
              <th className="py-3 px-4">Size</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {filteredDocs.length > 0 ? (
              filteredDocs.map((doc) => (
                <tr key={doc.document_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-200 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                    <span className="truncate max-w-xs">{doc.filename}</span>
                  </td>
                  <td className="py-3 px-4">
                    <CategoryBadge category={doc.category} />
                  </td>
                  <td className="py-3 px-4">
                    <LifecycleBadge
                      status={doc.lifecycle_status}
                      isSearchable={doc.is_searchable}
                    />
                  </td>
                  <td className="py-3 px-4 font-mono font-medium text-slate-300">
                    {doc.chunk_count}
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    {(doc.file_size_bytes / 1024).toFixed(1)} KB
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          setSelectedDoc(doc);
                          setDetailOpen(true);
                        }}
                        title="View Details"
                      >
                        <Eye className="w-4 h-4 text-slate-400 hover:text-white" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => setDeleteDoc(doc)}
                        title="Atomically Delete Document"
                      >
                        <Trash2 className="w-4 h-4 text-rose-400 hover:text-rose-300" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400">
                  {loading ? (
                    'Loading knowledge base documents...'
                  ) : (
                    <div>
                      <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                      <p className="font-semibold text-slate-300">No documents found</p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Try modifying your search or upload a new document above.
                      </p>
                    </div>
                  )}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Document Detail Modal */}
      <DocumentDetailModal
        document={selectedDoc}
        open={detailOpen}
        onOpenChange={setDetailOpen}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        open={!!deleteDoc}
        onOpenChange={(open) => !open && setDeleteDoc(null)}
        title="Confirm Atomic Document Deletion"
        description="This action will permanently purge the document across ChromaDB vector space, BM25 sparse index, and disk storage."
      >
        <div className="space-y-4 pt-2 text-xs">
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-200 flex items-start gap-2.5">
            <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <div>
              <span className="font-bold block">Permanent Deletion Warning</span>
              Are you sure you want to delete{' '}
              <strong className="text-white">"{deleteDoc?.filename}"</strong>? All associated
              embeddings and chunks will be removed immediately.
            </div>
          </div>

          {deleteError && (
            <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-300">
              {deleteError}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setDeleteDoc(null)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              size="sm"
              loading={deleting}
              onClick={handleDelete}
            >
              Delete Document
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
