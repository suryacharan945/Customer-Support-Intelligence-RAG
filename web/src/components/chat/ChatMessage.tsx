import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Copy, Check, ThumbsUp, Info, Clock, Sparkles, Wrench, ShieldCheck, BookmarkCheck } from 'lucide-react';
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

          {/* Local Grounded Engine Indicator */}
          {(isFallback || response.provider_status?.toUpperCase().includes('LOCAL_GROUNDED')) && (
            <div className="flex items-center gap-2.5 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
              <div>
                <strong className="inline font-semibold text-emerald-300">Local Grounded AI Engine: </strong>
                Synthesized directly from verified knowledge-base documentation (100% offline & private).
              </div>
            </div>
          )}

          {/* Answer Markdown Body */}
          <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed space-y-3">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h3: ({ children }) => {
                  const text = String(children || '');
                  let icon = <Sparkles className="w-3.5 h-3.5 text-indigo-400" />;
                  let badgeStyle = 'border-indigo-500/30 bg-indigo-500/10 text-indigo-200';

                  if (text.toLowerCase().includes('step-by-step') || text.toLowerCase().includes('technical')) {
                    icon = <Wrench className="w-3.5 h-3.5 text-cyan-400" />;
                    badgeStyle = 'border-cyan-500/30 bg-cyan-500/10 text-cyan-200';
                  } else if (text.toLowerCase().includes('warranty') || text.toLowerCase().includes('policy')) {
                    icon = <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />;
                    badgeStyle = 'border-amber-500/30 bg-amber-500/10 text-amber-200';
                  } else if (text.toLowerCase().includes('citation') || text.toLowerCase().includes('source')) {
                    icon = <BookmarkCheck className="w-3.5 h-3.5 text-emerald-400" />;
                    badgeStyle = 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200';
                  }

                  return (
                    <div className="mt-5 mb-2.5 pt-1.5 first:mt-1">
                      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border font-semibold text-xs tracking-wide ${badgeStyle}`}>
                        {icon}
                        <span>{children}</span>
                      </div>
                    </div>
                  );
                },
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
              }}
            >
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
