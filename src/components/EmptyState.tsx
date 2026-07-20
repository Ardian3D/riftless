/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Inbox } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({ title, description, action, className = '' }: EmptyStateProps) {
  return (
    <div
      id="empty-state-container"
      className={`flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-800/80 rounded-lg max-w-md mx-auto bg-slate-900/10 ${className}`}
    >
      <div className="w-10 h-10 rounded-full border border-slate-800/50 bg-[#141C1E] flex items-center justify-center text-slate-500 mb-4">
        <Inbox className="w-5 h-5" aria-hidden="true" />
      </div>

      <h3 className="text-sm font-display font-semibold text-slate-200 uppercase tracking-wider mb-1">
        {title}
      </h3>
      <p className="text-sm text-slate-300 font-mono leading-relaxed max-w-sm mb-5">
        {description}
      </p>

      {action && (
        <Button
          id="empty-state-action"
          variant="outline"
          size="sm"
          onClick={action.onClick}
          className="text-xs py-1.5 px-4 font-mono uppercase tracking-wider border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 hover:bg-slate-800/30"
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}
