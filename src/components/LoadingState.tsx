/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export function LoadingState({ message = 'Loading pipeline context...', className = '' }: LoadingStateProps) {
  return (
    <div
      id="loading-state-container"
      role="status"
      aria-live="polite"
      className={`flex flex-col items-center justify-center p-8 min-h-[160px] text-center ${className}`}
    >
      <Loader2 
        className="w-6 h-6 text-slate-400 motion-safe:animate-spin mb-3" 
        aria-hidden="true" 
      />
      <p className="text-sm font-mono tracking-wider text-slate-300 uppercase select-none">
        {message}
      </p>
      {/* Screen Reader Only Accessible Text */}
      <span className="sr-only">Please wait while we process: {message}</span>
    </div>
  );
}
