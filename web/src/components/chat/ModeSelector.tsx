import React from 'react';
import { Layers, Zap, Sliders, Filter, Cpu } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { LLMProvider } from '../../api/types';

export const ModeSelector: React.FC = () => {
  const {
    retrievalMode,
    setRetrievalMode,
    topK,
    setTopK,
    llmProvider,
    setLlmProvider,
    categoryFocus,
    setCategoryFocus,
  } = useChat();

  return (
    <div className="p-4 rounded-2xl bg-[#151D32]/90 border border-slate-700/60 backdrop-blur-md mb-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Sliders className="w-3.5 h-3.5 text-indigo-400" />
          Retrieval & Inference Parameters
        </span>
        <span className="text-[11px] text-slate-400">
          Mode:{' '}
          <strong className="text-cyan-400">
            {retrievalMode === 'multi_context' ? 'MCP Hybrid (Dense + BM25)' : 'Baseline Dense'}
          </strong>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Retrieval Strategy */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            RAG Strategy
          </label>
          <div className="grid grid-cols-2 gap-1.5 p-1 rounded-xl bg-slate-900/80 border border-slate-800">
            <button
              type="button"
              onClick={() => setRetrievalMode('multi_context')}
              className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-xs font-semibold transition-all ${
                retrievalMode === 'multi_context'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Multi-Context
            </button>
            <button
              type="button"
              onClick={() => setRetrievalMode('baseline')}
              className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-xs font-semibold transition-all ${
                retrievalMode === 'baseline'
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              Baseline
            </button>
          </div>
        </div>

        {/* 2. LLM Generation Mode */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1">
            <Cpu className="w-3 h-3 text-cyan-400" />
            LLM Generation Engine
          </label>
          <select
            value={llmProvider}
            onChange={(e) => setLlmProvider(e.target.value as LLMProvider)}
            className="w-full text-xs font-medium bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="auto">Auto (Colab GPU + Local Fallback)</option>
            <option value="local">Local Grounded (Always Ready / No GPU)</option>
            <option value="colab_remote">Remote Colab GPU Only</option>
          </select>
        </div>

        {/* 3. Category Filter */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1">
            <Filter className="w-3 h-3 text-purple-400" />
            Category Filter Focus
          </label>
          <select
            value={categoryFocus}
            onChange={(e) => setCategoryFocus(e.target.value)}
            className="w-full text-xs font-medium bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Categories (Auto-Detect)</option>
            <option value="troubleshooting">troubleshooting</option>
            <option value="warranty">warranty</option>
            <option value="product_manual">product_manual</option>
            <option value="faq">faq</option>
          </select>
        </div>

        {/* 4. Top-K Slider */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-slate-300">
              Top-K Context Depth
            </label>
            <span className="text-xs font-bold text-indigo-400">{topK} Chunks</span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            step={1}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-full accent-indigo-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
};
