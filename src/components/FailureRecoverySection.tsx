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

export function FailureRecoverySection() {
  return (
    <section id="failure-recovery" aria-labelledby="failure-recovery-heading" className="space-y-8 animate-none scroll-mt-24">
      {/* Title & Lead */}
      <div className="space-y-4">
        <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
          OPERATIONS
        </span>
        <h2 id="failure-recovery-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
          FAILURE RECOVERY
        </h2>
        
        <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
          RIFTLESS failure recovery preserves non-success outcomes, identifies permitted recovery paths, and requires explicit reevaluation, revalidation, retry authorization, or run closure without erasing previous evidence.
        </p>

        <Callout type="target" title="TARGET RECOVERY CONTRACT">
          This section describes the target failure-recovery contract. Retry scheduling, queues, backoff rules, operation locking, recovery automation, and persistent orchestration remain undefined until repository-backed recovery controls are implemented and verified.
        </Callout>
      </div>

      <hr className="border-stone-200/50" />

      {/* CORE RECOVERY PRINCIPLES */}
      <section className="space-y-4" aria-labelledby="core-principles-heading">
        <h3 id="core-principles-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          CORE RECOVERY PRINCIPLES
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              FAILURE REMAINS RECORDED
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A failed stage or integration result should remain distinguishable from later retries or successful outcomes.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              RECOVERY DOES NOT REWRITE HISTORY
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A later successful attempt must not silently replace or erase an earlier failure.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              RECOVERY REMAINS AUTHORIZED
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A retry, revised evaluation, revalidation, writeback attempt, or new handoff preparation must satisfy its applicable configured requirements.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              INPUT CONSISTENCY REMAINS REQUIRED
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A recovery result applies only to the candidate, revision, configuration, context, and scope that were evaluated.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              NON-SUCCESS DOES NOT BECOME SUCCESS
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Unavailable, rejected, partial, indeterminate, or failed outcomes must remain explicit.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SECRETS REMAIN EXCLUDED
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Failure messages, diagnostics, logs, and recovery records must not expose credentials or prohibited values.
            </p>
          </div>
        </div>

        <Callout type="note">
          A Failure Record explains that an operation did not complete. It does not determine the permitted recovery action by itself.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* TARGET RECOVERY FLOW */}
      <section className="space-y-4" aria-labelledby="recovery-flow-heading">
        <h3 id="recovery-flow-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET RECOVERY FLOW
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The flow preserves the lineage of failure and identifies permitted recovery coordinates without modifying completed run history:
        </p>

        {/* FLOW CONTAINER */}
        <div className="border border-stone-200 rounded p-6 bg-stone-50/50 max-w-5xl space-y-6">
          <div className="font-mono text-[10px] font-bold text-stone-500 uppercase tracking-wider block border-b border-stone-200 pb-2">
            Target Failure Recovery Flow
          </div>
          
          {/* Desktop horizontal flow */}
          <div className="hidden lg:flex items-center gap-1.5 font-mono text-[9px] font-bold text-stone-700">
            <div className="flex-1 border border-red-200 bg-red-50/30 rounded p-2 text-center shadow-sm uppercase text-red-900">
              <span className="block text-[7px] text-red-500">STATUS: FAILED</span>
              Non-Success Outcome
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700">
              <span className="block text-[7px] text-stone-500 font-mono">RECORDED</span>
              Failure Record
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-400 bg-stone-100 rounded p-2 text-center shadow-sm uppercase text-stone-800">
              <span className="block text-[7px] text-stone-500">GRAPH GRAY</span>
              Failure Classification
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-amber-300 bg-amber-50/10 rounded p-2 text-center shadow-sm uppercase text-amber-900">
              <span className="block text-[7px] text-[#F2A93B]">WARNING AMBER</span>
              Recovery Req. Check
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-600">
              <span className="block text-[7px] text-stone-400">PATH REQUIREMENTS CHECKED</span>
              Permitted Recovery Path
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-200 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-500">
              <span className="block text-[7px] text-stone-400">NEW EVAL</span>
              New Attempt or Revised Run
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-2 text-center shadow-sm uppercase text-[#556b03]">
              <span className="block text-[7px] text-[#A8CD16]">SIGNAL LIME</span>
              New Result Record
            </div>
          </div>

          {/* Mobile Flow Sequence */}
          <div className="lg:hidden space-y-2 font-mono text-[10px] font-bold">
            <div className="border border-red-200 bg-red-50/30 rounded p-2 text-center uppercase text-red-900">
              <span className="block text-[8px] text-red-500">STATUS: FAILED</span>
              Non-Success Outcome
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              <span className="block text-[8px] text-stone-500">RECORDED</span>
              Failure Record
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-400 bg-stone-100 rounded p-2 text-center uppercase text-stone-800">
              <span className="block text-[8px] text-stone-500">GRAPH GRAY</span>
              Failure Classification
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-amber-300 bg-amber-50/10 rounded p-2 text-center uppercase text-amber-900">
              <span className="block text-[8px] text-[#F2A93B]">WARNING AMBER</span>
              Recovery Requirement Check
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-600">
              <span className="block text-[8px] text-stone-400">PATH REQUIREMENTS CHECKED</span>
              Permitted Recovery Path
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-200 bg-white rounded p-2 text-center uppercase text-stone-500">
              <span className="block text-[8px] text-stone-400">NEW EVAL</span>
              New Attempt or Revised Run
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-2 text-center uppercase text-[#556b03]">
              <span className="block text-[8px] text-[#A8CD16]">SIGNAL LIME</span>
              New Result Record
            </div>
          </div>

          {/* SUPPORTING REFERENCES */}
          <div className="space-y-2 pt-4 border-t border-stone-200">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              Supporting References
            </span>
            <ul className="list-disc pl-5 text-stone-600 space-y-1 text-xs font-mono">
              <li>FAILED STAGE</li>
              <li>ORIGINAL INPUT REFERENCES</li>
              <li>EFFECTIVE CONFIGURATION REFERENCE</li>
              <li>DECISION OR AUTHORIZATION REFERENCES</li>
              <li>AVAILABLE DIAGNOSTIC REFERENCES</li>
            </ul>
          </div>

          {/* BLOCKED PATHS */}
          <div className="space-y-3 pt-4 border-t border-stone-200">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              Blocked Paths (Non-Success Transitions)
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-[10px] font-bold">
              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>MODEL OUTPUT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>RECOVERY AUTHORIZATION</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>FAILED RESULT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>SILENT SUCCESS</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>STALE INPUT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>CURRENT RECOVERY RESULT</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>PREVIOUS AUTHORIZATION</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>CHANGED OPERATION SCOPE</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* FAILURE CLASSIFICATION */}
      <section className="space-y-4" aria-labelledby="classification-heading">
        <h3 id="classification-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          FAILURE CLASSIFICATION
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target failure-recovery contract groups non-success outcomes into conceptual categories for classification and recovery planning.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl text-xs">
          {/* INPUT FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">INPUT FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>unreadable proposed change</li>
              <li>unsupported input structure</li>
              <li>missing required revision reference</li>
            </ul>
          </div>

          {/* CONFIGURATION FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CONFIGURATION FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>malformed configuration</li>
              <li>conflicting capability requirements</li>
              <li>required secret reference unavailable</li>
            </ul>
          </div>

          {/* CONTEXT FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CONTEXT FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>required DataHub metadata unavailable</li>
              <li>required context reference stale</li>
              <li>redaction or allowlist failure</li>
            </ul>
          </div>

          {/* MODEL ASSISTANCE FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">MODEL ASSISTANCE FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>model unavailable</li>
              <li>request rejected</li>
              <li>response malformed</li>
              <li>response conflicts with policy</li>
            </ul>
            <p className="text-[10px] text-stone-500 leading-relaxed italic pt-1">
              Model failure must not alter an already recorded deterministic Risk Decision.
            </p>
          </div>

          {/* POLICY EVALUATION FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">POLICY EVALUATION FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>required policy unavailable</li>
              <li>required rule result indeterminate</li>
              <li>decision record invalid or unavailable</li>
            </ul>
          </div>

          {/* VALIDATION FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>required validator failed</li>
              <li>validator unavailable</li>
              <li>bounded input unavailable</li>
              <li>Validation Bundle invalid</li>
            </ul>
          </div>

          {/* WRITEBACK FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">WRITEBACK FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>authorization missing</li>
              <li>mapping unavailable</li>
              <li>destination rejected operation</li>
              <li>destination outcome unavailable</li>
              <li>Writeback Record storage unavailable</li>
            </ul>
          </div>

          {/* HANDOFF FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">HANDOFF FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>candidate not eligible</li>
              <li>review requirement incomplete</li>
              <li>handoff package invalid</li>
              <li>external delivery unavailable</li>
            </ul>
          </div>

          {/* ARTIFACT OR STORAGE FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ARTIFACT OR STORAGE FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>artifact could not be preserved</li>
              <li>required predecessor reference missing</li>
              <li>unsupported artifact contract version</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* FAILURE CLASSIFICATION TABLE */}
      <section className="space-y-4" aria-labelledby="classification-table-heading">
        <h3 id="classification-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          FAILURE CLASSIFICATION TABLE
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following table defines conceptual categories, meanings, recovery targets, and boundaries:
        </p>

        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-5xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="failure-recovery-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual RIFTLESS failure categories and their possible recovery requirements.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[20%]">Failure Category</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[30%]">Meaning</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Possible Recovery Requirement</th>
                <th scope="col" className="px-4 py-3 w-[25%]">Authority Constraint</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">INPUT FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required intake data could not be normalized.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Correct or resubmit the proposed input.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">A corrected input requires a new intake result.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONFIGURATION FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Effective configuration could not be established.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Correct configuration or resolve required capability references.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">No protected stage may run with invalid configuration.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTEXT FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required bounded context could not be assembled.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Refresh or provide permitted context and reevaluate.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Missing context must not silently become ALLOW.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">MODEL ASSISTANCE FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Advisory analysis or remediation could not complete.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Human review, a later permitted request, or continuation when model assistance is not required.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The model does not determine recovery authorization.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">POLICY EVALUATION FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A deterministic Risk Decision could not be validly produced or recorded.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Resolve required policy inputs and run a new deterministic evaluation.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">No decision status may be fabricated.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required validation did not complete successfully.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Revise the candidate, repair the environment, or perform authorized revalidation.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Failure must not become successful evidence.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITEBACK FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Metadata operation or result recording did not complete.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Resolve authorization, mappings, destination availability, or permitted content.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Destination availability does not bypass authorization.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">HANDOFF FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Release-handoff eligibility or package preparation failed.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Resolve decision, validation, review, revision, or package requirements.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">RIFTLESS still does not execute deployment.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">STORAGE FAILURE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A required artifact or result record could not be preserved.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record unavailable preservation state and retry only after configured authorization.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Stage execution and storage success remain distinct.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* RECOVERY PATH STATES */}
      <section className="space-y-4" aria-labelledby="path-states-heading">
        <h3 id="path-states-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          RECOVERY PATH STATES
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The evaluation of a Failure Record indicates the current conceptual recovery path. These are conceptual targets, not official runtime enums:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RETRY MAY BE CONSIDERED</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The failed operation may be attempted again after the same required inputs and authorization state remain valid.
            </p>
            <p className="text-[10px] text-stone-500 italic pt-1">
              RETRY MAY BE CONSIDERED does not mean automatic retry.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REVIEW REQUIRED</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A human or policy-defined decision is required before any further protected action.
            </p>
            <p className="text-[10px] text-stone-500 italic pt-1">
              REVIEW REQUIRED does not mean approval.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REVISION REQUIRED</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The candidate, remediation, configuration, or context must change before reevaluation or revalidation.
            </p>
            <p className="text-[10px] text-stone-500 italic pt-1">
              A revised candidate requires new evaluation where applicable.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DEPENDENCY RESTORATION REQUIRED</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A required integration, validator, environment, or destination must become available.
            </p>
            <p className="text-[10px] text-stone-500 italic pt-1">
              Dependency restoration does not automatically authorize execution.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">NEW AUTHORIZATION REQUIRED</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The operation scope, candidate, revision, mapping, or protected action changed materially.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RUN MAY CLOSE</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Configured policy may permit terminal closure without another attempt.
            </p>
          </div>

          <div className="border border-[#A8CD16] rounded p-4 bg-[#A8CD16]/5 md:col-span-2 lg:col-span-1 space-y-1">
            <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase">RECOVERY SUCCEEDED</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A later permitted attempt completed for its recorded scope.
            </p>
            <p className="text-[10px] text-stone-500 italic pt-1">
              RECOVERY SUCCEEDED does not erase the original failure.
            </p>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* FAILURE RECORD CONTRACT */}
      <section className="space-y-4" aria-labelledby="failure-record-heading">
        <h3 id="failure-record-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          FAILURE RECORD
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The primary purpose of a Failure Record is to record why a stage, integration, artifact operation, or external boundary could not complete.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              Target Content May Include
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>failed stage or operation</li>
              <li>failure category</li>
              <li>failure reason</li>
              <li>source references</li>
              <li>predecessor artifact references</li>
              <li>candidate or revision reference</li>
              <li>effective configuration reference</li>
              <li>decision or authorization references when relevant</li>
              <li>available partial-result references</li>
              <li>permitted diagnostic references</li>
              <li>prohibited next stages</li>
              <li>possible recovery categories</li>
              <li>recovery-eligibility status when implementation defines it</li>
              <li>limitations</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50/50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-800 block uppercase">
              MUST NOT CONTAIN (STRICT EXCLUSIONS)
            </span>
            <ul className="list-disc pl-4 text-red-800 space-y-1 text-[11px] font-mono">
              <li>credentials</li>
              <li>access tokens</li>
              <li>private keys</li>
              <li>raw authorization headers</li>
              <li>unrestricted logs</li>
              <li>unrestricted production data</li>
              <li>secret environment values</li>
              <li>fabricated success result</li>
              <li>hidden model reasoning</li>
              <li>unredacted prohibited content</li>
            </ul>
          </div>
        </div>

        <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed text-[11px]">
          <strong>Authority Boundary:</strong> A Failure Record describes a non-success outcome. It does not authorize retry, bypass policy, convert failure into success, or select the recovery action independently.
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* RECOVERY ACTION CONTRACT */}
      <section className="space-y-4" aria-labelledby="recovery-action-heading">
        <h3 id="recovery-action-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          RECOVERY ACTION
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          A target Recovery Action describes one permitted response to a recorded failure:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              RETRY SAME OPERATION
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Applicable only when relevant inputs remain current, operation scope is unchanged, authorization remains valid, and configured policy permits another attempt.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REVISE AND REEVALUATE
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Applicable when candidate changes, remediation changes, context changes materially, policy inputs change, or a previous decision becomes stale.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REFRESH CONTEXT
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Applicable when required metadata was unavailable, context references became stale, or permitted context can be reassembled.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REVALIDATE
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Applicable when required validator failed or was unavailable, candidate or test scope changed, or prior validation became stale.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REAUTHORIZE
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Applicable when protected operation changes, target destination changes, operation content or scope changes materially, or previous authorization is invalid or unavailable.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              HUMAN REVIEW
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Applicable when configured WARN requirements remain unresolved, failure requires owner or operator judgment, or recovery cannot be selected deterministically.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              CLOSE RUN
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Applicable when policy permits terminal closure, candidate will not be revised, required capability remains unavailable, or review is no longer applicable.
            </p>
          </div>
        </div>

        <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed text-[11px]">
          <strong>Lineage Clarification:</strong> A Recovery Action should identify prerequisites. It is not proof that the action was executed.
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* RECOVERY AUTHORITY MODEL */}
      <section className="space-y-4" aria-labelledby="authority-model-heading">
        <h3 id="authority-model-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          AUTHORITY MODEL
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The authority model defines responsibility limits for each participant in the failure-recovery contract:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl text-xs">
          {/* CONTROL PLANE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CONTROL PLANE</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>read Failure Record and predecessor references</li>
              <li>evaluate configured recovery requirements</li>
              <li>determine whether retry, revision, review, or closure may be considered</li>
              <li>require new authorization when scope changes</li>
              <li>record the selected recovery path when implementation exists</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              The control plane must not convert an unavailable, failed, or rejected result into success.
            </p>
          </div>

          {/* DETERMINISTIC RISK ENGINE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DETERMINISTIC RISK ENGINE</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>perform a new evaluation when relevant decision inputs changed</li>
              <li>produce a new Risk Decision</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              A previous decision must not automatically apply to changed input.
            </p>
          </div>

          {/* VALIDATION WORKER */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION WORKER</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>perform authorized revalidation</li>
              <li>produce a new Validation Bundle or non-success result</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              The worker cannot authorize its own retry or downstream transition.
            </p>
          </div>

          {/* INTEGRATION ADAPTERS */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">INTEGRATION ADAPTERS</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>retry permitted integration operations</li>
              <li>report new accepted, rejected, unavailable, or failed outcomes</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Adapters do not create authorization.
            </p>
          </div>

          {/* HUMAN REVIEWER OR OPERATOR */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1 md:col-span-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">HUMAN REVIEWER OR OPERATOR</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>provide configured acknowledgment or operational decision where required</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              A human review result does not rewrite historical artifacts.
            </p>
          </div>

          {/* DEEPSEEK */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1 md:col-span-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DEEPSEEK</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>explain the failure</li>
              <li>suggest remediation</li>
              <li>summarize possible recovery options</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed font-semibold">
              DeepSeek cannot authorize recovery, retry an operation, clear BLOCK, or create executable evidence.
            </p>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* RETRY AND NEW-RUN BOUNDARY */}
      <section className="space-y-4" aria-labelledby="retry-versus-new-run-heading">
        <h3 id="retry-versus-new-run-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          RETRY VERSUS NEW RUN
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target recovery contract distinguishes a retry of the same applicable operation scope from a new run or new evaluation.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              RETRY MAY BE APPROPRIATE WHEN:
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>candidate and evaluated revision are unchanged</li>
              <li>relevant context and policy references remain current</li>
              <li>operation scope is unchanged</li>
              <li>failure was caused by temporary dependency unavailability</li>
              <li>authorization remains applicable</li>
              <li>configured policy permits another attempt</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              A NEW RUN OR NEW EVALUATION SHOULD BE REQUIRED WHEN:
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>candidate content changes</li>
              <li>repository revision changes</li>
              <li>relevant Context Pack changes materially</li>
              <li>effective policy changes</li>
              <li>remediation changes</li>
              <li>validation scope changes materially</li>
              <li>destination mapping changes materially</li>
              <li>previous authorization no longer matches the operation</li>
              <li>a stale result must be replaced</li>
            </ul>
          </div>
        </div>

        <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed text-[11px]">
          <strong>Statement:</strong> A retry repeats a permitted operation against the same applicable scope. A revised candidate or materially changed scope requires new evaluation records rather than silently reusing old results.
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* RECOVERY RESULT CONTRACT */}
      <section className="space-y-4" aria-labelledby="recovery-result-heading">
        <h3 id="recovery-result-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          RECOVERY RESULT
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          A permitted recovery attempt may produce a new Recovery Result describing completion, non-success, partial progress, unresolved review, or closure.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              Target Content May Include
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>original Failure Record reference</li>
              <li>selected Recovery Action reference</li>
              <li>new attempt reference</li>
              <li>evaluated candidate or revision</li>
              <li>current configuration reference</li>
              <li>current authorization reference where required</li>
              <li>new stage result</li>
              <li>new artifact references</li>
              <li>recovery outcome</li>
              <li>remaining limitations</li>
              <li>superseded or current status references</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              Conceptual Recovery Outcomes
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li><strong>COMPLETED FOR RECORDED SCOPE:</strong> The permitted recovery action completed for the recorded scope.</li>
              <li><strong>NON-SUCCESSFUL:</strong> The recovery attempt failed, was rejected, or could not complete.</li>
              <li><strong>PARTIAL:</strong> Only part of the permitted recovery action completed.</li>
              <li><strong>REVIEW STILL REQUIRED:</strong> The recovery attempt did not resolve a required human or policy decision.</li>
              <li><strong>CLOSED:</strong> The run was closed according to configured policy without successful recovery.</li>
            </ul>
          </div>
        </div>

        <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed text-[11px]">
          <strong>Lineage Boundary:</strong> A completed recovery describes the recovery operation. It does not imply deployment success, universal correctness, or erasure of the original failure.
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* NON-EXECUTABLE OPERATION SHAPES */}
      <section className="space-y-4" aria-labelledby="operation-shapes-heading">
        <h3 id="operation-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET OPERATION SHAPES
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following conceptual definitions outline the target operations for failure classification, checking recovery requirements, and executing recovery:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-5xl text-xs">
          {/* Block 1 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL FAILURE CLASSIFICATION
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive non-success stage result
receive predecessor artifact references
receive effective configuration reference
identify failure category
record available diagnostics and limitations
identify prohibited next stages
return target Failure Record`}
            </pre>
          </div>

          {/* Block 2 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL RECOVERY REQUIREMENT CHECK
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive Failure Record
check candidate and revision consistency
check current policy requirements
check dependency availability
check authorization applicability
identify permitted retry, revision, review, or closure paths
return conceptual recovery-path result`}
            </pre>
          </div>

          {/* Block 3 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL RECOVERY ATTEMPT
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive selected permitted recovery action
receive required current authorization
execute or request the permitted stage operation
record new result without rewriting previous failure
associate predecessor and successor references
return target Recovery Result`}
            </pre>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
          Exact retry APIs, scheduling, backoff, queues, operation locks, recovery commands, and orchestration behavior will be documented only after repository-backed recovery controls are implemented and versioned.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* RECOVERY CONSISTENCY REQUIREMENTS */}
      <section className="space-y-4" aria-labelledby="consistency-heading">
        <h3 id="consistency-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          RECOVERY CONSISTENCY
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">HISTORY CONSISTENCY</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>original Failure Record remains referenced</li>
              <li>later success does not overwrite earlier failure</li>
              <li>previous and current attempts remain distinguishable</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">INPUT CONSISTENCY</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>candidate and revision match the recovery scope</li>
              <li>changed input requires new evaluation where applicable</li>
              <li>stale context or evidence does not become current automatically</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHORIZATION CONSISTENCY</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>protected recovery action has recorded authorization</li>
              <li>changed operation scope may require new authorization</li>
              <li>model output does not provide authorization</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RESULT CONSISTENCY</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>failed recovery does not appear completed</li>
              <li>partial does not appear fully successful</li>
              <li>closure does not appear recovered</li>
              <li>dependency restoration does not imply operation success</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-1 md:col-span-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ARTIFACT CONSISTENCY</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>predecessor and successor references remain associated</li>
              <li>secrets are absent from failure and recovery records</li>
              <li>storage success remains distinct from operation success</li>
            </ul>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
          These are target consistency requirements. Do not claim a recovery-state validator already exists.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* RECOVERY FAILURE BEHAVIOR */}
      <section className="space-y-4" aria-labelledby="recovery-failure-behavior-heading">
        <h3 id="recovery-failure-behavior-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          RECOVERY FAILURE BEHAVIOR
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target recovery contract defines non-success behavior when recovery selection, authorization, execution, or record storage cannot complete.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl text-xs">
          {/* FAILURE RECORD INVALID */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">FAILURE RECORD INVALID</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>recovery selection must not begin</li>
              <li>UI must not infer a recovery path</li>
            </ul>
          </div>

          {/* REQUIRED PREDECESSOR REFERENCE MISSING */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REQUIRED PREDECESSOR REFERENCE MISSING</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>recovery scope remains unresolved</li>
              <li>protected retry must not proceed</li>
            </ul>
          </div>

          {/* RECOVERY CONFIGURATION UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RECOVERY CONFIGURATION UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>no automatic recovery path is selected</li>
              <li>unavailable configuration remains visible</li>
            </ul>
          </div>

          {/* AUTHORIZATION UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHORIZATION UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>protected recovery action must not execute</li>
              <li>dependency availability does not bypass authorization</li>
            </ul>
          </div>

          {/* RECOVERY INPUT STALE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RECOVERY INPUT STALE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>prior recovery eligibility must not appear current</li>
              <li>new evaluation may be required</li>
            </ul>
          </div>

          {/* RECOVERY ATTEMPT FAILED */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RECOVERY ATTEMPT FAILED</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>new failure remains recorded separately</li>
              <li>previous failure remains referenced</li>
            </ul>
          </div>

          {/* RECOVERY RESULT PARTIAL */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RECOVERY RESULT PARTIAL</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>completed and unresolved portions remain distinguishable</li>
              <li>full success must not be reported</li>
            </ul>
          </div>

          {/* RECOVERY RECORD STORAGE UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RECOVERY RECORD STORAGE UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>recovery must not be reported as successfully preserved</li>
              <li>operation outcome and record-storage success remain distinct</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* FAILURE RECOVERY INVARIANTS */}
      <section className="space-y-4" aria-labelledby="invariants-heading">
        <h3 id="invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          FAILURE RECOVERY INVARIANTS
        </h3>
        
        <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-4xl space-y-3 font-mono text-xs">
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">FAILURE REMAINS REPRESENTABLE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">FAILURE HISTORY REMAINS TRACEABLE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">NON-SUCCESS DOES NOT BECOME SUCCESS.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS NON-AUTHORIZING.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">RETRY REMAINS DISTINCT FROM REVISION.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">CHANGED INPUT REQUIRES NEW EVALUATION WHERE APPLICABLE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">AUTHORIZATION REMAINS OPERATION-SPECIFIC.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">RECOVERY SUCCESS DOES NOT ERASE PRIOR FAILURE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">PARTIAL REMAINS DISTINCT FROM COMPLETED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">CLOSURE REMAINS DISTINCT FROM RECOVERY.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN EXCLUDED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">OPERATION SUCCESS REMAINS DISTINCT FROM RECORD STORAGE.</div>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
          These statements describe target failure-recovery requirements, not proof that retry scheduling, recovery workers, queues, operation locks, automated rollback, or recovery persistence have already been implemented.
        </p>
      </section>
    </section>
  );
}
