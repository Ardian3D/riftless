/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { AlertTriangle, RotateCcw } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  title: string;
  description: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({ title, description, onRetry, className = '' }: ErrorStateProps) {
  return (
    <div
      id="error-state-container"
      className={`flex flex-col items-center justify-center text-center p-8 border border-[var(--color-riftless-critical)]/20 rounded-lg max-w-md mx-auto bg-[var(--color-riftless-critical)]/5 ${className}`}
    >
      <div className="w-10 h-10 rounded-full border border-[var(--color-riftless-critical)]/30 bg-[var(--color-riftless-critical)]/10 flex items-center justify-center text-[var(--color-riftless-critical)] mb-4">
        <AlertTriangle className="w-5 h-5 animate-pulse" aria-hidden="true" />
      </div>

      <h3 className="text-sm font-display font-semibold text-slate-200 uppercase tracking-wider mb-1">
        {title}
      </h3>
      <p className="text-sm text-slate-300 font-mono leading-relaxed max-w-sm mb-5">
        {description}
      </p>

      {onRetry && (
        <Button
          id="error-state-retry"
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="inline-flex items-center gap-2 text-xs py-1.5 px-4 font-mono uppercase tracking-wider border-[var(--color-riftless-critical)]/30 text-slate-300 hover:text-white hover:border-[var(--color-riftless-critical)]/60 hover:bg-[var(--color-riftless-critical)]/10"
        >
          <RotateCcw className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Retry Action</span>
        </Button>
      )}
    </div>
  );
}
