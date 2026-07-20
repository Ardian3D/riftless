/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import {
  Circle,
  Check,
  Triangle,
  Square,
  Activity,
  CheckCheck,
  X,
  LucideIcon
} from 'lucide-react';

export type StatusType =
  | 'neutral'
  | 'allow'
  | 'warn'
  | 'block'
  | 'running'
  | 'validated'
  | 'failed';

interface StatusBadgeProps {
  status: StatusType;
  children?: React.ReactNode;
  className?: string;
  key?: React.Key;
}

interface StatusConfig {
  icon: LucideIcon;
  label: string;
  classes: string;
  iconClasses?: string;
}

export function StatusBadge({ status, children, className = '' }: StatusBadgeProps) {
  // Map statuses to appropriate icons, labels, and classes
  const config: Record<StatusType, StatusConfig> = {
    neutral: {
      icon: Circle,
      label: 'Neutral',
      classes: 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-900/50 dark:text-slate-400 dark:border-slate-800',
      iconClasses: 'scale-75 fill-current', // Makes it look like a solid dot
    },
    allow: {
      icon: Check,
      label: 'Allow',
      classes: 'bg-[var(--color-riftless-success)]/10 text-[var(--color-riftless-success)] border-[var(--color-riftless-success)]/30',
    },
    warn: {
      icon: Triangle,
      label: 'Warning',
      classes: 'bg-[var(--color-riftless-warning)]/10 text-[var(--color-riftless-warning)] border-[var(--color-riftless-warning)]/30',
    },
    block: {
      icon: Square,
      label: 'Block',
      classes: 'bg-[var(--color-riftless-critical)]/10 text-[var(--color-riftless-critical)] border-[var(--color-riftless-critical)]/30',
    },
    running: {
      icon: Activity,
      label: 'Running',
      classes: 'bg-[var(--color-riftless-signal)]/10 text-[var(--color-riftless-signal)] border-[var(--color-riftless-signal)]/30',
      iconClasses: 'motion-safe:animate-pulse',
    },
    validated: {
      icon: CheckCheck,
      label: 'Validated',
      classes: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    },
    failed: {
      icon: X,
      label: 'Failed',
      classes: 'bg-[var(--color-riftless-critical)]/15 text-red-500 border-red-500/30',
    },
  };

  const current = config[status] || config.neutral;
  const IconComponent = current.icon;

  return (
    <span
      id={`status-badge-${status}`}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-medium tracking-wide uppercase border rounded-md select-none transition-all ${current.classes} ${className}`}
      aria-label={`Status: ${current.label}`}
    >
      <IconComponent 
        className={`w-3.5 h-3.5 flex-shrink-0 ${current.iconClasses || ''}`} 
        aria-hidden="true" 
      />
      <span>{children || current.label}</span>
    </span>
  );
}
