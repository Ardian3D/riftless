/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link } from 'react-router-dom';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Badge } from '../components/Badge';

export function NotFoundPage() {
  return (
    <div className="flex-grow flex items-center justify-center p-6 py-12 bg-[var(--color-riftless-paper)] text-[var(--color-riftless-ink)]">
      <div className="w-full max-w-md mx-auto">
        <Card className="p-8 text-center flex flex-col items-center gap-6 bg-white border border-slate-200/60 shadow-sm rounded-lg">
          <Badge variant="secondary" className="bg-[var(--color-riftless-critical)]/15 text-[var(--color-riftless-critical)] border-[var(--color-riftless-critical)]/30 text-xs font-mono uppercase tracking-wider">
            ● 404 - Not Found
          </Badge>

          <div className="space-y-2">
            <h1 className="text-2xl font-display font-bold tracking-tight uppercase">
              Page Not Found
            </h1>
            <p className="text-xs font-mono text-[var(--color-riftless-graph-gray)] tracking-wider uppercase">
              The requested path does not exist
            </p>
          </div>

          <p className="text-sm text-slate-500 leading-relaxed">
            The route you are trying to access might have been renamed or is postponed until future phases.
          </p>

          <div className="w-full border-t border-slate-100 my-1" />

          <Link to="/">
            <Button variant="primary" size="sm" className="bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] hover:bg-slate-800">
              Return Home
            </Button>
          </Link>
        </Card>
      </div>
    </div>
  );
}
