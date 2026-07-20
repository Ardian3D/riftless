/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Card } from '../components/Card';
import { Badge } from '../components/Badge';

export function RunsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-display font-extrabold tracking-tight uppercase text-white">
            Run History
          </h1>
          <p className="text-sm text-slate-400">
            Audit history tracking previous deterministic risk scores and deep-seek fixes.
          </p>
        </div>
        <div className="flex justify-start sm:justify-end">
          <Badge variant="success" className="bg-[var(--color-riftless-signal)]/15 text-[var(--color-riftless-signal)] border-[var(--color-riftless-signal)]/30 text-xs font-mono whitespace-nowrap">
            ● Foundation Placeholder
          </Badge>
        </div>
      </div>

      <Card className="bg-[#182226] border border-slate-800 shadow-none rounded-lg overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-display font-bold uppercase text-white">
            Analyzed Repository Pull Requests
          </h3>
          <span className="text-xs text-slate-500 font-mono">0 results</span>
        </div>
        <div className="p-12 text-center">
          <p className="text-xs text-slate-400 font-mono uppercase tracking-wider">
            No active runs available in persistent storage.
          </p>
        </div>
      </Card>
    </div>
  );
}
