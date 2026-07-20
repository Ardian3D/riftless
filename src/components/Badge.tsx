/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { HTMLAttributes, ReactNode } from 'react';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'success';
  children?: ReactNode;
  className?: string;
  id?: string;
}

export function Badge({
  children,
  variant = 'primary',
  className = '',
  id,
  ...props
}: BadgeProps) {
  const baseStyles = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors';
  
  const variants = {
    primary: 'bg-slate-950 text-slate-50 border-transparent',
    secondary: 'bg-slate-100 text-slate-800 border-transparent hover:bg-slate-200',
    outline: 'border-slate-200 text-slate-600 bg-transparent hover:bg-slate-50',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  };

  return (
    <span
      id={id}
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
