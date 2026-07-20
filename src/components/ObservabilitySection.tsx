import React, { ReactNode } from 'react';

interface CalloutProps {
  type: 'note' | 'warning' | 'target';
  title?: string;
  children: ReactNode;
}

function Callout({ type, title, children }: CalloutProps) {
  const styles = {
    note: {
      border: 'border-l-4 border-stone-400',
      bg: 'bg-stone-50',
      text: 'text-stone-800',
      label: 'NOTE',
      labelColor: 'text-stone-600',
      icon: (
        <svg className="w-4 h-4 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    warning: {
      border: 'border-l-4 border-[#F2A93B]',
      bg: 'bg-amber-50/20',
      text: 'text-amber-900',
      label: 'WARNING',
      labelColor: 'text-[#F2A93B]',
      icon: (
        <svg className="w-4 h-4 text-[#F2A93B]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      )
    },
    target: {
      border: 'border-l-4 border-[#A8CD16]',
      bg: 'bg-lime-50/20',
      text: 'text-stone-800',
      label: 'TARGET CONTRACT',
      labelColor: 'text-[#A8CD16]',
      icon: (
        <svg className="w-4 h-4 text-[#A8CD16]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  };

  const config = styles[type];

  return (
    <div className={`p-4 ${config.border} ${config.bg} rounded-r my-6 space-y-1`}>
      <div className="flex items-center gap-2">
        {config.icon}
        <span className={`text-[10px] font-mono font-bold tracking-wider ${config.labelColor}`}>
          {title || config.label}
        </span>
      </div>
      <div className={`text-sm ${config.text} leading-relaxed`}>
        {children}
      </div>
    </div>
  );
}

export function ObservabilitySection() {
  return (
    <section id="observability" aria-labelledby="observability-heading" className="space-y-8 animate-none scroll-mt-24">
      {/* Title & Lead */}
      <div className="space-y-4">
        <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
          OPERATIONS
        </span>
        <h2 id="observability-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
          OBSERVABILITY
        </h2>
        
        <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
          RIFTLESS observability provides target visibility into run progression, component outcomes, dependency availability, validation evidence, authorization states, persistence results, and non-success conditions without replacing the underlying artifacts as sources of truth.
        </p>

        <Callout type="target" title="TARGET OBSERVABILITY CONTRACT">
          This section describes the target observability contract. Telemetry providers, event schemas, metric names, alert thresholds, dashboards, trace formats, retention periods, and notification channels remain undefined until repository-backed operational instrumentation is implemented and verified.
        </Callout>
      </div>

      <hr className="border-stone-200/50" />

      {/* CORE OBSERVABILITY PRINCIPLES */}
      <section className="space-y-4" aria-labelledby="core-observability-principles-heading">
        <h3 id="core-observability-principles-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          CORE OBSERVABILITY PRINCIPLES
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              ARTIFACTS REMAIN THE SOURCE OF TRUTH
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Operational displays should reference recorded run artifacts and outcomes rather than replacing them.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              VISIBILITY DOES NOT CREATE AUTHORITY
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A dashboard status, metric, log message, or alert must not authorize a protected operation.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              NON-SUCCESS REMAINS VISIBLE
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Failed, rejected, unavailable, partial, indeterminate, stale, and skipped outcomes should remain distinguishable.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TELEMETRY STATUS REMAINS SEPARATE
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Telemetry collection success or failure is distinct from the run, validation, writeback, or deployment-handoff result being observed.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SCOPE REMAINS IDENTIFIABLE
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Observed status should remain associated with the relevant run, candidate, revision, stage, component, and evaluated scope.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              STALE INFORMATION REMAINS EXPLICIT
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Old or delayed operational information must not appear current merely because it remains visible.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SECRETS REMAIN EXCLUDED
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Logs, events, metrics, traces, alerts, and dashboards must not expose credentials or prohibited values.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              NO SUCCESS BY PRESENTATION
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A green label, successful HTTP response, completed chart, or absence of alerts must not be interpreted as proof that a protected operation succeeded.
            </p>
          </div>
        </div>

        <Callout type="note">
          Observability describes what the system recorded or could observe. It does not independently prove correctness, authorization, or production impact.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* TARGET OBSERVABILITY FLOW */}
      <section className="space-y-4" aria-labelledby="observability-flow-heading">
        <h3 id="observability-flow-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET OBSERVABILITY FLOW
        </h3>
        
        {/* FLOW CONTAINER */}
        <div className="border border-stone-200 rounded p-6 bg-stone-50/50 max-w-5xl space-y-6">
          <div className="font-mono text-[10px] font-bold text-stone-500 uppercase tracking-wider block border-b border-stone-200 pb-2">
            Target Observability Flow
          </div>
          
          {/* Desktop horizontal flow */}
          <div className="hidden lg:flex flex-wrap items-center gap-1 font-mono text-[8px] font-bold text-stone-700 leading-tight">
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              <span className="block text-[6px] text-stone-500">STAGE OUTCOME</span>
              Component or Stage Outcome
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              <span className="block text-[6px] text-stone-500">PROCESSING</span>
              Permitted Signal Extraction
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              <span className="block text-[6px] text-stone-500">PROCESSING</span>
              Redaction & Scope Check
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-2 text-center shadow-sm uppercase text-[#556b03] min-w-[120px]">
              <span className="block text-[6px] text-[#A8CD16]">SIGNAL LIME</span>
              Signal Recording
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              <span className="block text-[6px] text-stone-500">CORRELATION</span>
              Correlation with Run & Artifacts
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-amber-300 bg-amber-50/10 rounded p-2 text-center shadow-sm uppercase text-amber-900 min-w-[120px]">
              <span className="block text-[6px] text-[#F2A93B]">WARN CHECK</span>
              Operational View or Review Condition
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-stone-100 rounded p-2 text-center shadow-sm uppercase text-stone-500 min-w-[120px]">
              <span className="block text-[6px] text-stone-400">RETENTION</span>
              Retention or Expiration Handling
            </div>
          </div>

          {/* Mobile Flow Sequence */}
          <div className="lg:hidden space-y-2 font-mono text-[10px] font-bold">
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              <span className="block text-[8px] text-stone-500 font-sans">STAGE OUTCOME</span>
              Component or Stage Outcome
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              <span className="block text-[8px] text-stone-500 font-sans">PROCESSING</span>
              Permitted Signal Extraction
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              <span className="block text-[8px] text-stone-500 font-sans">PROCESSING</span>
              Redaction & Scope Check
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-2 text-center uppercase text-[#556b03]">
              <span className="block text-[8px] text-[#A8CD16] font-sans">SIGNAL LIME</span>
              Signal Recording
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              <span className="block text-[8px] text-stone-500 font-sans">CORRELATION</span>
              Correlation with Run & Artifact References
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-amber-300 bg-amber-50/10 rounded p-2 text-center uppercase text-amber-900">
              <span className="block text-[8px] text-[#F2A93B] font-sans">WARN CHECK</span>
              Operational View or Review Condition
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-stone-100 rounded p-2 text-center uppercase text-stone-500">
              <span className="block text-[8px] text-stone-400 font-sans">RETENTION</span>
              Retention or Expiration Handling
            </div>
          </div>

          {/* SUPPORTING REFERENCES */}
          <div className="space-y-2 pt-4 border-t border-stone-200">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              Supporting References
            </span>
            <ul className="list-disc pl-5 text-stone-600 space-y-1 text-xs font-mono">
              <li>RUN REFERENCE</li>
              <li>STAGE REFERENCE</li>
              <li>COMPONENT REFERENCE</li>
              <li>CANDIDATE OR REVISION REFERENCE</li>
              <li>EFFECTIVE CONFIGURATION REFERENCE</li>
              <li>RELATED ARTIFACT REFERENCES</li>
              <li>FAILURE OR LIMITATION REFERENCE</li>
            </ul>
          </div>

          {/* BLOCKED PATHS */}
          <div className="space-y-3 pt-4 border-t border-stone-200">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              Blocked Paths (Observability Transitions Rejected)
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-[10px] font-bold">
              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>TELEMETRY SIGNAL</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>OPERATION AUTHORIZATION</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>MISSING TELEMETRY</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>RUN SUCCESS</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>STALE SIGNAL</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>CURRENT STATUS</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>UNFILTERED LOG</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>PUBLIC OR MODEL CONTEXT</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>ALERT DELIVERY</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>ISSUE RESOLUTION</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>
            </div>
          </div>
        </div>
        <Callout type="note" title="SIGNAL LIME CLARIFICATION">
          Signal Lime identifies that an operational signal was recorded. It does not indicate that the observed run, validation, writeback, handoff, or external operation succeeded.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* OBSERVABILITY SIGNAL CATEGORIES */}
      <section className="space-y-4" aria-labelledby="signal-categories-heading">
        <h3 id="signal-categories-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          SIGNAL CATEGORIES
        </h3>
        
        <div className="space-y-6 max-w-5xl text-xs">
          {/* CATEGORY A */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase">
              A. RUN AND STAGE EVENTS
            </span>
            <div className="space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May describe:</span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>run received</li>
                <li>lifecycle stage entered</li>
                <li>stage completed</li>
                <li>stage closed early</li>
                <li>stage failed or remained unavailable</li>
                <li>protected transition permitted or rejected</li>
                <li>current or superseded state reference</li>
              </ul>
            </div>
          </div>

          {/* CATEGORY B */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              B. COMPONENT OUTCOMES
            </span>
            <div className="space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May describe:</span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>integration request status</li>
                <li>deterministic evaluation result availability</li>
                <li>validator result availability</li>
                <li>writeback operation outcome</li>
                <li>artifact-storage outcome</li>
                <li>handoff-preparation outcome</li>
                <li>security-control outcome</li>
              </ul>
            </div>
          </div>

          {/* CATEGORY C */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              C. DEPENDENCY AVAILABILITY
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May describe:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>configured integration available</li>
                  <li>unavailable</li>
                  <li>degraded</li>
                  <li>response delayed</li>
                  <li>status unknown</li>
                </ul>
              </div>
              <div className="border-t md:border-t-0 md:border-l border-stone-200 pt-2 md:pt-0 md:pl-4">
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">Clarification:</span>
                <p className="text-stone-600 leading-relaxed text-[11px] italic mt-1">
                  Dependency availability does not authorize an operation or prove that a specific request succeeded.
                </p>
              </div>
            </div>
          </div>

          {/* CATEGORY D */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              D. VALIDATION OBSERVABILITY
            </span>
            <div className="space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May describe:</span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>selected validator categories</li>
                <li>individual validator outcomes</li>
                <li>tested scope</li>
                <li>skipped or unavailable validators</li>
                <li>Validation Bundle recording outcome</li>
                <li>storage limitations</li>
              </ul>
            </div>
          </div>

          {/* CATEGORY E */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              E. AUTHORIZATION OBSERVABILITY
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May describe:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>authorization required</li>
                  <li>authorization available</li>
                  <li>authorization rejected</li>
                  <li>authorization unavailable</li>
                  <li>authorization stale for current scope</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must not expose:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>credentials</li>
                  <li>authorization tokens</li>
                  <li>internal authorization secrets</li>
                </ul>
              </div>
            </div>
          </div>

          {/* CATEGORY F */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              F. ARTIFACT AND STORAGE OBSERVABILITY
            </span>
            <div className="space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May describe:</span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>artifact preparation status</li>
                <li>artifact validation status</li>
                <li>preservation success or failure</li>
                <li>unsupported contract version</li>
                <li>predecessor-reference inconsistency</li>
              </ul>
            </div>
          </div>

          {/* CATEGORY G */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              G. SECURITY-CONTROL OUTCOMES
            </span>
            <div className="space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May describe:</span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>content permitted</li>
                <li>content redacted</li>
                <li>content rejected</li>
                <li>control unavailable</li>
                <li>review required</li>
              </ul>
            </div>
          </div>

          {/* CATEGORY H */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              H. EXTERNAL-BOUNDARY REFERENCES
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May describe:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>GitHub reporting outcome</li>
                  <li>DataHub writeback outcome</li>
                  <li>release-handoff preparation outcome</li>
                  <li>external deployment outcome only after a verified integration provides it</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must not:</span>
                <p className="text-stone-600 leading-relaxed text-[11px] italic mt-1">
                  Must not infer external results from internal preparation.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* SIGNAL CATEGORY TABLE */}
      <section className="space-y-4" aria-labelledby="signal-category-table-heading">
        <h3 id="signal-category-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          SIGNAL CATEGORIES MATRIX
        </h3>
        
        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-5xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="signal-categories-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual RIFTLESS observability signal categories and their authority limitations.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[20%]">Signal Category</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Primary Purpose</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[30%]">Example Recorded Condition</th>
                <th scope="col" className="px-4 py-3 w-[25%]">Must Not Imply</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RUN AND STAGE EVENTS</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Describe target lifecycle progression.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Stage entered, completed, failed, or closed.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Displayed state replaces the underlying artifact.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">COMPONENT OUTCOMES</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Expose target component operation results.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Request accepted, rejected, unavailable, or failed.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Component success authorizes a later stage.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DEPENDENCY AVAILABILITY</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Describe whether a configured dependency may be reachable.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Available, degraded, unavailable, or unknown.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">A protected operation is authorized or completed.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION SIGNALS</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Expose selected validators, individual results, and tested scope.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required validator failed or remained unavailable.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">A partial result is complete validation.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">AUTHORIZATION SIGNALS</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Expose recorded authorization requirement and status references.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required, recorded, rejected, unavailable, or stale.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Authentication or UI state is authorization.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACT AND STORAGE SIGNALS</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Describe artifact preparation, validation, and persistence outcomes.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Artifact recorded, invalid, or storage unavailable.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Storage success proves stage correctness.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">SECURITY-CONTROL SIGNALS</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Expose content-boundary or authorization-control results.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Permitted, redacted, rejected, or unavailable.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Security documentation proves runtime protection.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">EXTERNAL-BOUNDARY SIGNALS</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Reference permitted integration outcomes.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">GitHub reporting or DataHub writeback result.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Internal preparation proves an external action occurred.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* EVENT RECORD CONTRACT */}
      <section className="space-y-4" aria-labelledby="event-record-heading">
        <h3 id="event-record-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          OBSERVABILITY EVENT RECORD
        </h3>
        
        <div className="space-y-4 max-w-5xl text-xs text-stone-600">
          <div>
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PURPOSE</span>
            <p className="leading-relaxed mt-1">
              Represent a permitted operational event associated with a run, stage, component, artifact, or external boundary.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                TARGET CONTENT MAY INCLUDE
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
                <li>conceptual event category</li>
                <li>run reference</li>
                <li>stage reference</li>
                <li>component reference</li>
                <li>candidate or revision reference</li>
                <li>effective configuration reference</li>
                <li>related artifact references</li>
                <li>operation or outcome reference</li>
                <li>current status</li>
                <li>previous status reference when relevant</li>
                <li>evaluated scope</li>
                <li>tested scope when relevant</li>
                <li>limitations</li>
                <li>failure category</li>
                <li>permitted diagnostic references</li>
                <li>redaction-result reference</li>
                <li>recorded-time reference after implementation defines time behavior</li>
              </ul>
            </div>

            <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-4">
              <div className="space-y-1">
                <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                  AUTHORITY BOUNDARY
                </span>
                <p className="text-stone-600 text-[11px] leading-relaxed">
                  An Observability Event records a permitted operational signal. It does not create authorization, replace the originating artifact, or prove external execution.
                </p>
              </div>

              <div className="space-y-1">
                <span className="font-mono text-[10px] font-bold text-red-800 block uppercase">
                  MUST NOT CONTAIN
                </span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
                  <li>credentials</li>
                  <li>tokens</li>
                  <li>private keys</li>
                  <li>raw authorization headers</li>
                  <li>unrestricted logs</li>
                  <li>unrestricted source content</li>
                  <li>unrestricted Context Pack content</li>
                  <li>secret environment values</li>
                  <li>private model reasoning</li>
                  <li>fabricated success state</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* EVENT RELATIONSHIP TABLE */}
      <section className="space-y-4" aria-labelledby="event-relationship-heading">
        <h3 id="event-relationship-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          EVENT RELATIONSHIP MATRIX
        </h3>
        
        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-5xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="event-relationships-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual relationships between RIFTLESS operational events and source records.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[20%]">Observed Event</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Required Source Reference</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Permitted Interpretation</th>
                <th scope="col" className="px-4 py-3 w-[30%]">Prohibited Interpretation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK DECISION AVAILABLE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Risk Decision reference.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A deterministic decision artifact was recorded.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The change is universally safe.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION COMPLETED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Validation Bundle reference.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured validation execution completed and its outcome was recorded within the tested scope. Completion does not necessarily mean the validation passed.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Deployment is authorized.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITEBACK COMPLETED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Writeback Record reference.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">The permitted metadata operation completed for the recorded scope.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Risk Decision is ALLOW or validation passed.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">HANDOFF ELIGIBLE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Release-handoff eligibility reference.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured handoff requirements were satisfied.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Deployment occurred.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RECOVERY SUCCEEDED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Recovery Result reference.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A recovery operation completed for its recorded scope.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Previous failure was erased.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACT STORAGE FAILED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Artifact or Failure Record reference.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Preservation did not complete.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The originating stage necessarily failed.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">SECURITY CONTROL REJECTED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Security-result or Failure Record reference.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A protected boundary did not permit the content or operation.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The entire review run automatically becomes BLOCK unless configured policy says so.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* RUN AND STAGE VISIBILITY */}
      <section className="space-y-4" aria-labelledby="run-stage-visibility-heading">
        <h3 id="run-stage-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          RUN AND STAGE VISIBILITY
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TARGET OPERATIONAL VIEWS MAY SHOW
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>run reference</li>
              <li>current lifecycle stage</li>
              <li>current candidate or revision</li>
              <li>latest valid Risk Decision reference</li>
              <li>current validation outcome</li>
              <li>writeback outcome when applicable</li>
              <li>handoff eligibility when applicable</li>
              <li>recovery state when applicable</li>
              <li>known limitations</li>
              <li>stale or superseded references</li>
              <li>latest permitted non-success condition</li>
              <li>artifact-storage status</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              VISIBILITY BOUNDARIES
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>current stage must be derived from recorded lifecycle state</li>
              <li>UI state must not invent a backend stage</li>
              <li>absence of a later artifact does not automatically mean failure</li>
              <li>early run closure should remain distinguishable from runtime failure</li>
              <li>a superseded decision or validation result must not appear current</li>
              <li>stale repository revision must not inherit prior successful status</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* CONCEPTUAL SIGNAL AVAILABILITY STATES */}
      <section className="space-y-4" aria-labelledby="signal-availability-heading">
        <h3 id="signal-availability-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          SIGNAL AVAILABILITY STATES
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following states represent the conceptual visibility of recorded telemetry events, distinct from operational status or database enums:
        </p>

        <div className="space-y-4 max-w-5xl text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CURRENT</span>
              <p className="text-stone-600 text-[11px] leading-relaxed">The recorded signal corresponds to the currently identified run scope and source reference.</p>
            </div>
            
            <div className="border border-[#F2A93B]/40 rounded p-4 bg-amber-50/10 space-y-1">
              <span className="font-mono text-[10px] font-bold text-amber-900 block uppercase">DELAYED</span>
              <p className="text-amber-800 text-[11px] leading-relaxed">The expected signal has not yet been observed within an implementation-defined interval.</p>
            </div>

            <div className="border border-[#F2A93B]/40 rounded p-4 bg-amber-50/10 space-y-1">
              <span className="font-mono text-[10px] font-bold text-amber-900 block uppercase">PARTIAL</span>
              <p className="text-amber-800 text-[11px] leading-relaxed">Only part of the expected permitted signal content is available.</p>
            </div>

            <div className="border border-red-200 rounded p-4 bg-red-50/20 space-y-1">
              <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">STALE</span>
              <p className="text-red-800 text-[11px] leading-relaxed">The signal no longer matches the current candidate, revision, policy, evidence, or operation scope.</p>
            </div>

            <div className="border border-red-200 rounded p-4 bg-red-50/20 space-y-1">
              <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">UNAVAILABLE</span>
              <p className="text-red-800 text-[11px] leading-relaxed">The signal could not be collected, recorded, or retrieved.</p>
            </div>

            <div className="border border-red-200 rounded p-4 bg-red-50/20 space-y-1">
              <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">REJECTED</span>
              <p className="text-red-800 text-[11px] leading-relaxed">The signal could not be preserved or exposed because content, scope, authorization, or redaction requirements were not satisfied.</p>
            </div>

            <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">UNKNOWN</span>
              <p className="text-stone-600 text-[11px] leading-relaxed">The available information is insufficient to determine signal availability.</p>
            </div>
          </div>

          <div className="p-4 border border-stone-300 bg-stone-50 rounded max-w-2xl">
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-xs leading-relaxed">
              <li>DELAYED is not FAILED</li>
              <li>PARTIAL is not COMPLETE</li>
              <li>STALE is not CURRENT</li>
              <li>UNAVAILABLE is not SUCCESS</li>
              <li>REJECTED must not expose prohibited content</li>
              <li>UNKNOWN must not silently become CURRENT</li>
              <li>No state should determine run authorization by itself</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* SIGNAL STATE TABLE */}
      <section className="space-y-4" aria-labelledby="signal-state-table-heading">
        <h3 id="signal-state-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          SIGNAL STATE MATRIX
        </h3>
        
        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-5xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="signal-states-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual availability states for RIFTLESS operational signals.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[20%]">Signal State</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[30%]">Meaning</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Display Requirement</th>
                <th scope="col" className="px-4 py-3 w-[25%]">Must Not Imply</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CURRENT</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Signal matches the identified source scope.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Show source and scope references.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The observed operation was authorized universally.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DELAYED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Expected signal has not yet appeared within an implementation-defined interval.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Show delay or pending limitation.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The operation failed.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PARTIAL</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Only part of the expected signal is available.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Show available and missing portions.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Complete observability.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">STALE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Signal does not match current scope.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Show superseded or stale status.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Old status remains current.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">UNAVAILABLE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Signal could not be recorded or retrieved.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Show unavailable reason when permitted.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The run succeeded or failed.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REJECTED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Signal could not cross a configured content or security boundary.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Show rejection category without exposing prohibited content.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The secret or rejected value may be displayed.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">UNKNOWN</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Available information is insufficient.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Show uncertainty explicitly.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">A positive result.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* METRIC CONTRACT */}
      <section className="space-y-4" aria-labelledby="target-metrics-heading">
        <h3 id="target-metrics-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET METRICS
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following conceptual metric categories outline the visibility requirements for aggregate operational reporting:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              RUN VOLUME
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>number of target runs received</li>
              <li>number of runs closed</li>
              <li>number of runs by final recorded outcome</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              STAGE OUTCOME COUNTS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>completed stages</li>
              <li>failed stages</li>
              <li>unavailable stages</li>
              <li>review-required stages</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              DECISION OUTCOME COUNTS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>ALLOW</li>
              <li>WARN</li>
              <li>BLOCK</li>
              <li>incomplete decision evaluation</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              VALIDATION OUTCOME COUNTS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>successful within scope</li>
              <li>non-successful</li>
              <li>partial</li>
              <li>unavailable</li>
              <li>validator-specific conceptual outcomes</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              DEPENDENCY AVAILABILITY
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>configured integration request outcomes</li>
              <li>unavailable or degraded dependencies</li>
              <li>response duration after implementation defines timing behavior</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              PERSISTENCE OUTCOMES
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>artifact storage results</li>
              <li>GitHub reporting results</li>
              <li>DataHub writeback results</li>
              <li>handoff-package storage results</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SECURITY-CONTROL OUTCOMES
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>permitted</li>
              <li>redacted</li>
              <li>rejected</li>
              <li>review required</li>
              <li>control unavailable</li>
            </ul>
          </div>
        </div>

        <div className="p-4 border border-[#F2A93B]/40 bg-amber-50/10 rounded max-w-3xl space-y-2">
          <span className="font-mono text-[10px] font-bold text-amber-900 block uppercase">METRIC CLARIFICATIONS</span>
          <ul className="list-disc pl-4 text-stone-600 space-y-1 text-xs">
            <li>metric names and labels or dimensions are not yet defined</li>
            <li>metric collection does not replace artifacts</li>
            <li>aggregated counts must not expose sensitive content</li>
            <li>absence of a failure metric is not proof of success</li>
            <li>metrics must not become operation authorization inputs</li>
          </ul>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* LOG AND DIAGNOSTIC CONTRACT */}
      <section className="space-y-4" aria-labelledby="logs-diagnostics-heading">
        <h3 id="logs-diagnostics-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          LOGS AND DIAGNOSTICS
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase">
              MAY BE RECORDED WHEN PERMITTED
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>run and stage references</li>
              <li>component category</li>
              <li>operation category</li>
              <li>conceptual status</li>
              <li>failure category</li>
              <li>bounded diagnostic summary</li>
              <li>permitted source references</li>
              <li>tested-scope reference</li>
              <li>limitation</li>
              <li>correlation reference</li>
              <li>redaction-result reference</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">
              MUST BE REMOVED, REJECTED, OR KEPT SERVER-SIDE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>credentials</li>
              <li>tokens</li>
              <li>private keys</li>
              <li>raw authorization headers</li>
              <li>credential-bearing connection strings</li>
              <li>secret environment values</li>
              <li>unrestricted repository content</li>
              <li>unrestricted Context Pack content</li>
              <li>unrestricted production data</li>
              <li>unrestricted validator output</li>
              <li>private model reasoning</li>
              <li>unrelated sensitive metadata</li>
            </ul>
          </div>
        </div>

        <Callout type="warning" title="DIAGNOSTIC VISIBILITY WARNING">
          A diagnostic value is not safe for operational visibility merely because it was emitted by a trusted component.
        </Callout>

        <Callout type="note">
          Runtime tests should verify that prohibited values are removed or rejected before logs or diagnostics are persisted, displayed, supplied to a model, or sent to an external monitoring destination.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* CORRELATION AND TRACEABILITY */}
      <section className="space-y-4" aria-labelledby="correlation-traceability-heading">
        <h3 id="correlation-traceability-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          CORRELATION AND TRACEABILITY
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          Target operational signals should remain correlatable through permitted references such as:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              CORRELATION REFERENCES
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>run reference</li>
              <li>candidate or revision reference</li>
              <li>stage reference</li>
              <li>component reference</li>
              <li>artifact reference</li>
              <li>operation reference</li>
              <li>predecessor and successor references</li>
              <li>authorization-record reference when permitted</li>
              <li>failure-record reference</li>
              <li>external-result reference when verified</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TARGET RULES
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>correlation reference must not contain credentials</li>
              <li>one reference type must not be reused as authorization</li>
              <li>external outcomes must remain associated with their source integration</li>
              <li>superseded records must remain distinguishable</li>
              <li>a trace or correlation view must not rewrite artifact history</li>
              <li>missing correlation reference should remain an explicit limitation</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* HEALTH AND DEPENDENCY VISIBILITY */}
      <section className="space-y-4" aria-labelledby="dependency-health-heading">
        <h3 id="dependency-health-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          DEPENDENCY HEALTH VISIBILITY
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following conceptual conditions outline the visibility of configured external dependencies:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 max-w-5xl text-xs">
          <div className="border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-4 space-y-1">
            <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase">AVAILABLE</span>
            <p className="text-[#556b03] text-[11px] leading-relaxed">The configured dependency is reported as available for the relevant capability. This does not prove that a specific request will be accepted or succeed.</p>
          </div>

          <div className="border border-[#F2A93B]/40 bg-amber-50/10 rounded p-4 space-y-1">
            <span className="font-mono text-[10px] font-bold text-amber-900 block uppercase">DEGRADED</span>
            <p className="text-amber-800 text-[11px] leading-relaxed">The dependency responds incompletely, slowly, or with limited capability after implementation defines those conditions.</p>
          </div>

          <div className="border border-red-200 bg-red-50/20 rounded p-4 space-y-1">
            <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">UNAVAILABLE</span>
            <p className="text-red-800 text-[11px] leading-relaxed">The dependency cannot accept or complete the relevant target operation.</p>
          </div>

          <div className="border border-stone-200 bg-white rounded p-4 space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">UNKNOWN</span>
            <p className="text-stone-600 text-[11px] leading-relaxed">The dependency condition cannot be established.</p>
          </div>

          <div className="border border-stone-200 bg-white rounded p-4 space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">NOT CONFIGURED</span>
            <p className="text-stone-600 text-[11px] leading-relaxed">The dependency is not enabled for the current capability.</p>
          </div>
        </div>

        <div className="p-4 border border-stone-300 bg-stone-50 rounded max-w-2xl text-xs text-stone-600 leading-relaxed space-y-1">
          <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CLARIFICATIONS</span>
          <ul className="list-disc pl-4 space-y-0.5">
            <li>AVAILABLE does not authorize a request or prove that a specific request succeeded</li>
            <li>DEGRADED does not define a universal failure threshold</li>
            <li>UNAVAILABLE does not automatically determine Risk Decision</li>
            <li>UNKNOWN must remain visible</li>
            <li>NOT CONFIGURED is distinct from operational failure</li>
          </ul>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* ALERT AND REVIEW BOUNDARY */}
      <section className="space-y-4" aria-labelledby="alerts-boundary-heading">
        <h3 id="alerts-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          ALERTS AND REVIEW CONDITIONS
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TARGET ALERT OR REVIEW CONDITIONS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>repeated component failure</li>
              <li>required validator failure</li>
              <li>decision persistence unavailable</li>
              <li>writeback rejection</li>
              <li>artifact-storage failure</li>
              <li>stale authorization</li>
              <li>stale validation or handoff evidence</li>
              <li>prohibited secret detected</li>
              <li>redaction-control unavailable</li>
              <li>external dependency unavailable</li>
              <li>recovery attempt failure</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-4">
            <div className="space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                AUTHORITY BOUNDARY
              </span>
              <p className="text-stone-600 text-[11px] leading-relaxed">
                An alert identifies a condition requiring attention. It does not authorize retry, acknowledgment, writeback, deployment, closure, or remediation.
              </p>
            </div>

            <div className="space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                CLARIFICATIONS
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>alert creation does not mean notification delivery succeeded</li>
                <li>notification delivery does not mean a human reviewed it</li>
                <li>human review does not automatically mean approval</li>
                <li>alert resolution does not rewrite previous failure records</li>
                <li>missing alerts do not prove the system is healthy</li>
                <li>thresholds and routing remain undefined</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* OPERATIONAL VIEW CONTRACT */}
      <section className="space-y-4" aria-labelledby="operational-views-heading">
        <h3 id="operational-views-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          OPERATIONAL VIEWS
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase">
              MAY PRESENT
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>run and revision reference</li>
              <li>lifecycle state</li>
              <li>decision status</li>
              <li>validation outcome</li>
              <li>writeback outcome</li>
              <li>handoff eligibility</li>
              <li>recovery status</li>
              <li>dependency availability</li>
              <li>artifact-storage outcome</li>
              <li>security-control outcome</li>
              <li>stale or superseded status</li>
              <li>limitations and permitted diagnostic references</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">
              MUST NOT
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>infer authorization from styling</li>
              <li>hide failed or partial outcomes</li>
              <li>represent stale data as current</li>
              <li>display prohibited secrets</li>
              <li>display private model reasoning</li>
              <li>describe handoff as deployment</li>
              <li>describe persistence as approval</li>
              <li>treat absence of data as success</li>
            </ul>
          </div>
        </div>

        <Callout type="note">
          The final dashboard structure, filters, queries, aggregation behavior, refresh behavior, and visualization library remain undefined.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* RETENTION AND PRIVACY BOUNDARY */}
      <section className="space-y-4" aria-labelledby="data-boundary-heading">
        <h3 id="data-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          OBSERVABILITY DATA BOUNDARY
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TARGET REQUIREMENTS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>collect only permitted operational fields</li>
              <li>associate signals with configured retention-policy references</li>
              <li>exclude credentials and prohibited content</li>
              <li>avoid unrestricted payload capture</li>
              <li>preserve limitations and missing-data conditions</li>
              <li>distinguish operational data from source artifacts</li>
              <li>restrict browser-visible detail to permitted content</li>
              <li>apply configured redaction before external telemetry export</li>
              <li>avoid exposing unrelated personal data</li>
              <li>preserve deletion or expiration status only after implementation defines it</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-4">
            <div className="space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                CLARIFICATIONS
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>retention duration is not yet defined</li>
                <li>external telemetry destination is not selected</li>
                <li>observability data must not become an unrestricted secondary copy of repository, metadata, validation, or model content</li>
                <li>aggregation does not automatically make sensitive content safe</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* NON-EXECUTABLE OPERATION SHAPES */}
      <section className="space-y-4" aria-labelledby="observability-shapes-heading">
        <h3 id="observability-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET OPERATION SHAPES
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following conceptual definitions outline the target interface boundaries for signal recording, view assembly, and alert checking:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-5xl text-xs">
          {/* Block 1 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL SIGNAL RECORDING
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive component or stage outcome
receive permitted run and scope references
apply configured content filtering
associate related artifact references
record status, limitation, or failure category
return target operational-event reference`}
            </pre>
          </div>

          {/* Block 2 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL OPERATIONAL VIEW ASSEMBLY
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive permitted event and artifact references
resolve current and superseded states
identify missing, delayed, or stale signals
exclude prohibited values
assemble target operational view
return target view result`}
            </pre>
          </div>

          {/* Block 3 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL ALERT-CONDITION CHECK
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive current permitted operational signals
receive configured review-condition references
evaluate conceptual alert or review condition
record condition without authorizing action
return target alert-condition result`}
            </pre>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
          Exact telemetry APIs, event payloads, metric names, log formats, trace identifiers, alert routing, dashboard queries, retention behavior, and monitoring-provider integrations will be documented only after repository-backed observability controls are implemented and versioned.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* OBSERVABILITY CONSISTENCY */}
      <section className="space-y-4" aria-labelledby="observability-consistency-heading">
        <h3 id="observability-consistency-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          OBSERVABILITY CONSISTENCY
        </h3>
        
        <div className="space-y-4 max-w-5xl text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                SOURCE CONSISTENCY
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>operational signal references an available source record</li>
                <li>displayed stage corresponds to recorded lifecycle state</li>
                <li>external outcome is not inferred from internal preparation</li>
              </ul>
            </div>

            <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                SCOPE CONSISTENCY
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>candidate and revision remain identifiable</li>
                <li>stale signals remain distinguishable</li>
                <li>changed scope does not reuse current status silently</li>
              </ul>
            </div>

            <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                STATUS CONSISTENCY
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>failed does not appear successful</li>
                <li>partial does not appear complete</li>
                <li>unavailable does not appear healthy</li>
                <li>delayed does not appear failed automatically</li>
                <li>unknown does not appear current</li>
              </ul>
            </div>

            <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                AUTHORITY CONSISTENCY
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>observability signal does not create authorization</li>
                <li>dashboard action does not rewrite deterministic status</li>
                <li>alert does not authorize recovery</li>
                <li>metric threshold does not replace configured policy</li>
              </ul>
            </div>

            <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                SECURITY CONSISTENCY
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>prohibited values remain excluded</li>
                <li>redaction failure does not permit external export</li>
                <li>browser-visible operational data remains bounded</li>
              </ul>
            </div>

            <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                HISTORY CONSISTENCY
              </span>
              <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                <li>superseded and current events remain distinguishable</li>
                <li>later success does not erase earlier failure</li>
                <li>signal retention does not silently rewrite artifact history</li>
              </ul>
            </div>
          </div>

          <Callout type="note" title="CONSISTENCY NOTE">
            These are target consistency requirements. Do not claim an event-schema validator, telemetry reconciler, or dashboard-state validator already exists.
          </Callout>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* OBSERVABILITY FAILURE BEHAVIOR */}
      <section className="space-y-4" aria-labelledby="observability-failure-behavior-heading">
        <h3 id="observability-failure-behavior-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          OBSERVABILITY FAILURE BEHAVIOR
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">SIGNAL RECORDING UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>operational signal must not be reported as successfully recorded</li>
              <li>originating stage outcome remains distinct</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">SOURCE REFERENCE MISSING</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>signal remains uncorrelated or invalid</li>
              <li>UI must not infer source state</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REDACTION OR FILTERING FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>prohibited signal content must not be persisted or exported</li>
              <li>failure reason must not reproduce the secret</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">METRIC COLLECTION UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>absence of the metric must not imply absence of the condition</li>
              <li>run result remains independent</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">LOG STORAGE UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>log must not be reported as preserved</li>
              <li>component outcome and log-storage outcome remain distinct</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">OPERATIONAL VIEW STALE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>stale state must remain visible</li>
              <li>old status must not appear current</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ALERT-CONDITION CHECK UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>no alert result should be fabricated</li>
              <li>protected action must not infer approval or closure</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">NOTIFICATION DELIVERY UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>alert-condition creation and notification delivery remain distinct</li>
              <li>no human-review result may be inferred</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">EXTERNAL TELEMETRY DESTINATION UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>external export must not appear successful</li>
              <li>local source records remain independently authoritative when available</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* OBSERVABILITY INVARIANTS */}
      <section className="space-y-4" aria-labelledby="observability-invariants-heading">
        <h3 id="observability-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          OBSERVABILITY INVARIANTS
        </h3>
        
        <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-4xl space-y-3 font-mono text-xs">
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">ARTIFACTS REMAIN THE SOURCE OF TRUTH.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">OBSERVABILITY REMAINS NON-AUTHORIZING.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">RUN SCOPE REMAINS IDENTIFIABLE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">STALE SIGNALS DO NOT BECOME CURRENT.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">PARTIAL DOES NOT BECOME COMPLETE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">UNAVAILABLE DOES NOT BECOME SUCCESS.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">ALERTS DO NOT AUTHORIZE ACTION.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">NOTIFICATION DELIVERY DOES NOT IMPLY REVIEW.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">METRICS DO NOT REPLACE POLICY.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">LOGS REMAIN FILTERED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN EXCLUDED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">EXTERNAL OUTCOMES REMAIN UNINFERRED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">LATER SUCCESS DOES NOT ERASE PRIOR FAILURE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">SIGNAL RECORDING SUCCESS REMAINS EXPLICIT.</div>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-4xl">
          These statements describe target observability requirements, not proof that event collection, metrics, logs, traces, dashboards, alerting, notification delivery, retention, or telemetry-provider integrations have already been implemented.
        </p>
      </section>
    </section>
  );
}
