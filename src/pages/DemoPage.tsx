/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { Link } from 'react-router-dom';

export function DemoPage() {
  return (
    <div className="flex-grow flex items-center justify-center p-6 py-12">
      <div className="w-full max-w-md mx-auto">
        <Card className="p-8 text-center flex flex-col items-center gap-6 bg-white border border-slate-200/60 shadow-sm rounded-lg">
          <Badge variant="success" className="bg-[var(--color-riftless-success)]/10 text-emerald-700 border-[var(--color-riftless-success)]/30 text-[11px] font-mono">
            ● Foundation Placeholder
          </Badge>

          <div className="space-y-2">
            <h1 className="text-2xl font-display font-bold tracking-tight text-[var(--color-riftless-ink)] uppercase">
              Interactive Demo
            </h1>
            <p className="text-xs font-mono text-[var(--color-riftless-graph-gray)] tracking-wider uppercase">
              Judge experience simulation coming soon
            </p>
          </div>

          <p className="text-sm text-slate-500 leading-relaxed">
            This space will hold the zero-config demo experience, allowing judges to test schema analysis, view downstream blast radius calculations, and generate deep-seek remediation plans.
          </p>

          <div className="w-full border-t border-slate-100 my-1" />

          <Link
            to="/app/overview"
            className="text-xs font-mono font-bold tracking-wider text-[var(--color-riftless-ink)] hover:underline uppercase"
          >
            Explore Dashboard Console →
          </Link>
        </Card>
      </div>
    </div>
  );
}
