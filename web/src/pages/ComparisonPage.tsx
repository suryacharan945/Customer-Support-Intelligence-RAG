import React, { useState } from 'react';
import { GitCompare, Play, Sparkles, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import { QueryResponse } from '../api/types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { CitationCard } from '../components/chat/CitationCard';
import { ProviderBadge, EvidenceBadge, CategoryBadge } from '../components/common/Badge';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export const ComparisonPage: React.FC = () => {
  const [query, setQuery] = useState<string>(
    'What is the warranty coverage for ProX-400 and how to fix error E-101?'
  );
  const [topK, setTopK] = useState<number>(5);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [baselineRes, setBaselineRes] = useState<QueryResponse | null>(null);
  const [multiRes, setMultiRes] = useState<QueryResponse | null>(null);

  const sampleQueries = [
    'What is the warranty coverage for ProX-400 and how to fix error E-101?',
    'Can I return an opened printer if the printhead is defective?',
    'How do I clear error code E-204 and is it covered under standard warranty?',
    'What maintenance procedures are required for ColorWave 850 monthly?',
  ];

  const handleRunComparison = async (overrideQuery?: string) => {
    const q = (overrideQuery || query).trim();
    if (!q || loading) return;

    setLoading(true);
    setErrorMessage('');

    try {
      // Execute both baseline and multi_context queries concurrently
      const [resBaseline, resMulti] = await Promise.all([
        apiClient.queryRAG({
          query: q,
          retrieval_mode: 'baseline',
          top_k: topK,
          session_id: `comp_base_${Date.now()}`,
          llm_provider: 'auto',
        }),
        apiClient.queryRAG({
          query: q,
          retrieval_mode: 'multi_context',
          top_k: topK,
          session_id: `comp_multi_${Date.now()}`,
          llm_provider: 'auto',
        }),
      ]);

      setBaselineRes(resBaseline);
      setMultiRes(resMulti);
    } catch (err: any) {
      setErrorMessage(err.message || 'Comparison execution failed');
    } finally {
      setLoading(false);
    }
  };

  const bLat = baselineRes?.retrieval_latency_ms ?? 0;
  const mLat = multiRes?.retrieval_latency_ms ?? 0;
  const bCites = baselineRes?.supporting_citations?.length ?? 0;
  const mCites = multiRes?.supporting_citations?.length ?? 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div>
        <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-indigo-400" />
          Baseline vs Multi-Context RAG Comparison
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Execute queries across both Mode A (Baseline Dense) and Mode B (Multi-Context MCP Hybrid) to
          compare retrieval latency, category routing, and citation precision.
        </p>
      </div>

      {/* Query Input Section */}
      <Card className="space-y-4">
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 w-full">
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Customer Support Inquiry
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter cross-domain technical or warranty question..."
              className="w-full text-xs sm:text-sm bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="w-32 flex-shrink-0">
            <label className="block text-xs font-semibold text-slate-300 mb-1">Top-K Chunks</label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full text-xs bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value={3}>3 Chunks</option>
              <option value={5}>5 Chunks</option>
              <option value={8}>8 Chunks</option>
              <option value={10}>10 Chunks</option>
            </select>
          </div>

          <Button
            type="button"
            variant="gradient"
            size="md"
            loading={loading}
            onClick={() => handleRunComparison()}
            icon={<Play className="w-4 h-4 fill-white" />}
            className="flex-shrink-0"
          >
            Run Side-by-Side Analysis
          </Button>
        </div>

        {/* Quick sample inquiry pills */}
        <div className="pt-2 border-t border-slate-800 flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-semibold text-slate-400">Quick Samples:</span>
          {sampleQueries.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setQuery(sq);
                handleRunComparison(sq);
              }}
              className="text-[11px] text-slate-300 bg-slate-800/60 hover:bg-slate-800 hover:text-white px-2.5 py-1 rounded-lg border border-slate-700/60 transition-colors"
            >
              Option {i + 1}
            </button>
          ))}
        </div>
      </Card>

      {errorMessage && (
        <div className="p-3.5 rounded-2xl bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Comparison Results */}
      {(baselineRes || multiRes) && (
        <div className="space-y-6">
          {/* Comparative Metrics Delta Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block font-medium">Baseline Retrieval</span>
              <span className="text-xl font-extrabold text-slate-200">{bLat.toFixed(2)} ms</span>
              <span className="text-[10px] text-slate-500 block">Single-Channel Dense</span>
            </div>

            <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 space-y-1">
              <span className="text-[11px] text-indigo-300 block font-medium">Multi-Context Retrieval</span>
              <span className="text-xl font-extrabold text-cyan-300">{mLat.toFixed(2)} ms</span>
              <span className="text-[10px] text-indigo-400 block">
                {mLat >= bLat ? `+${(mLat - bLat).toFixed(2)} ms` : `${(mLat - bLat).toFixed(2)} ms`} (BM25 + RRF)
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-400 block font-medium">Baseline Verified Citations</span>
              <span className="text-xl font-extrabold text-slate-200">{bCites}</span>
              <span className="text-[10px] text-slate-500 block">Passages Cited</span>
            </div>

            <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 space-y-1">
              <span className="text-[11px] text-indigo-300 block font-medium">MCP Verified Citations</span>
              <span className="text-xl font-extrabold text-cyan-300">{mCites}</span>
              <span className="text-[10px] text-cyan-400 block">
                {mCites - bCites >= 0 ? `+${mCites - bCites}` : `${mCites - bCites}`} Cross-Domain Citations
              </span>
            </div>
          </div>

          {/* Two-Column Side-by-Side Answers */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            {/* Column 1: Mode A Baseline RAG */}
            <div className="p-5 rounded-2xl bg-[#151D32] border border-slate-700/70 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-slate-200">Mode A: Baseline RAG</h3>
                  <span className="text-[11px] text-slate-400">Single-Channel Dense Semantic Search</span>
                </div>
                <div className="flex items-center gap-1.5">
                  {baselineRes && (
                    <>
                      <ProviderBadge status={baselineRes.provider_status} />
                      <EvidenceBadge status={baselineRes.evidence_status} />
                    </>
                  )}
                </div>
              </div>

              {baselineRes ? (
                <>
                  <div className="prose prose-invert prose-xs text-slate-200 leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{baselineRes.answer}</ReactMarkdown>
                  </div>

                  <CitationCard
                    supportingCitations={baselineRes.supporting_citations || []}
                    candidateCitations={baselineRes.citations || []}
                  />
                </>
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs">Awaiting execution...</div>
              )}
            </div>

            {/* Column 2: Mode B Multi-Context RAG */}
            <div className="p-5 rounded-2xl bg-gradient-to-b from-indigo-950/30 to-[#151D32] border border-indigo-500/40 space-y-4 shadow-xl shadow-indigo-500/5">
              <div className="flex items-center justify-between pb-3 border-b border-indigo-500/30">
                <div>
                  <h3 className="text-sm font-bold text-indigo-200 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    Mode B: Multi-Context RAG (MCP)
                  </h3>
                  <span className="text-[11px] text-indigo-300">
                    Category Routing + Hybrid Fusion (Dense + BM25)
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {multiRes && (
                    <>
                      <ProviderBadge status={multiRes.provider_status} />
                      <EvidenceBadge status={multiRes.evidence_status} />
                    </>
                  )}
                </div>
              </div>

              {multiRes && multiRes.selected_categories?.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap text-xs">
                  <span className="text-[11px] text-indigo-400">Routed Categories:</span>
                  {multiRes.selected_categories.map((c) => (
                    <CategoryBadge key={c} category={c} />
                  ))}
                </div>
              )}

              {multiRes ? (
                <>
                  <div className="prose prose-invert prose-xs text-slate-100 leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{multiRes.answer}</ReactMarkdown>
                  </div>

                  <CitationCard
                    supportingCitations={multiRes.supporting_citations || []}
                    candidateCitations={multiRes.citations || []}
                  />
                </>
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs">Awaiting execution...</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
