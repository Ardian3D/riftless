/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
  className?: string;
  id?: string;
}

export function Card({
  children,
  className = '',
  id,
  ...props
}: CardProps) {
  const baseStyles = 'bg-white border border-slate-200 rounded-lg p-5 shadow-sm';

  return (
    <div
      id={id}
      className={`${baseStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

