import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  User,
  Bot,
  Copy,
  Check,
  ThumbsUp,
  Info,
  Clock,
  Sparkles,
  Layers,
  BarChart2,
  GitCompare,
  HelpCircle,
  Compass,
  Wrench,
  ShieldCheck,
  BookmarkCheck,
  AlertTriangle,
  FileCode,
} from 'lucide-react';
import { QueryResponse } from '../../api/types';
import { ProviderBadge, EvidenceBadge, CategoryBadge } from '../common/Badge';
import { CitationCard } from './CitationCard';
import { FeedbackModal } from './FeedbackModal';

interface ChatMessageProps {
  query: string;
  response: QueryResponse;
  turnId: string;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ query, response, turnId }) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [feedbackOpen, setFeedbackOpen] = useState<boolean>(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(response?.answer || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isLocalSynthesizer =
    response?.provider_status?.toUpperCase().includes('LOCAL_GROUNDED') ||
    response?.provider_status?.toUpperCase().includes('LOCAL_GROUNDED_FALLBACK') ||
    response?.provider_status?.toUpperCase().includes('LOCAL');

  const isInsufficient = response?.evidence_status === 'INSUFFICIENT';

  // Section heading styler
  const renderHeadingBadge = (text: string) => {
    const lower = text.toLowerCase();
    let icon = <Sparkles className="w-3.5 h-3.5 text-indigo-400" />;
    let badgeStyle = 'border-indigo-500/30 bg-indigo-500/10 text-indigo-200';

    if (lower.includes('architecture') || lower.includes('subsystem') || lower.includes('components')) {
      icon = <Layers className="w-3.5 h-3.5 text-cyan-400" />;
      badgeStyle = 'border-cyan-500/30 bg-cyan-500/10 text-cyan-200';
    } else if (lower.includes('technology') || lower.includes('stack')) {
      icon = <FileCode className="w-3.5 h-3.5 text-violet-400" />;
      badgeStyle = 'border-violet-500/30 bg-violet-500/10 text-violet-200';
    } else if (lower.includes('benchmark') || lower.includes('metric') || lower.includes('evaluation')) {
      icon = <BarChart2 className="w-3.5 h-3.5 text-blue-400" />;
      badgeStyle = 'border-blue-500/30 bg-blue-500/10 text-blue-200';
    } else if (lower.includes('compar') || lower.includes('trade-off')) {
      icon = <GitCompare className="w-3.5 h-3.5 text-indigo-400" />;
      badgeStyle = 'border-indigo-500/30 bg-indigo-500/10 text-indigo-200';
    } else if (lower.includes('interview') || lower.includes('question')) {
      icon = <HelpCircle className="w-3.5 h-3.5 text-sky-400" />;
      badgeStyle = 'border-sky-500/30 bg-sky-500/10 text-sky-200';
    } else if (lower.includes('finding') || lower.includes('decision') || lower.includes('detail')) {
      icon = <Compass className="w-3.5 h-3.5 text-amber-400" />;
      badgeStyle = 'border-amber-500/30 bg-amber-500/10 text-amber-200';
    } else if (lower.includes('step-by-step') || lower.includes('resolution') || lower.includes('troubleshooting')) {
      icon = <Wrench className="w-3.5 h-3.5 text-cyan-400" />;
      badgeStyle = 'border-cyan-500/30 bg-cyan-500/10 text-cyan-200';
    } else if (lower.includes('warranty') || lower.includes('policy')) {
      icon = <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />;
      badgeStyle = 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200';
    } else if (lower.includes('citation') || lower.includes('source')) {
      icon = <BookmarkCheck className="w-3.5 h-3.5 text-emerald-400" />;
      badgeStyle = 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200';
    } else if (lower.includes('missing') || lower.includes('limitation') || lower.includes('insufficient')) {
      icon = <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />;
      badgeStyle = 'border-rose-500/30 bg-rose-500/10 text-rose-200';
    }

    return (
      <div className="mt-5 mb-2.5 pt-1.5 first:mt-1">
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border font-semibold text-xs tracking-wide ${badgeStyle}`}>
          {icon}
          <span>{text}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4 my-6">
      {/* 1. User Message Bubble */}
      <div className="flex items-start gap-3 justify-end pl-12">
        <div className="max-w-2xl bg-indigo-600/90 text-white rounded-2xl rounded-tr-sm p-4 shadow-md shadow-indigo-600/10 text-sm leading-relaxed border border-indigo-400/30">
          <p className="font-medium whitespace-pre-wrap">{query}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 flex-shrink-0 mt-1">
          <User className="w-4 h-4" />
        </div>
      </div>

      {/* 2. Assistant Message Bubble */}
      <div className="flex items-start gap-3 pr-8">
        <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-300 flex-shrink-0 mt-1">
          <Bot className="w-4 h-4" />
        </div>

        <div className="flex-1 max-w-4xl bg-[#151D32] border border-slate-700/70 rounded-2xl rounded-tl-sm p-5 shadow-xl text-slate-100 space-y-3">
          {/* Telemetry Header */}
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-700/60 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-bold text-slate-200">
                {response.retrieval_mode === 'multi_context' ? '🔷 Multi-Context RAG' : '⚪ Baseline RAG'}
              </span>
              <ProviderBadge status={response.provider_status} />
              <EvidenceBadge status={response.evidence_status} />
            </div>

            {/* Accurate Provenance-Specific Latency Labels */}
            <div className="flex items-center gap-2 text-slate-400 text-[11px] font-mono">
              <span className="flex items-center gap-1.5" title="Execution latency breakdown">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                <span>Ret: {response.retrieval_latency_ms}ms</span>
                {response.generation_latency_ms !== null && response.generation_latency_ms !== undefined && (
                  <span>
                    + {isLocalSynthesizer ? 'Local Syn' : 'Remote LLM'}: {response.generation_latency_ms}ms
                  </span>
                )}
              </span>
            </div>
          </div>

          {/* Selected Categories / Domain Badges */}
          {response.selected_categories && response.selected_categories.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap text-xs text-slate-400">
              <span className="text-[11px] text-slate-500">Domain Routing:</span>
              {response.selected_categories.map((c) => (
                <CategoryBadge key={c} category={c} />
              ))}
            </div>
          )}

          {/* Local Grounded Engine Indicator */}
          {isLocalSynthesizer && (
            <div className="flex items-center gap-2.5 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
              <div>
                <strong className="inline font-semibold text-emerald-300">Local Grounded Synthesizer: </strong>
                Dynamically synthesized from indexed reference passages (100% offline, zero external LLM API cost).
              </div>
            </div>
          )}

          {/* Insufficient Evidence Honest Abstention Notice */}
          {isInsufficient && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-200 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="font-semibold text-rose-300 block">Honest Abstention:</strong>
                The requested information was not found in the indexed knowledge base. The assistant abstains from fabricating ungrounded answers.
              </div>
            </div>
          )}

          {/* Answer Markdown Body */}
          <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed space-y-3">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h3: ({ children }) => renderHeadingBadge(String(children || '')),
                p: ({ children }) => (
                  <p className="text-slate-200 text-sm leading-relaxed mb-3">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="space-y-2 my-2.5 pl-1 list-none">
                    {children}
                  </ul>
                ),
                li: ({ children }) => (
                  <li className="text-sm text-slate-200 leading-relaxed flex items-start gap-2.5">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2 flex-shrink-0" />
                    <span className="flex-1">{children}</span>
                  </li>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-white">
                    {children}
                  </strong>
                ),
                code: ({ children }) => (
                  <code className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono text-xs border border-slate-700/80">
                    {children}
                  </code>
                ),
                table: ({ children }) => (
                  <div className="my-4 overflow-x-auto rounded-xl border border-slate-700/80 bg-slate-900/60 shadow-md">
                    <table className="w-full text-xs text-left border-collapse">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-[#1A243D] text-slate-200 font-bold border-b border-slate-700">
                    {children}
                  </thead>
                ),
                tbody: ({ children }) => (
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {children}
                  </tbody>
                ),
                th: ({ children }) => (
                  <th className="px-3.5 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-200">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-3.5 py-2.5 text-xs leading-relaxed">
                    {children}
                  </td>
                ),
              }}
            >
              {response.answer}
            </ReactMarkdown>
          </div>

          {/* Citations Inspector with Evidence Drawer */}
          <CitationCard
            supportingCitations={response.supporting_citations || []}
            candidateCitations={response.citations || []}
            queryContext={query}
          />

          {/* Actions & Feedback Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-700/60 text-xs">
            <div className="flex items-center gap-2 text-slate-400 text-[11px]">
              <Info className="w-3.5 h-3.5 text-slate-500" />
              <span>
                {response.contexts_used || response.supporting_citations?.length || 0} reference passages synthesized
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title="Copy Answer to Clipboard"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>

              <button
                type="button"
                onClick={() => setFeedbackOpen(true)}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-slate-800 transition-colors"
                title="Submit Accuracy Feedback"
              >
                <ThumbsUp className="w-3.5 h-3.5 text-indigo-400" />
                <span>Rate & Review</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Feedback Modal */}
      <FeedbackModal
        open={feedbackOpen}
        onOpenChange={setFeedbackOpen}
        queryId={turnId}
        queryText={query}
      />
    </div>
  );
};
