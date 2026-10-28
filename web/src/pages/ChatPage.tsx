import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Send, Trash2, Sparkles, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import { ModeSelector } from '../components/chat/ModeSelector';
import { ChatMessage } from '../components/chat/ChatMessage';
import { Button } from '../components/common/Button';
import { apiClient, ApiClientError } from '../api/client';

export const ChatPage: React.FC = () => {
  const location = useLocation();
  const {
    chatHistory,
    addTurn,
    clearHistory,
    retrievalMode,
    topK,
    llmProvider,
    categoryFocus,
  } = useChat();

  const [inputQuery, setInputQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const samplePrompts = [
    "What is the warranty coverage for ProX-400 and how to fix error E-101?",
    "How do I clear a paper jam in feed tray B on the ApexPrint ColorWave 850?",
    "Is print head damage covered under standard warranty or SLA tier 2?",
    "What maintenance procedures are required for ColorWave 850 monthly?",
  ];

  // Auto-fill from navigation state if present
  useEffect(() => {
    if (location.state && (location.state as any).initialQuery) {
      setInputQuery((location.state as any).initialQuery);
      // clear location state
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, loading]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || loading) return;

    setLoading(true);
    setErrorMessage('');

    try {
      // Apply category focus prefix if explicitly selected
      const finalQuery =
        categoryFocus && categoryFocus !== 'all'
          ? `[${categoryFocus}] ${query}`
          : query;

      const response = await apiClient.queryRAG({
        query: finalQuery,
        retrieval_mode: retrievalMode,
        top_k: topK,
        session_id: `react_session_${Date.now()}`,
        llm_provider: llmProvider,
      });

      addTurn(query, response);
      setInputQuery('');
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to connect to backend service. Ensure FastAPI is running on port 8000.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16">
      {/* Configuration Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            AI Customer Support Assistant
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Grounded reasoning against the ApexPrint enterprise knowledge base.
          </p>
        </div>

        {chatHistory.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearHistory}
            icon={<Trash2 className="w-3.5 h-3.5 text-rose-400" />}
          >
            Clear History
          </Button>
        )}
      </div>

      {/* RAG Mode & Generation Configuration Bar */}
      <ModeSelector />

      {/* Conversation Thread */}
      <div className="min-h-[380px] space-y-4">
        {chatHistory.length === 0 ? (
          <div className="p-12 text-center rounded-3xl border border-dashed border-slate-700/80 bg-slate-900/30 space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20">
              <Layers className="w-7 h-7" />
            </div>
            <div className="max-w-md mx-auto space-y-1">
              <h3 className="text-base font-bold text-slate-200">How can I assist you today?</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ask about hardware error codes, connectivity troubleshooting, standard limited warranty coverage,
                or SLA exclusions. All answers cite verified source passages.
              </p>
            </div>

            {/* Quick Sample Queries */}
            <div className="pt-4 max-w-2xl mx-auto">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Suggested Prompts
              </span>
              <div className="flex flex-wrap justify-center gap-2">
                {samplePrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setInputQuery(prompt);
                      textareaRef.current?.focus();
                    }}
                    className="text-xs text-slate-300 bg-slate-800/80 hover:bg-slate-800 hover:text-white px-3.5 py-1.5 rounded-full border border-slate-700 transition-colors text-left"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          chatHistory.map((turn) => (
            <ChatMessage
              key={turn.id}
              turnId={turn.id}
              query={turn.query}
              response={turn.response}
            />
          ))
        )}

        {/* Loading Spinner Indicator */}
        {loading && (
          <div className="flex items-start gap-3 my-6 animate-pulse">
            <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-300 flex-shrink-0">
              <RefreshCw className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-4 rounded-2xl rounded-tl-sm bg-[#151D32] border border-slate-700/70 text-xs text-slate-300 flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span>
                Retrieving knowledge chunks, merging multi-context evidence, and verifying citations...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Callout */}
      {errorMessage && (
        <div className="p-3.5 rounded-2xl bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <strong className="block font-semibold">Inference Error</strong>
            <span>{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Floating Query Composer */}
      <div className="sticky bottom-4 z-20">
        <form
          onSubmit={handleSubmit}
          className="p-2 rounded-2xl bg-[#151D32]/95 border border-slate-700/80 shadow-2xl backdrop-blur-xl flex items-end gap-2"
        >
          <textarea
            ref={textareaRef}
            rows={2}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type customer support inquiry here... (Enter to submit, Shift+Enter for newline)"
            disabled={loading}
            className="flex-1 text-xs sm:text-sm bg-transparent border-0 p-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-0 resize-none max-h-32 leading-relaxed"
          />

          <Button
            type="submit"
            variant="gradient"
            size="md"
            disabled={!inputQuery.trim() || loading}
            loading={loading}
            icon={<Send className="w-4 h-4" />}
          >
            Send
          </Button>
        </form>
      </div>
    </div>
  );
};
