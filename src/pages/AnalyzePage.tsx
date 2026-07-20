/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Card } from '../components/Card';
import { Badge } from '../components/Badge';

export function AnalyzePage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-display font-extrabold tracking-tight uppercase text-white">
            Analyze Changes
          </h1>
          <p className="text-sm text-slate-400">
            Trigger a manual diff parse or execute synthetic scenario mappings.
          </p>
        </div>
        <div className="flex justify-start sm:justify-end">
          <Badge variant="success" className="bg-[var(--color-riftless-signal)]/15 text-[var(--color-riftless-signal)] border-[var(--color-riftless-signal)]/30 text-xs font-mono whitespace-nowrap">
            ● Foundation Placeholder
          </Badge>
        </div>
      </div>

      <Card className="p-6 bg-[#182226] border border-slate-800 shadow-none rounded-lg space-y-4">
        <h3 className="text-sm font-display font-bold uppercase text-white">
          Pasted Diff input
        </h3>
        <textarea
          id="diff-input-placeholder"
          disabled
          rows={6}
          placeholder="diff --git a/models/orders.sql b/models/orders.sql..."
          className="w-full p-4 bg-[#11181B] border border-slate-800 rounded font-mono text-xs text-slate-500 cursor-not-allowed select-none"
        />
        <p className="text-xs text-slate-400">
          Manual input is currently locked. The analysis loop is configured under Foundation parameters.
        </p>
      </Card>
    </div>
  );
}
