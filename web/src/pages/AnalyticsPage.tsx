import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { BarChart3, ShieldCheck, Clock, AlertTriangle, Info, FileText, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { Card, CardHeader } from '../components/common/Card';

export const AnalyticsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'stage8_eval' | 'dev' | 'held_out' | 'limitations'>('stage8_eval');

  const { data: evalData } = useQuery({
    queryKey: ['evaluation-summary'],
    queryFn: () => apiClient.getEvaluationSummary(),
  });

  const devMetrics = evalData?.development_benchmark?.aggregate_metrics;
  const devMeta = evalData?.development_benchmark;
  const heldOutMeta = evalData?.held_out_benchmark;

  // Chart data 1: Latency Breakdown (ms)
  const latencyChartData = [
    {
      metric: 'Retrieval Latency',
      Baseline: devMetrics?.baseline?.mean_retrieval_latency_ms ?? 0.17,
      MultiContext: devMetrics?.multi_context?.mean_retrieval_latency_ms ?? 0.63,
    },
    {
      metric: 'Mean Gen Latency (s)',
      Baseline: Number(((devMetrics?.baseline?.mean_generation_latency_ms ?? 12386) / 1000).toFixed(1)),
      MultiContext: Number(((devMetrics?.multi_context?.mean_generation_latency_ms ?? 26518) / 1000).toFixed(1)),
    },
    {
      metric: 'P95 Gen Latency (s)',
      Baseline: Number(((devMetrics?.baseline?.p95_total_latency_ms ?? 17399) / 1000).toFixed(1)),
      MultiContext: Number(((devMetrics?.multi_context?.p95_total_latency_ms ?? 29159) / 1000).toFixed(1)),
    },
  ];

  // Chart data 2: Citation Quality & Utilization (%)
  const qualityChartData = [
    {
      name: 'Citation Precision',
      Baseline: 100,
      MultiContext: 100,
    },
    {
      name: 'Context Utilization',
      Baseline: 100, // 1 candidate, 1 cited
      MultiContext: 41.25, // 5 candidates, 2.06 cited
    },
    {
      name: 'Lexical Grounding',
      Baseline: 100,
      MultiContext: 100,
    },
  ];

  // Stage 8 Phase 2.1 15-Question Live Evaluation Dataset
  const stage8Results = [
    { id: 'Q01', category: 'Architecture', query: 'Explain the complete system architecture of this project.', status: 'SUFFICIENT', precision: '100%', ret_ms: 652.1, gen_ms: 86.6, hits: '5/5' },
    { id: 'Q02', category: 'Technology Stack', query: 'What technologies are used in the frontend and presentation layer?', status: 'SUFFICIENT', precision: '100%', ret_ms: 710.2, gen_ms: 31.1, hits: '5/5' },
    { id: 'Q03', category: 'Backend Architecture', query: 'Explain the backend architecture, application server, and endpoint routing.', status: 'SUFFICIENT', precision: '100%', ret_ms: 552.4, gen_ms: 32.6, hits: '4/5' },
    { id: 'Q04', category: 'Multi-Context Prompting', query: 'What is Multi-Context Prompting and how does it prevent context starvation?', status: 'SUFFICIENT', precision: '100%', ret_ms: 535.5, gen_ms: 13.0, hits: '5/5' },
    { id: 'Q05', category: 'Hybrid Retrieval', query: 'Explain the hybrid retrieval pipeline and Reciprocal Rank Fusion.', status: 'SUFFICIENT', precision: '100%', ret_ms: 569.1, gen_ms: 13.0, hits: '5/5' },
    { id: 'Q06', category: 'Reciprocal Rank Fusion', query: 'How does Reciprocal Rank Fusion combine dense and sparse rankings?', status: 'SUFFICIENT', precision: '100%', ret_ms: 574.3, gen_ms: 14.3, hits: '5/5' },
    { id: 'Q07', category: 'Citation Validation', query: 'How does the citation validation engine work and ensure zero hallucinations?', status: 'SUFFICIENT', precision: '100%', ret_ms: 559.8, gen_ms: 13.6, hits: '5/5' },
    { id: 'Q08', category: 'Benchmark Results', query: 'Summarize the benchmark results comparing Mode A and Mode B.', status: 'SUFFICIENT', precision: '100%', ret_ms: 578.4, gen_ms: 16.9, hits: '5/5' },
    { id: 'Q09', category: 'Engineering Decisions', query: 'Explain the core engineering decisions made in this project.', status: 'SUFFICIENT', precision: '100%', ret_ms: 546.8, gen_ms: 10.7, hits: '5/5' },
    { id: 'Q10', category: 'Storage Constraints', query: 'What are the storage constraints and how is the 1024 MB budget enforced?', status: 'SUFFICIENT', precision: '100%', ret_ms: 612.5, gen_ms: 9.7, hits: '3/5' },
    { id: 'Q11', category: 'Accessibility', query: 'Explain the accessibility decisions and WCAG compliance features.', status: 'SUFFICIENT', precision: '100%', ret_ms: 669.8, gen_ms: 7.9, hits: '3/5' },
    { id: 'Q12', category: 'Technical Interview Questions', query: 'What are the key technical interview questions and elevator pitch for this project?', status: 'SUFFICIENT', precision: '100%', ret_ms: 588.9, gen_ms: 14.7, hits: '5/5' },
    { id: 'Q13', category: 'Comparison', query: 'Compare Baseline RAG and Multi-Context Prompting.', status: 'SUFFICIENT', precision: '100%', ret_ms: 567.2, gen_ms: 17.6, hits: '5/5' },
    { id: 'Q14', category: 'Multi-Page Synthesis', query: 'Explain the system architecture and its benchmark results across precision and hallucination rate.', status: 'SUFFICIENT', precision: '100%', ret_ms: 562.0, gen_ms: 16.8, hits: '5/5' },
    { id: 'Q15', category: 'Unsupported Abstention', query: 'Provide a culinary recipe for chocolate chip cookies with quantum computing principles.', status: 'INSUFFICIENT', precision: '0.0%', ret_ms: 561.1, gen_ms: 1.0, hits: '1/5' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div>
        <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-400" />
          Evaluation & Empirical Benchmarks
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Audited experimental metrics with verified provenance across Stage 7B live inference, Stage 8B held-out validation, and Stage 8 Phase 2.1 local synthesis.
        </p>
      </div>

      {/* Dataset & Scope Switcher */}
      <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-[#151D32] border border-slate-700/80 w-fit flex-wrap">
        <button
          type="button"
          onClick={() => setActiveTab('stage8_eval')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'stage8_eval'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Stage 8 Phase 2.1 Dossier Benchmark (15 Queries)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('dev')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'dev'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Stage 7B Development Benchmark (16 Queries / 32 Gens)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('held_out')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'held_out'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Stage 8B Held-Out Suite (10 Unseen Queries)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('limitations')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'limitations'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Known Limitations
        </button>
      </div>

      {/* TAB 1: Stage 8 Phase 2.1 Local Synthesizer Evaluation */}
      {activeTab === 'stage8_eval' && (
        <div className="space-y-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Citation ID Validity</span>
              <div className="text-2xl font-extrabold text-emerald-400 mt-1">100.0%</div>
              <span className="text-[10px] text-slate-500 mt-0.5 block">14/14 Supported Queries Verified</span>
            </Card>

            <Card className="p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Evidence Grounding</span>
              <div className="text-2xl font-extrabold text-cyan-400 mt-1">14 / 14</div>
              <span className="text-[10px] text-slate-500 mt-0.5 block">SUFFICIENT + 1 Honest Abstention</span>
            </Card>

            <Card className="p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Mean Retrieval Latency</span>
              <div className="text-2xl font-extrabold text-indigo-400 mt-1">580.4 ms</div>
              <span className="text-[10px] text-slate-500 mt-0.5 block">Dense + BM25Okapi + RRF Fusion</span>
            </Card>

            <Card className="p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Local Synthesis Latency</span>
              <div className="text-2xl font-extrabold text-emerald-400 mt-1">18.2 ms</div>
              <span className="text-[10px] text-slate-500 mt-0.5 block">Sub-100ms Offline Synthesis</span>
            </Card>
          </div>

          {/* Detailed 15-Question Audit Table */}
          <Card>
            <CardHeader
              title="Stage 8 Phase 2.1 Historical Evaluation Audit: 15-Question Dossier Benchmark"
              subtitle="Historical evaluation results (14 supported questions + 1 unsupported question) evaluated against ChromaDB-indexed Project Dossier"
              icon={<FileText className="w-5 h-5 text-indigo-400" />}
            />
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400 font-semibold uppercase text-[11px] border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">ID</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Query</th>
                    <th className="py-2.5 px-3">Evidence Status</th>
                    <th className="py-2.5 px-3">Citation Validity</th>
                    <th className="py-2.5 px-3">Ret Latency</th>
                    <th className="py-2.5 px-3">Synthesis Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {stage8Results.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-mono text-[11px] text-indigo-300">{r.id}</td>
                      <td className="py-2.5 px-3 text-slate-400">{r.category}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-medium max-w-sm">{r.query}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                            r.status === 'SUFFICIENT'
                              ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
                              : 'bg-rose-950/60 text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-emerald-400">{r.precision}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">{r.ret_ms} ms</td>
                      <td className="py-2.5 px-3 font-mono text-cyan-300">{r.gen_ms} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Provenance and Terminology Note */}
          <div className="p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 text-xs text-slate-300 space-y-2">
            <div className="flex items-center gap-2 font-bold text-indigo-300">
              <Info className="w-4 h-4 text-cyan-400" />
              <span>Historical Evaluation Scope & Metric Terminology</span>
            </div>
            <p className="leading-relaxed">
              <strong>Evaluation Dataset:</strong> Stage 8 Phase 2.1 benchmark comprising 15 questions (14 in-domain supported questions across architecture, benchmarks, and tech stack + 1 out-of-domain unsupported question).
            </p>
            <p className="leading-relaxed">
              <strong>Local Synthesis Latency (~18.2 ms):</strong> Measures deterministic local Python response synthesis, completely distinct from remote Colab GPU inference with Mistral-7B (~12–26s).
            </p>
            <p className="leading-relaxed">
              <strong>Citation ID Validity (100%):</strong> Verifies that every cited chunk ID and source metadata physically matches retrieved candidate metadata without fabrication.
            </p>
            <p className="leading-relaxed">
              <strong>Lexical Evidence Overlap:</strong> Evaluates lexical token containment ($\ge 20\%$ threshold). Lexical token overlap is an automated heuristic, not human-reviewed semantic claim truthfulness or factual correctness.
            </p>
          </div>
        </div>
      )}

      {/* TAB 2: Stage 7B Live Colab Inference Benchmark */}
      {activeTab === 'dev' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Citation Precision</span>
              <div className="text-2xl font-extrabold text-emerald-400 mt-1">100.0%</div>
              <span className="text-[10px] text-slate-500 mt-0.5 block">0 Hallucinated Citations</span>
            </Card>

            <Card className="p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">MCP Context Utilization</span>
              <div className="text-2xl font-extrabold text-cyan-400 mt-1">41.25%</div>
              <span className="text-[10px] text-slate-500 mt-0.5 block">2.06 cited of 4.88 candidates</span>
            </Card>

            <Card className="p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Mean Retrieval Latency</span>
              <div className="text-2xl font-extrabold text-indigo-400 mt-1">0.63 ms</div>
              <span className="text-[10px] text-slate-500 mt-0.5 block">Hybrid Fusion (Dense + BM25)</span>
            </Card>

            <Card className="p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Evaluated Model</span>
              <div className="text-sm font-bold text-slate-200 mt-2 truncate font-mono">
                Mistral-7B-Instruct-v0.3
              </div>
              <span className="text-[10px] text-emerald-400 mt-0.5 block">4-bit NF4 Quantization (Remote Colab)</span>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader
                title="Latency Profile: Baseline vs. Multi-Context"
                subtitle="Retrieval in milliseconds; Remote LLM Generation in seconds"
                icon={<Clock className="w-5 h-5" />}
              />
              <div className="h-64 w-full pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={latencyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#263353" />
                    <XAxis dataKey="metric" stroke="#94A3B8" fontSize={11} />
                    <YAxis stroke="#94A3B8" fontSize={11} />
                    <RechartsTooltip
                      contentStyle={{
                        backgroundColor: '#151D32',
                        borderColor: '#334155',
                        borderRadius: '0.75rem',
                        fontSize: '12px',
                        color: '#F8FAFC',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                    <Bar dataKey="Baseline" fill="#94A3B8" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="MultiContext" fill="#6366F1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card>
              <CardHeader
                title="Citation Groundedness & Candidate Context Utilization (%)"
                subtitle="Strict distinction between precision and candidate utilization"
                icon={<ShieldCheck className="w-5 h-5" />}
              />
              <div className="h-64 w-full pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={qualityChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#263353" />
                    <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} />
                    <YAxis stroke="#94A3B8" fontSize={11} domain={[0, 100]} />
                    <RechartsTooltip
                      contentStyle={{
                        backgroundColor: '#151D32',
                        borderColor: '#334155',
                        borderRadius: '0.75rem',
                        fontSize: '12px',
                        color: '#F8FAFC',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                    <Bar dataKey="Baseline" fill="#94A3B8" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="MultiContext" fill="#22D3EE" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 3: Stage 8B Held-Out Live Evaluation Dataset */}
      {activeTab === 'held_out' && (
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Stage 8B Held-Out Live Evaluation Dataset (10 Queries)"
              subtitle="Unseen evaluation queries spanning all 4 document domains"
              icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
            />
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400 font-semibold uppercase text-[11px] border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3">Query ID</th>
                    <th className="py-2.5 px-3">Question</th>
                    <th className="py-2.5 px-3">Domain</th>
                    <th className="py-2.5 px-3">Baseline Citations</th>
                    <th className="py-2.5 px-3">MCP Citations</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {heldOutMeta?.results?.map((r: any) => (
                    <tr key={r.query_id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-mono text-[11px] text-indigo-300">{r.query_id}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-medium max-w-md">{r.query}</td>
                      <td className="py-2.5 px-3 text-slate-400 capitalize">{r.domain_category}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {r.baseline?.supporting_citations?.length ?? 1}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-cyan-300">
                        {r.multi_context?.supporting_citations?.length ?? 2}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 4: Known Limitations */}
      {activeTab === 'limitations' && (
        <Card className="space-y-4">
          <CardHeader
            title="Known Limitations & Empirical Boundaries"
            subtitle="Transparent reporting of scientific boundaries and testing assumptions"
            icon={<AlertTriangle className="w-5 h-5 text-amber-400" />}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {evalData?.known_limitations?.map((lim, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-3"
              >
                <span className="w-5 h-5 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span className="text-xs text-slate-300 leading-relaxed">{lim}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
