import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Copy, Check, ThumbsUp, Info, Clock, AlertTriangle } from 'lucide-react';
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
    navigator.clipboard.writeText(response.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isFallback =
    response.provider_status?.toUpperCase().includes('LOCAL_GROUNDED_FALLBACK');

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

            <div className="flex items-center gap-2 text-slate-400 text-[11px] font-mono">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-500" />
                {response.retrieval_latency_ms}ms (ret)
                {response.generation_latency_ms ? ` + ${response.generation_latency_ms}ms (gen)` : ''}
              </span>
            </div>
          </div>

          {/* Selected Categories */}
          {response.selected_categories && response.selected_categories.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap text-xs text-slate-400">
              <span className="text-[11px] text-slate-500">Categories:</span>
              {response.selected_categories.map((c) => (
                <CategoryBadge key={c} category={c} />
              ))}
            </div>
          )}

          {/* Fallback Warning Notice if Colab was down */}
          {isFallback && (
            <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-950/40 border border-amber-500/30 text-amber-200 text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block font-semibold">Local Grounded Fallback Engaged</strong>
                Remote Colab GPU was offline or unreachable. The response was synthesized instantly via the local knowledge-base engine with 100% verified citations.
              </div>
            </div>
          )}

          {/* Answer Markdown Body */}
          <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed space-y-2">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {response.answer}
            </ReactMarkdown>
          </div>

          {/* Citations Inspector */}
          <CitationCard
            supportingCitations={response.supporting_citations || []}
            candidateCitations={response.citations || []}
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
                title="Copy Answer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>

              <button
                type="button"
                onClick={() => setFeedbackOpen(true)}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-slate-800 transition-colors"
                title="Submit Feedback"
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
