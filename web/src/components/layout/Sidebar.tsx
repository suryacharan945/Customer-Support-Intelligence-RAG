import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  Files,
  GitCompare,
  BarChart3,
  BookOpen,
  Activity,
  Printer,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Database,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../api/client';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const { data: healthData, isError: isHealthError } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 15000,
  });

  const { data: kbData } = useQuery({
    queryKey: ['kb-status'],
    queryFn: () => apiClient.getKnowledgeBaseStatus(),
    refetchInterval: 30000,
  });

  const navItems = [
    { to: '/', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, exact: true },
    { to: '/chat', label: 'AI Support Chat', icon: <MessageSquare className="w-5 h-5" /> },
    { to: '/documents', label: 'Knowledge Base', icon: <Files className="w-5 h-5" /> },
    { to: '/comparison', label: 'Mode Comparison', icon: <GitCompare className="w-5 h-5" /> },
    { to: '/analytics', label: 'Evaluation & Analytics', icon: <BarChart3 className="w-5 h-5" /> },
    { to: '/how-it-works', label: 'How It Works', icon: <BookOpen className="w-5 h-5" /> },
    { to: '/status', label: 'System Status', icon: <Activity className="w-5 h-5" /> },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 z-40 bg-[#111827]/90 backdrop-blur-xl border-r border-slate-800 transition-all duration-300 flex flex-col ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 flex-shrink-0">
            <Printer className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <span className="font-extrabold text-base tracking-tight text-white block truncate">
                ApexPrint AI
              </span>
              <span className="text-[10px] font-semibold text-cyan-400 block tracking-wider uppercase truncate">
                RAG + MCP Capstone
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors hidden md:flex"
          aria-label={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.exact}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 group relative ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`
            }
          >
            <div className="flex-shrink-0">{item.icon}</div>
            {!collapsed && <span className="truncate">{item.label}</span>}
            {collapsed && (
              <div className="absolute left-full ml-3 px-2.5 py-1 bg-slate-900 text-slate-100 text-xs rounded-md shadow-xl border border-slate-700 whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                {item.label}
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Telemetry Footnote & Status */}
      <div className="p-3 border-t border-slate-800/80 space-y-2">
        {!collapsed ? (
          <>
            {/* Backend status card */}
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-slate-300">FastAPI Backend</span>
                <span className="flex items-center gap-1.5">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      isHealthError ? 'bg-rose-500' : 'bg-emerald-400 animate-pulse'
                    }`}
                  />
                  <span className={isHealthError ? 'text-rose-400' : 'text-emerald-400'}>
                    {isHealthError ? 'Offline' : 'Online'}
                  </span>
                </span>
              </div>
              <div className="text-[11px] text-slate-400 flex items-center justify-between mt-1">
                <span className="flex items-center gap-1">
                  <Database className="w-3 h-3 text-indigo-400" />
                  {kbData?.total_active_chunks ?? 32} Chunks
                </span>
                <span className="text-slate-500">
                  Drive: {healthData?.storage?.google_drive_connected ? 'Sync' : 'Standby'}
                </span>
              </div>
            </div>

            {/* Streamlit Fallback link */}
            <a
              href="http://localhost:8501"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-indigo-300 bg-slate-800/40 hover:bg-slate-800/80 border border-slate-750 transition-colors"
            >
              <span>Streamlit App (Port 8501)</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </>
        ) : (
          <div className="flex justify-center py-1">
            <span
              className={`w-3 h-3 rounded-full ${
                isHealthError ? 'bg-rose-500' : 'bg-emerald-400 animate-pulse'
              }`}
              title={isHealthError ? 'Backend Offline' : 'Backend Online'}
            />
          </div>
        )}
      </div>
    </aside>
  );
};
