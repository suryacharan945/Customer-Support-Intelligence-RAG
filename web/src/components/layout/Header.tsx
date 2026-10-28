import React from 'react';
import { useLocation } from 'react-router-dom';
import { Sun, Moon, Menu, Cpu, ShieldCheck } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useChat } from '../../context/ChatContext';

interface HeaderProps {
  onMobileMenuToggle: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMobileMenuToggle }) => {
  const { theme, toggleTheme } = useTheme();
  const { retrievalMode, llmProvider } = useChat();
  const location = useLocation();

  const getPageTitle = (path: string) => {
    switch (path) {
      case '/':
        return 'System Overview';
      case '/chat':
        return 'AI Customer Support Assistant';
      case '/documents':
        return 'Knowledge Base Studio';
      case '/comparison':
        return 'Baseline vs Multi-Context Comparison';
      case '/analytics':
        return 'Evaluation & Benchmarks';
      case '/how-it-works':
        return 'Architecture & Methodology';
      case '/status':
        return 'System Status & Diagnostics';
      default:
        return 'Support Intelligence';
    }
  };

  return (
    <header className="h-16 px-6 border-b border-slate-800/80 bg-[#0B1020]/80 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button
          onClick={onMobileMenuToggle}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 md:hidden"
          aria-label="Open mobile menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-base font-bold text-slate-100 flex items-center gap-2">
            {getPageTitle(location.pathname)}
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* RAG Mode Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-950/60 border border-indigo-500/30 text-indigo-300">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>
            {retrievalMode === 'multi_context' ? 'Multi-Context (MCP Hybrid)' : 'Baseline (Dense Only)'}
          </span>
        </div>

        {/* Provider Mode Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800/80 border border-slate-700 text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          <span className="capitalize">{llmProvider} Generation</span>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 border border-slate-700/60 transition-colors"
          aria-label={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-400" />}
        </button>
      </div>
    </header>
  );
};
