import React from 'react';
import { DocumentLifecycleStatus, DocumentCategory, EvidenceStatus } from '../../api/types';

interface BadgeProps {
  children?: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple' | 'outline';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', className = '' }) => {
  const variantStyles = {
    default: 'bg-slate-800 text-slate-200 border-slate-700',
    success: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30',
    warning: 'bg-amber-950/60 text-amber-300 border-amber-500/30',
    error: 'bg-rose-950/60 text-rose-300 border-rose-500/30',
    info: 'bg-sky-950/60 text-sky-300 border-sky-500/30',
    purple: 'bg-indigo-950/60 text-indigo-300 border-indigo-500/30',
    outline: 'bg-transparent text-slate-300 border-slate-700',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};

export const LifecycleBadge: React.FC<{ status: DocumentLifecycleStatus; isSearchable: boolean }> = ({
  status,
  isSearchable,
}) => {
  if (status === 'indexed' && isSearchable) {
    return (
      <Badge variant="success">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        Indexed & Searchable
      </Badge>
    );
  }
  if (status === 'pending_index') {
    return (
      <Badge variant="warning">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
        Pending Indexing
      </Badge>
    );
  }
  if (status === 'processed') {
    return (
      <Badge variant="info">
        <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
        Processed (Not Searchable)
      </Badge>
    );
  }
  if (status === 'uploaded') {
    return (
      <Badge variant="default">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
        Uploaded (Pending Processing)
      </Badge>
    );
  }
  if (status === 'indexing_failed') {
    return (
      <Badge variant="error">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
        Indexing Failed
      </Badge>
    );
  }
  if (status === 'deleted') {
    return (
      <Badge variant="outline" className="line-through opacity-70">
        Deleted
      </Badge>
    );
  }
  return <Badge variant="default">{status}</Badge>;
};

export const CategoryBadge: React.FC<{ category: DocumentCategory | string }> = ({ category }) => {
  const cat = category.toLowerCase();
  if (cat === 'troubleshooting') {
    return <Badge variant="warning">🔧 Troubleshooting</Badge>;
  }
  if (cat === 'warranty') {
    return <Badge variant="success">🛡️ Warranty & SLA</Badge>;
  }
  if (cat === 'product_manual') {
    return <Badge variant="info">📖 Product Manual</Badge>;
  }
  if (cat === 'faq') {
    return <Badge variant="purple">❓ FAQ</Badge>;
  }
  return <Badge variant="default">📁 {category}</Badge>;
};

export const EvidenceBadge: React.FC<{ status: EvidenceStatus }> = ({ status }) => {
  if (status === 'SUFFICIENT') {
    return <Badge variant="success">🟢 Sufficient Grounding</Badge>;
  }
  if (status === 'PARTIAL') {
    return <Badge variant="warning">🟡 Partial Evidence</Badge>;
  }
  return <Badge variant="error">🔴 Insufficient Evidence</Badge>;
};

export const ProviderBadge: React.FC<{ status: string }> = ({ status }) => {
  const upper = status.toUpperCase();
  if (upper.includes('LOCAL_GROUNDED_SYNTHESIS') || upper.includes('LOCAL_GROUNDED_ENGINE')) {
    return <Badge variant="success">💻 Local Grounded Engine</Badge>;
  }
  if (upper.includes('LOCAL_GROUNDED_FALLBACK')) {
    return <Badge variant="warning">⚠️ Local Grounded Fallback</Badge>;
  }
  if (upper.includes('ONLINE_COLAB_GPU') || upper.includes('ONLINE')) {
    return <Badge variant="info">⚡ Remote Mistral GPU</Badge>;
  }
  if (upper.includes('READY_FOR_COLAB')) {
    return <Badge variant="purple">⚡ Colab GPU Standby</Badge>;
  }
  if (upper.includes('MOCK')) {
    return <Badge variant="warning">🧪 Test Mock Mode</Badge>;
  }
  return <Badge variant="default">⚪ {status}</Badge>;
};
