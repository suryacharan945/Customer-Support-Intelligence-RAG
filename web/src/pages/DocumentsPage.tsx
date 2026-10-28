import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Files, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import { UploadDropzone } from '../components/documents/UploadDropzone';
import { DocumentTable } from '../components/documents/DocumentTable';
import { Button } from '../components/common/Button';

export const DocumentsPage: React.FC = () => {
  const {
    data: docResponse,
    isLoading,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['documents-list'],
    queryFn: () => apiClient.listDocuments(),
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <Files className="w-5 h-5 text-indigo-400" />
            Knowledge Base Studio
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage enterprise document lifecycle, format validation, chunking, and ChromaDB searchability.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          loading={isRefetching}
          icon={<RefreshCw className="w-3.5 h-3.5 text-cyan-400" />}
        >
          Refresh Manifest
        </Button>
      </div>

      {/* 1. Upload & Ingest Dropzone */}
      <UploadDropzone onSuccess={() => refetch()} />

      {/* 2. Document Registry Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-200">
            Registered Documents ({docResponse?.total ?? 0})
          </h3>
          <span className="text-[11px] text-slate-400">
            Only documents with verified state <strong className="text-emerald-400">Indexed</strong> are searchable.
          </span>
        </div>

        <DocumentTable
          documents={docResponse?.documents ?? []}
          onRefresh={() => refetch()}
          loading={isLoading}
        />
      </div>
    </div>
  );
};
