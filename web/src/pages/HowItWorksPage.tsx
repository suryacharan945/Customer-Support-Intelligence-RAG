import React from 'react';
import {
  UploadCloud,
  Scissors,
  Binary,
  Search,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { Card } from '../components/common/Card';

export const HowItWorksPage: React.FC = () => {
  const steps = [
    {
      num: 1,
      title: 'Upload Documents',
      desc: 'Technical manuals, error sheets, and warranty policies are ingested as PDF, TXT, or Markdown documents.',
      icon: <UploadCloud className="w-5 h-5 text-indigo-400" />,
      detail: 'Enforces format validation, 10MB size limits, and path traversal defenses.',
    },
    {
      num: 2,
      title: 'Intelligent Chunking',
      desc: 'Documents are partitioned into structured semantic chunks with 10% overlap to preserve surrounding context.',
      icon: <Scissors className="w-5 h-5 text-cyan-400" />,
      detail: 'Chunk IDs retain source document name, page number, and section header metadata.',
    },
    {
      num: 3,
      title: 'Embedding Generation & Indexing',
      desc: 'Every chunk is converted into high-dimensional vector embeddings using sentence-transformers/all-MiniLM-L6-v2.',
      icon: <Binary className="w-5 h-5 text-purple-400" />,
      detail: 'Stored locally in ChromaDB vector space alongside a BM25 sparse keyword index.',
    },
    {
      num: 4,
      title: 'Hybrid Fusion Retrieval',
      desc: 'Queries execute dual-channel search: dense vector similarity + BM25 keyword matching fused via Reciprocal Rank Fusion (RRF).',
      icon: <Search className="w-5 h-5 text-emerald-400" />,
      detail: 'Overcomes vector search limitations on specific alphanumeric printer error codes (e.g. E-101, E-204).',
    },
    {
      num: 5,
      title: 'Multi-Context Merging (MCP)',
      desc: 'The query is analyzed to detect multiple intents (e.g., how to fix a jam + whether repair is under warranty).',
      icon: <Layers className="w-5 h-5 text-amber-400" />,
      detail: 'MCP balances evidence chunks across relevant categories to eliminate single-source bias.',
    },
    {
      num: 6,
      title: 'Mistral-7B Grounded Generation',
      desc: 'Mistral-7B-Instruct-v0.3 synthesizes an accurate answer strictly and solely from the retrieved context blocks.',
      icon: <Sparkles className="w-5 h-5 text-indigo-400" />,
      detail: 'Treated as untrusted data with strict prompt injection defense and zero ungrounded extrapolation.',
    },
    {
      num: 7,
      title: 'Automated Citation Validation',
      desc: 'The response is validated against retrieved passages. Every claim must cite the exact document and chunk ID.',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
      detail: 'Provides users with one-click verification of source snippets and page numbers.',
    },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Header */}
      <div>
        <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
          How ApexPrint Support Intelligence Works
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          A step-by-step educational guide to the retrieval-augmented generation lifecycle.
        </p>
      </div>

      {/* Visual Pipeline Flow */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-950/40 via-[#151D32] to-cyan-950/40 border border-slate-700/70">
        <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          End-to-End RAG Architecture Pipeline
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {steps.map((step, idx) => (
            <div
              key={step.num}
              className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center flex flex-col justify-between space-y-2 relative"
            >
              <div className="w-8 h-8 rounded-full bg-slate-800 text-slate-200 flex items-center justify-center font-bold text-xs mx-auto border border-slate-700">
                {step.num}
              </div>
              <div>
                <span className="text-xs font-bold text-slate-100 block">{step.title}</span>
              </div>
              <div className="flex justify-center text-slate-500 pt-1">
                {step.icon}
              </div>
              {idx < steps.length - 1 && (
                <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-slate-600">
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step-by-Step Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {steps.map((step) => (
          <Card key={step.num} className="p-5 space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700 text-indigo-400">
                {step.icon}
              </div>
              <div>
                <span className="text-[11px] font-bold text-indigo-400 block uppercase tracking-wider">
                  Phase {step.num}
                </span>
                <h4 className="text-sm font-bold text-slate-100">{step.title}</h4>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed pt-1">{step.desc}</p>
            <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 font-mono">
              💡 {step.detail}
            </div>
          </Card>
        ))}
      </div>

      {/* Limitations Disclaimer */}
      <div className="p-5 rounded-2xl bg-amber-950/30 border border-amber-500/40 text-amber-200 text-xs space-y-2">
        <div className="flex items-center gap-2 font-bold text-amber-300">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>Understanding the Boundaries of AI-Generated Support</span>
        </div>
        <p className="leading-relaxed">
          While the ApexPrint platform uses rigorous multi-context verification and strict citation checking,
          answers are generated by a statistical language model. Whenever safety-critical electrical procedures
          or complex warranty claim decisions arise, customers should verify the supporting documentation cards
          or contact an authorized ApexPrint human technician.
        </p>
      </div>
    </div>
  );
};
