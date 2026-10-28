import React from 'react';

export const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div
      className={`animate-pulse rounded-lg bg-slate-800/70 border border-slate-700/30 ${className}`}
    />
  );
};
