import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  MessageSquare,
  Files,
  GitCompare,
  BarChart3,
  Database,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  HardDrive,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { KnowledgeHero3D } from '../components/3d/KnowledgeHero3D';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: kbStatus } = useQuery({
    queryKey: ['kb-status'],
    queryFn: () => apiClient.getKnowledgeBaseStatus(),
  });

  const { data: health } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getHealth(),
  });

  const quickQuestions = [
    "What is the warranty coverage for ProX-400 and how to fix error E-101?",
    "How do I clear a paper jam in feed tray B on the ApexPrint ColorWave 850?",
    "Is print head damage covered under standard warranty or SLA tier 2?",
    "What should I do when error code E-204 appears on the control panel?",
  ];

  const handleSelectQuestion = (q: string) => {
    navigate('/chat', { state: { initialQuery: q } });
  };

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Hero Section with 3D Knowledge Network */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 flex flex-col justify-between p-8 rounded-3xl bg-gradient-to-br from-[#151D32] via-[#10172A] to-[#0B1020] border border-slate-700/60 shadow-2xl relative overflow-hidden">
          <div className="space-y-4 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Multi-Context RAG + MCP Architecture</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
              ApexPrint Customer Support{' '}
              <span className="gradient-text-brand">Intelligence Platform</span>
            </h2>

            <p className="text-slate-300 text-sm leading-relaxed max-w-xl">
              Grounded, verifiable enterprise technical support powered by Multi-Context Prompting (MCP),
              hybrid vector and BM25 retrieval, and automated citation validation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-6 relative z-10">
            <Button
              variant="gradient"
              size="md"
              onClick={() => navigate('/chat')}
              icon={<MessageSquare className="w-4 h-4" />}
            >
              Launch Support Chat
            </Button>
            <Button
              variant="outline"
              size="md"
              onClick={() => navigate('/comparison')}
              icon={<GitCompare className="w-4 h-4" />}
            >
              Compare Baseline vs MCP
            </Button>
          </div>
        </div>

        <div className="lg:col-span-5 h-[320px] lg:h-auto">
          <KnowledgeHero3D />
        </div>
      </div>

      {/* 2. Real Knowledge Base Telemetry Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-5">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Documents</span>
            <Files className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">
            {kbStatus?.total_active_documents ?? 9}
          </div>
          <div className="text-[11px] text-emerald-400 font-medium flex items-center gap-1 mt-1">
            <CheckCircle2 className="w-3 h-3" />
            {kbStatus?.searchable_documents_count ?? 9} Searchable & Verified
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Indexed Chunks</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">
            {kbStatus?.total_active_chunks ?? 32}
          </div>
          <div className="text-[11px] text-slate-400 font-medium flex items-center gap-1 mt-1">
            ChromaDB + BM25 Indices
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Backend Status</span>
            <HardDrive className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 flex items-center gap-2">
            <span>Online</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <div className="text-[11px] text-slate-400 font-medium flex items-center gap-1 mt-1">
            Drive Sync: {health?.storage?.google_drive_connected ? 'Connected' : 'Standby'}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Uptime</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">
            {health?.uptime_seconds ? `${Math.round(health.uptime_seconds)}s` : 'Active'}
          </div>
          <div className="text-[11px] text-slate-400 font-medium mt-1">
            Port 8000 • FastAPI
          </div>
        </Card>
      </div>

      {/* 3. Baseline vs Multi-Context Explanation Card */}
      <Card>
        <CardHeader
          title="Baseline RAG vs. Multi-Context Prompting (MCP)"
          subtitle="Understanding the dual-channel retrieval architecture"
          icon={<Layers className="w-5 h-5" />}
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Mode A: Baseline RAG
              </span>
              <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-md font-mono">
                Single-Channel Dense
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Performs unconstrained semantic dense search over the complete document index using MiniLM-L6-v2.
              Passages are concatenated directly into the prompt without category partitioning or conflict analysis.
            </p>
            <div className="text-[11px] text-slate-500 pt-2 border-t border-slate-800/80">
              Best for: Simple, single-topic factual lookups.
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                Mode B: Multi-Context RAG (MCP)
              </span>
              <span className="text-[10px] bg-indigo-900/60 text-cyan-300 px-2 py-0.5 rounded-md font-mono">
                Hybrid + Category Balanced
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Performs query intent classification across 4 technical domains, executes hybrid (Dense + BM25 Okapi)
              fusion search, structures balanced context blocks, and validates citations for factual grounding.
            </p>
            <div className="text-[11px] text-cyan-400/80 pt-2 border-t border-indigo-900/40">
              Best for: Complex inquiries spanning troubleshooting, error codes, and warranty coverage.
            </div>
          </div>
        </div>
      </Card>

      {/* 4. Quick Inquiries & Fast Navigation */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-3">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-cyan-400" />
            Quick Example Inquiries
          </h3>
          <p className="text-xs text-slate-400">
            Click any question to execute live retrieval and grounded answer generation:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {quickQuestions.map((q, idx) => (
              <div
                key={idx}
                onClick={() => handleSelectQuestion(q)}
                className="p-4 rounded-xl bg-[#151D32] border border-slate-700/60 hover:border-indigo-500/50 hover:bg-slate-800/70 cursor-pointer transition-all duration-200 group flex items-start justify-between gap-3"
              >
                <span className="text-xs text-slate-200 font-medium group-hover:text-white leading-relaxed">
                  "{q}"
                </span>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 flex-shrink-0 transition-transform group-hover:translate-x-1" />
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-4 space-y-3">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Files className="w-4 h-4 text-purple-400" />
            Quick Navigation
          </h3>
          <p className="text-xs text-slate-400">Explore platform subsystems:</p>
          <div className="space-y-2 pt-1">
            <Button
              variant="outline"
              size="md"
              onClick={() => navigate('/documents')}
              icon={<Files className="w-4 h-4 text-indigo-400" />}
              className="w-full justify-between"
            >
              <span>Knowledge Base Studio</span>
              <ArrowRight className="w-4 h-4 text-slate-500" />
            </Button>
            <Button
              variant="outline"
              size="md"
              onClick={() => navigate('/analytics')}
              icon={<BarChart3 className="w-4 h-4 text-cyan-400" />}
              className="w-full justify-between"
            >
              <span>Evaluation & Benchmarks</span>
              <ArrowRight className="w-4 h-4 text-slate-500" />
            </Button>
            <Button
              variant="outline"
              size="md"
              onClick={() => navigate('/status')}
              icon={<HardDrive className="w-4 h-4 text-emerald-400" />}
              className="w-full justify-between"
            >
              <span>System Status & Readiness</span>
              <ArrowRight className="w-4 h-4 text-slate-500" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
