/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { StatusBadge, StatusType } from '../components/StatusBadge';
import { LoadingState } from '../components/LoadingState';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { RefreshCw, Play, CircleAlert } from 'lucide-react';

export function OverviewPage() {
  // Simulator State to show interactive preview of F0.5 feedback components
  const [activeTab, setActiveTab] = useState<'all' | 'loading' | 'empty' | 'error'>('all');
  const [loadingMsg, setLoadingMsg] = useState('Fetching Schema Lineage from DataHub...');
  const [errorCount, setErrorCount] = useState(0);

  const statuses: StatusType[] = ['neutral', 'allow', 'warn', 'block', 'running', 'validated', 'failed'];

  const handleRetry = () => {
    setActiveTab('loading');
    setLoadingMsg('Re-authenticating and pulling secure context...');
    setTimeout(() => {
      setActiveTab('all');
    }, 1500);
  };

  const handleSimulateLoad = () => {
    setActiveTab('loading');
    setLoadingMsg('Analyzing dbt models with SQLGlot parser...');
    setTimeout(() => {
      setActiveTab('all');
    }, 2000);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-display font-extrabold tracking-tight uppercase text-white">
            Overview
          </h1>
          <p className="text-sm text-slate-300">
            Monitor protected database assets, analyze recent runs, and audit pipeline changes.
          </p>
        </div>
        <div className="flex justify-start sm:justify-end">
          <Badge variant="success" className="bg-[var(--color-riftless-signal)]/15 text-[var(--color-riftless-signal)] border-[var(--color-riftless-signal)]/30 text-xs font-mono whitespace-nowrap">
            ● F0.5 — Status & Feedback
          </Badge>
        </div>
      </div>

      {/* Component Simulator Controller Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800/60 pb-3">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-3 py-1.5 text-xs font-mono rounded transition-all ${
            activeTab === 'all'
              ? 'bg-slate-800 text-white border-b-2 border-[var(--color-riftless-signal)] font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
          }`}
        >
          All Badges & Grid
        </button>
        <button
          onClick={() => setActiveTab('loading')}
          className={`px-3 py-1.5 text-xs font-mono rounded transition-all ${
            activeTab === 'loading'
              ? 'bg-slate-800 text-white border-b-2 border-[var(--color-riftless-signal)] font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
          }`}
        >
          Loading State
        </button>
        <button
          onClick={() => setActiveTab('empty')}
          className={`px-3 py-1.5 text-xs font-mono rounded transition-all ${
            activeTab === 'empty'
              ? 'bg-slate-800 text-white border-b-2 border-[var(--color-riftless-signal)] font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
          }`}
        >
          Empty State
        </button>
        <button
          onClick={() => setActiveTab('error')}
          className={`px-3 py-1.5 text-xs font-mono rounded transition-all ${
            activeTab === 'error'
              ? 'bg-slate-800 text-white border-b-2 border-[var(--color-riftless-signal)] font-bold'
              : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
          }`}
        >
          Error State
        </button>
      </div>

      {/* Primary Simulator Panel */}
      {activeTab === 'all' && (
        <>
          {/* Section: StatusBadge Inventory */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <h2 className="text-xs font-mono text-slate-300 uppercase tracking-widest">
                [Status Badge Inventory]
              </h2>
              <div className="flex-1 h-[1px] bg-slate-800" />
            </div>

            <Card className="p-6 bg-[#182226]/40 border border-slate-800/60 shadow-none rounded-lg space-y-4">
              <p className="text-sm text-slate-300 max-w-xl leading-relaxed">
                RIFTLESS uses explicit geometric markers, icon shapes, and clear textual descriptions alongside color palettes to guarantee visual clarity across various environments.
              </p>
              
              <div className="flex flex-wrap gap-3">
                {statuses.map((status) => (
                  <StatusBadge key={status} status={status} />
                ))}
              </div>

              <div className="pt-2 flex flex-wrap gap-3">
                <StatusBadge status="running">Analyzing dbt Lineage...</StatusBadge>
                <StatusBadge status="validated">DataHub Synced</StatusBadge>
                <StatusBadge status="failed">SQL Parsing Error</StatusBadge>
                <StatusBadge status="block">Critical Schema Change Blocked</StatusBadge>
              </div>
            </Card>
          </div>

          {/* Section: Core Metrics Overview */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <h2 className="text-xs font-mono text-slate-300 uppercase tracking-widest">
                [Metric Distribution & Pipeline Simulation]
              </h2>
              <div className="flex-1 h-[1px] bg-slate-800" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="p-6 bg-[#182226]/60 border border-slate-800/80 shadow-none rounded-lg flex flex-col justify-between h-40">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-300 uppercase tracking-wider font-bold">
                    Total Runs Analyzed
                  </span>
                  <StatusBadge status="neutral">Audit</StatusBadge>
                </div>
                <div className="space-y-1">
                  <span className="text-4xl font-display font-extrabold text-white block">
                    —
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                    COMPONENT PREVIEW
                  </span>
                </div>
              </Card>

              <Card className="p-6 bg-[#182226]/60 border border-slate-800/80 shadow-none rounded-lg flex flex-col justify-between h-40">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-300 uppercase tracking-wider font-bold">
                    Downstream Datasets
                  </span>
                  <StatusBadge status="validated">Secure</StatusBadge>
                </div>
                <div className="space-y-1">
                  <span className="text-4xl font-display font-extrabold text-white block">
                    —
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                    COMPONENT PREVIEW
                  </span>
                </div>
              </Card>

              <Card className="p-6 bg-[#182226]/60 border border-slate-800/80 shadow-none rounded-lg flex flex-col justify-between h-40">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-300 uppercase tracking-wider font-bold">
                    Blocked Deployments
                  </span>
                  <StatusBadge status="block">Halted</StatusBadge>
                </div>
                <div className="space-y-1">
                  <span className="text-4xl font-display font-extrabold text-red-400 block">
                    —
                  </span>
                  <span className="text-[10px] font-mono text-red-400/80 uppercase tracking-wider block">
                    COMPONENT PREVIEW
                  </span>
                </div>
              </Card>
            </div>
          </div>

          {/* Inline Action Sandbox */}
          <Card className="p-6 bg-slate-900/40 border border-slate-800 shadow-none rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-xs font-mono text-slate-200 uppercase tracking-wider font-bold">
                Interactive Components Sandbox
              </h3>
              <p className="text-sm text-slate-300 font-mono">
                Trigger various deterministic visual states to preview the interactive micro-experiences.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 w-full sm:w-auto">
              <button
                onClick={handleSimulateLoad}
                className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-white rounded border border-slate-700 transition-all"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Simulate Loader</span>
              </button>
              <button
                onClick={() => {
                  setActiveTab('empty');
                }}
                className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-white rounded border border-slate-700 transition-all"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Empty Screen</span>
              </button>
              <button
                onClick={() => {
                  setErrorCount((c) => c + 1);
                  setActiveTab('error');
                }}
                className="flex-grow sm:flex-grow-0 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-mono bg-red-950/40 border border-red-900/60 hover:bg-red-900/30 text-red-200 rounded transition-all"
              >
                <CircleAlert className="w-3.5 h-3.5 text-red-400" />
                <span>Trigger Error</span>
              </button>
            </div>
          </Card>
        </>
      )}

      {activeTab === 'loading' && (
        <Card className="p-12 bg-[#182226]/40 border border-slate-800/60 shadow-none rounded-lg">
          <LoadingState message={loadingMsg} />
          <div className="text-center mt-4">
            <button
              onClick={() => setActiveTab('all')}
              className="text-xs font-mono text-[var(--color-riftless-signal)] hover:underline uppercase"
            >
              ← Back to Overview
            </button>
          </div>
        </Card>
      )}

      {activeTab === 'empty' && (
        <Card className="p-12 bg-[#182226]/40 border border-slate-800/60 shadow-none rounded-lg space-y-6">
          <EmptyState
            title="No Schema Migrations Found"
            description="We searched your raw migrations path and dbt models but didn't find any pending transformations. Add a new schema delta or push a manual diff input on the Analyze page to begin."
            action={{
              label: 'Trigger Synthetic Analysis',
              onClick: () => {
                setActiveTab('loading');
                setLoadingMsg('Generating synthetic schema migration diff...');
                setTimeout(() => {
                  setActiveTab('all');
                }, 1500);
              },
            }}
          />
          <div className="text-center">
            <button
              onClick={() => setActiveTab('all')}
              className="text-xs font-mono text-[var(--color-riftless-signal)] hover:underline uppercase"
            >
              ← Back to Overview
            </button>
          </div>
        </Card>
      )}

      {activeTab === 'error' && (
        <Card className="p-12 bg-[#182226]/40 border border-slate-800/60 shadow-none rounded-lg space-y-6">
          <ErrorState
            title="DataHub Connection Timeout"
            description="The metadata retrieval stream to your DataHub instance has timed out (err_code: dh_0x44). The endpoint is currently unresponsive or the configured credentials are stale."
            onRetry={handleRetry}
          />
          <div className="text-center">
            <button
              onClick={() => setActiveTab('all')}
              className="text-xs font-mono text-slate-400 hover:text-white hover:underline uppercase"
            >
              ← Back to Overview
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}
