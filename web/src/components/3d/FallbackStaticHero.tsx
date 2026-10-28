import React from 'react';
import { Layers, Database, Sparkles, ShieldCheck } from 'lucide-react';

export const FallbackStaticHero: React.FC = () => {
  return (
    <div className="w-full h-full min-h-[300px] flex items-center justify-center p-6 bg-gradient-to-br from-indigo-950/20 via-[#151D32] to-cyan-950/20 rounded-2xl border border-slate-700/50">
      <div className="text-center max-w-md">
        <div className="flex justify-center gap-4 mb-4">
          <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Database className="w-6 h-6" />
          </div>
          <div className="p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Layers className="w-6 h-6" />
          </div>
          <div className="p-3 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>
        <h4 className="text-lg font-bold text-slate-100 mb-1">
          Multi-Context Knowledge Topology
        </h4>
        <p className="text-sm text-slate-400">
          Partitioned evidence merging across manuals, warranties, troubleshooting guides, and FAQs.
        </p>
      </div>
    </div>
  );
};
