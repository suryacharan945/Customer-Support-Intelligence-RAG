import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  CheckCircle2,
  XCircle,
  Cpu,
  RefreshCw,
  AlertTriangle,
  Server,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { useChat } from '../context/ChatContext';

export const SystemStatusPage: React.FC = () => {
  const { llmProvider, setLlmProvider } = useChat();

  const {
    data: readyData,
    refetch: refetchReady,
    isRefetching,
  } = useQuery({
    queryKey: ['system-ready'],
    queryFn: () => apiClient.getReady(),
    refetchInterval: 15000,
  });

  const { data: healthData } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getHealth(),
  });

  const checks = readyData?.checks;
  const isAllReady = readyData?.ready ?? false;

  const subsystems = [
    {
      name: 'Storage & Drive Sync',
      desc: 'Local ephemeral storage & Google Drive root directory',
      ready: checks?.storage ?? false,
      detail: healthData?.storage?.google_drive_connected
        ? `Connected to: ${healthData.storage.google_drive_root}`
        : 'Standby / Local temp storage writable',
    },
    {
      name: 'Ingestion Manifest',
      desc: 'Persistent JSON manifest tracking document lifecycle',
      ready: checks?.manifest ?? false,
      detail: 'Manifest database verified and schema validated',
    },
    {
      name: 'ChromaDB Vector Store',
      desc: 'Local high-performance vector collection for dense retrieval',
      ready: checks?.vector_store ?? false,
      detail: readyData?.details?.vector_store_collection
        ? `Collection: ${readyData.details.vector_store_collection} (${readyData.details.indexed_chunks_count} chunks)`
        : 'Collection initialized',
    },
    {
      name: 'Embedding Model',
      desc: 'sentence-transformers/all-MiniLM-L6-v2',
      ready: checks?.embedding_provider ?? false,
      detail: '384-dimensional dense semantic embedding pipeline',
    },
    {
      name: 'LLM Generation Provider',
      desc: `Configured: ${healthData?.compute?.llm_provider || 'auto'} (${healthData?.compute?.model_name || 'Mistral-7B'})`,
      ready: checks?.llm_provider ?? false,
      detail: 'Supports Colab remote GPU, Local Grounded synthesis, and Auto-Fallback',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            System Status & Deep Readiness Probe
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time diagnostic probe across all 5 operational subsystems.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => refetchReady()}
          loading={isRefetching}
          icon={<RefreshCw className="w-3.5 h-3.5 text-cyan-400" />}
        >
          Re-Run Diagnostic Probe
        </Button>
      </div>

      {/* Global Status Banner */}
      <div
        className={`p-5 rounded-2xl border flex items-center justify-between gap-4 ${
          isAllReady
            ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
            : 'bg-amber-950/30 border-amber-500/40 text-amber-200'
        }`}
      >
        <div className="flex items-center gap-3">
          {isAllReady ? (
            <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0" />
          )}
          <div>
            <h3 className="text-sm font-bold">
              {isAllReady ? 'All Subsystems Operational & Ready' : 'Subsystem Degradation or Notice'}
            </h3>
            <p className="text-xs opacity-90 mt-0.5">
              {isAllReady
                ? 'Vector database, manifest, storage, and generation providers are ready for live inquiries.'
                : 'One or more components are running in fallback or standby mode.'}
            </p>
          </div>
        </div>

        <div className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-slate-900/60 border border-slate-700">
          HTTP {readyData?.ready ? '200 OK' : '503 Notice'}
        </div>
      </div>

      {/* 5-Subsystems Diagnostic Checklist */}
      <Card>
        <CardHeader
          title="Readiness Checklist (5 Critical Subsystems)"
          subtitle="Monitored via GET /api/v1/ready probe"
          icon={<Server className="w-5 h-5 text-indigo-400" />}
        />
        <div className="divide-y divide-slate-800 mt-2">
          {subsystems.map((sub, idx) => (
            <div key={idx} className="py-3.5 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                {sub.ready ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <h4 className="text-xs font-bold text-slate-100">{sub.name}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">{sub.desc}</p>
                  <p className="text-[11px] text-slate-500 font-mono mt-1">Status: {sub.detail}</p>
                </div>
              </div>

              <span
                className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                  sub.ready
                    ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30'
                    : 'bg-rose-950/60 text-rose-300 border-rose-500/30'
                }`}
              >
                {sub.ready ? 'READY' : 'UNREADY'}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* LLM Generation Provider Runtime Settings */}
      <Card>
        <CardHeader
          title="LLM Generation Runtime Configuration"
          subtitle="Configure active inference mode and inspect Colab connectivity"
          icon={<Cpu className="w-5 h-5 text-cyan-400" />}
        />
        <div className="space-y-4 pt-2 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div
              onClick={() => setLlmProvider('auto')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                llmProvider === 'auto'
                  ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <span className="font-bold block text-sm mb-1">Auto Mode (Recommended)</span>
              <p className="text-[11px] leading-relaxed">
                Attempts remote Colab GPU inference; seamlessly falls back to local grounded synthesis if Colab times out. Zero 502 errors.
              </p>
            </div>

            <div
              onClick={() => setLlmProvider('local')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                llmProvider === 'local'
                  ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <span className="font-bold block text-sm mb-1">Local Grounded Mode</span>
              <p className="text-[11px] leading-relaxed">
                Synthesizes answers 100% locally from retrieved excerpts with 100% verified citations. Requires zero GPU.
              </p>
            </div>

            <div
              onClick={() => setLlmProvider('colab_remote')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                llmProvider === 'colab_remote'
                  ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <span className="font-bold block text-sm mb-1">Strict Colab GPU Only</span>
              <p className="text-[11px] leading-relaxed">
                Strictly routes generation to Google Colab Mistral-7B instance. Fails if the ephemeral tunnel is offline.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
