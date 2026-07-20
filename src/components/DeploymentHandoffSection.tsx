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
        <svg className="w-4 h-4 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
        <svg className="w-4 h-4 text-[#F2A93B]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      )
    },
    target: {
      border: 'border-l-4 border-[#A8CD16]',
      bg: 'bg-lime-50/20',
      text: 'text-stone-800',
      label: 'TARGET CAPABILITY',
      labelColor: 'text-[#A8CD16]',
      icon: (
        <svg className="w-4 h-4 text-[#A8CD16]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

export function DeploymentHandoffSection() {
  return (
    <section id="deployment" aria-labelledby="deployment-heading" className="space-y-8 animate-none scroll-mt-24">
      {/* Title & Lead */}
      <div className="space-y-4">
        <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
          REFERENCE
        </span>
        <h2 id="deployment-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
          Deployment Handoff
        </h2>
        
        <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
          RIFTLESS may prepare a governed release handoff after required decision, validation, review, and artifact conditions are recorded. Production deployment remains the responsibility of an external delivery system and its authorized operators.
        </p>

        <Callout type="target">
          This section describes the target deployment-handoff contract. Release integrations, approval systems, CI/CD providers, environment mappings, and deployment commands remain undefined until repository-backed delivery boundaries are implemented and verified.
        </Callout>
      </div>

      <hr className="border-stone-200/50" />

      {/* CORE DEPLOYMENT BOUNDARY */}
      <section className="space-y-4" aria-labelledby="core-boundary-heading">
        <h3 id="core-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Core Deployment Boundary
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The boundary between governed analysis results and execution systems defines the structural limits of RIFTLESS:
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl text-xs">
          {/* RIFTLESS MAY PREPARE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              RIFTLESS MAY PREPARE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>current Risk Decision reference</li>
              <li>scope-bound Validation Bundle reference</li>
              <li>acknowledgment or review reference when required</li>
              <li>effective configuration reference</li>
              <li>evaluated revision reference</li>
              <li>permitted remediation reference</li>
              <li>tested-scope statement</li>
              <li>known limitations</li>
              <li>owner actions</li>
              <li>permitted artifact references</li>
              <li>release-handoff status</li>
            </ul>
          </div>

          {/* RIFTLESS MUST NOT PERFORM */}
          <div className="border border-stone-200 rounded p-4 bg-stone-50/50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-800 block uppercase">
              RIFTLESS MUST NOT PERFORM
            </span>
            <ul className="list-disc pl-4 text-red-800 space-y-1 text-[11px] font-mono">
              <li>direct production mutation</li>
              <li>infrastructure deployment</li>
              <li>database migration execution in production</li>
              <li>automatic merge</li>
              <li>release approval</li>
              <li>environment promotion</li>
              <li>secret distribution</li>
              <li>production rollback</li>
              <li>deployment credential management</li>
            </ul>
          </div>
        </div>

        <p className="text-sm text-stone-600 leading-relaxed max-w-2xl font-mono text-xs">
          RIFTLESS may establish whether a reviewed candidate satisfies the configured requirements for a release handoff. It does not establish whether an external deployment actually occurred or succeeded.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* TARGET DEPLOYMENT HANDOFF FLOW */}
      <section className="space-y-4" aria-labelledby="handoff-flow-heading">
        <h3 id="handoff-flow-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Target Deployment Handoff Flow
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The handoff flow defines how a reviewed candidate is prepared for an external deployment system:
        </p>

        {/* FLOW CONTAINER */}
        <div className="border border-stone-200 rounded p-6 bg-stone-50/50 max-w-4xl space-y-6">
          <div className="font-mono text-[10px] font-bold text-stone-500 uppercase tracking-wider block border-b border-stone-200 pb-2">
            Conceptual Transition Sequence
          </div>
          
          {/* Desktop horizontal flow */}
          <div className="hidden md:flex items-center gap-1.5 font-mono text-[9px] font-bold text-stone-700">
            <div className="flex-1 border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase text-stone-500">
              Change / Revision
            </div>
            <div className="text-stone-400 text-xs px-0.5">&rarr;</div>
            <div className="flex-1 border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase text-stone-500">
              Risk Decision
            </div>
            <div className="text-stone-400 text-xs px-0.5">&rarr;</div>
            <div className="flex-1 border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase text-stone-500">
              Validation &amp; Review
            </div>
            <div className="text-stone-400 text-xs px-0.5">&rarr;</div>
            <div className="flex-1 border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase text-stone-500">
              Configuration
            </div>
            <div className="text-stone-400 text-xs px-0.5">&rarr;</div>
            <div className="flex-1 border border-stone-300 rounded p-2 bg-stone-100 text-center shadow-sm uppercase text-stone-700">
              Handoff Check
            </div>
            <div className="text-stone-400 text-xs px-0.5">&rarr;</div>
            <div className="flex-1 border border-[#A8CD16] rounded p-2 bg-[#A8CD16]/10 text-center shadow-sm uppercase text-[#556b03]">
              Handoff Package
            </div>
            
            {/* BOUNDARY MARKER */}
            <div className="flex flex-col items-center justify-center px-2 py-1 border-l border-r border-dashed border-red-400 bg-red-50/50 rounded max-w-[80px] text-center text-[8px] text-red-800 uppercase leading-none">
              <span>Riftless</span>
              <span className="font-extrabold mt-0.5">Authority</span>
              <span className="font-extrabold text-[7px] text-red-500">Ends Here</span>
            </div>
            
            <div className="text-stone-400 text-xs px-0.5">&rarr;</div>
            <div className="flex-1 border border-stone-400 rounded p-2 bg-white text-center shadow-sm uppercase text-stone-600">
              External Delivery
            </div>
            <div className="text-stone-400 text-xs px-0.5">&rarr;</div>
            <div className="flex-1 border border-stone-800 rounded p-2 bg-stone-900 text-white text-center shadow-sm uppercase">
              External Deploy
            </div>
          </div>

          {/* Mobile Flow Sequence */}
          <div className="md:hidden space-y-2 font-mono text-[10px] font-bold">
            <div className="border border-stone-200 rounded p-2 bg-white text-center uppercase text-stone-500">
              Change / Revision
            </div>
            <div className="text-center text-stone-400 text-xs">&darr;</div>
            <div className="border border-stone-200 rounded p-2 bg-white text-center uppercase text-stone-500">
              Risk Decision
            </div>
            <div className="text-center text-stone-400 text-xs">&darr;</div>
            <div className="border border-stone-200 rounded p-2 bg-white text-center uppercase text-stone-500">
              Validation &amp; Review
            </div>
            <div className="text-center text-stone-400 text-xs">&darr;</div>
            <div className="border border-stone-200 rounded p-2 bg-white text-center uppercase text-stone-500">
              Configuration Reference
            </div>
            <div className="text-center text-stone-400 text-xs">&darr;</div>
            <div className="border border-stone-300 rounded p-2 bg-stone-100 text-center uppercase text-stone-700">
              Handoff Requirement Check
            </div>
            <div className="text-center text-stone-400 text-xs">&darr;</div>
            <div className="border border-[#A8CD16] rounded p-2 bg-[#A8CD16]/10 text-center uppercase text-[#556b03]">
              Release Handoff Package
            </div>
            
            {/* MOBILE BOUNDARY MARKER */}
            <div className="my-2 border-t-2 border-b-2 border-dashed border-red-400 bg-red-50/50 p-2 text-center text-[9px] text-red-800 uppercase">
              Riftless Authority Ends Here
            </div>
            
            <div className="text-center text-stone-400 text-xs">&darr;</div>
            <div className="border border-stone-400 rounded p-2 bg-white text-center uppercase text-stone-600">
              Authorized External Delivery System
            </div>
            <div className="text-center text-stone-400 text-xs">&darr;</div>
            <div className="border border-stone-800 rounded p-2 bg-stone-900 text-white text-center uppercase">
              External Deployment Outcome
            </div>
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
                  <span className="mx-2 text-stone-400">&times;</span>
                  <span>DEPLOYMENT APPROVAL</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>BLOCK DECISION</span>
                  <span className="mx-2 text-stone-400">&times;</span>
                  <span>RELEASE-ELIGIBLE HANDOFF</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>FAILED REQUIRED VALIDATION</span>
                  <span className="mx-2 text-stone-400">&times;</span>
                  <span>RELEASE-ELIGIBLE HANDOFF</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>STALE REVISION</span>
                  <span className="mx-2 text-stone-400">&times;</span>
                  <span>CURRENT HANDOFF STATUS</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* AUTHORITY MODEL */}
      <section className="space-y-4" aria-labelledby="authority-model-heading">
        <h3 id="authority-model-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Authority Model
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The authority model defines target responsibility boundaries for each system actor in the handoff contract:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
          {/* CONTROL PLANE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CONTROL PLANE</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>resolve current predecessor artifacts</li>
              <li>evaluate configured handoff requirements</li>
              <li>distinguish eligible, review-required, and not-eligible outcomes</li>
              <li>prepare permitted handoff references</li>
              <li>record handoff preparation success or failure</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              The control plane may prepare a release handoff only when configured predecessor requirements are satisfied. It cannot execute production deployment.
            </p>
          </div>

          {/* DETERMINISTIC RISK ENGINE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DETERMINISTIC RISK ENGINE</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>provide current Risk Decision</li>
              <li>identify blocked transitions</li>
              <li>identify required validation and acknowledgment gates</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Risk policy may prevent release handoff eligibility. It does not perform deployment.
            </p>
          </div>

          {/* VALIDATION WORKER */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION WORKER</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>provide the required Validation Bundle or non-success result</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Validation evidence may satisfy a configured handoff requirement but does not deploy the change.
            </p>
          </div>

          {/* GITHUB ADAPTER */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">GITHUB ADAPTER</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>display permitted handoff status or evidence references when configured</li>
              <li>associate the handoff result with the evaluated repository revision</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Reporting a handoff status does not merge, release, or deploy the change.
            </p>
          </div>

          {/* EXTERNAL DELIVERY SYSTEM */}
          <div className="border border-stone-200 rounded p-4 bg-stone-50 w-full md:col-span-2 space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">EXTERNAL DELIVERY SYSTEM</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>receive a permitted handoff through an independently authorized integration</li>
              <li>apply its own deployment permissions and environment controls</li>
              <li>execute or reject the deployment outside RIFTLESS authority</li>
              <li>produce its own external deployment outcome when implemented</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed font-semibold">
              External delivery authorization and execution remain distinct from RIFTLESS review authorization.
            </p>
          </div>

          {/* DEEPSEEK */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1 md:col-span-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DEEPSEEK</span>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Target role:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] mb-2">
              <li>explain handoff limitations</li>
              <li>summarize evidence</li>
              <li>suggest release notes or operational considerations</li>
            </ul>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase">Authority boundary:</p>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              DeepSeek cannot approve or execute deployment.
            </p>
          </div>
        </div>

        <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed text-[11px]">
          <strong>Authority Statement:</strong> Risk authorization, validation success, handoff eligibility, external deployment authorization, and deployment success are distinct states.
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* HANDOFF ENTRY REQUIREMENTS */}
      <section className="space-y-4" aria-labelledby="entry-requirements-heading">
        <h3 id="entry-requirements-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Handoff Entry Requirements
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          A target release handoff may be prepared only when the following conditions are met:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              Required Input Conditions
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>current candidate or revision reference is available</li>
              <li>current Risk Decision reference is available</li>
              <li>Risk Decision is not BLOCK</li>
              <li>required validation outcome is successful within its recorded scope when configured policy requires validation</li>
              <li>required acknowledgment or review result is recorded</li>
              <li>effective configuration reference is available</li>
              <li>required artifact references are available</li>
              <li>tested scope and limitations are recorded</li>
              <li>handoff capability is configured and available</li>
              <li>prohibited secret values are excluded</li>
              <li>candidate revision remains current</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              Handoff Logic Boundaries
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li><strong>ALLOW</strong> does not automatically create a handoff.</li>
              <li><strong>WARN</strong> may become handoff-eligible only after configured review requirements are satisfied.</li>
              <li><strong>BLOCK</strong> cannot become handoff-eligible through model output or acknowledgment.</li>
              <li>Successful validation does not independently authorize deployment.</li>
              <li>A prepared handoff does not mean deployment occurred.</li>
              <li>External delivery-system availability does not mean deployment is authorized.</li>
            </ul>
          </div>
        </div>

        {/* EQUATION CALLOUT */}
        <div className="border border-stone-200 rounded bg-stone-50/50 p-4 max-w-4xl space-y-2 text-center">
          <div className="font-mono text-xs md:text-sm font-extrabold text-stone-800 tracking-wider">
            CONFIGURED &ne; HANDOFF ELIGIBLE &ne; HANDOFF PREPARED &ne; DEPLOYMENT AUTHORIZED &ne; DEPLOYED &ne; DEPLOYMENT SUCCEEDED
          </div>
          <p className="text-[11px] text-stone-500 leading-relaxed font-mono max-w-2xl mx-auto">
            These states represent completely separate lifecycle and authorization boundaries. Setting up handoff configuration does not mean a candidate is eligible; eligibility does not mean a handoff package is prepared; preparation does not authorize deployment; deployment authorization is separate from the physical delivery act; and delivery is separate from successful execution.
          </p>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* HANDOFF INPUTS */}
      <section className="space-y-4" aria-labelledby="handoff-inputs-heading">
        <h3 id="handoff-inputs-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Handoff Inputs
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target release handoff contract processes configured inputs to establish eligibility and prepare handoff records:
        </p>

        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="handoff-inputs-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Target inputs used to evaluate and prepare a RIFTLESS release handoff.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Input</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Purpose</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Required or Conditional</th>
                <th scope="col" className="px-4 py-3 w-1/4">Authority Constraint</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CANDIDATE OR REVISION REFERENCE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify the exact reviewed change.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">A repository revision does not establish approval.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK DECISION REFERENCE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide current deterministic policy status and required gates.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">BLOCK prevents release-handoff eligibility.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION BUNDLE REFERENCE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide required scope-bound executable evidence.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required when configured policy requires validation.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Validation does not execute deployment.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ACKNOWLEDGMENT OR REVIEW REFERENCE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide required human-review result for a WARN path.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Does not convert WARN into ALLOW.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">EFFECTIVE CONFIGURATION REFERENCE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify configured handoff requirements and capability boundaries.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configuration is not deployment authorization.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PERMITTED ARTIFACT REFERENCES</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Associate the handoff with decision and evidence records.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional by configured handoff contract.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Artifact presence does not prove deployment occurred.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* ELIGIBILITY STATES */}
      <section className="space-y-4" aria-labelledby="eligibility-states-heading">
        <h3 id="eligibility-states-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Handoff Eligibility States
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The handoff evaluation determines one of five target conceptual eligibility states. These are conceptual target boundaries, not runtime system enums:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl text-xs">
          {/* ELIGIBLE FOR HANDOFF */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ELIGIBLE FOR HANDOFF</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Configured decision, validation, review, revision, and artifact requirements are satisfied for preparation of a release handoff. This does not authorize or execute deployment.
            </p>
          </div>

          {/* REVIEW REQUIRED */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REVIEW REQUIRED</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The candidate has not satisfied a configured acknowledgment, owner-review, or policy-defined manual requirement.
            </p>
          </div>

          {/* NOT ELIGIBLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">NOT ELIGIBLE</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A configured requirement prevents preparation of a release handoff. May result from BLOCK, failed validation, missing required artifact, invalid authorization or review state, prohibited content, or unavailable required input. Non-success states may still be preserved as organizational memory.
            </p>
          </div>

          {/* STALE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">STALE</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The candidate, revision, policy reference, or evidence no longer matches the evaluated handoff scope. Old eligibility must not be inherited.
            </p>
          </div>

          {/* HANDOFF UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1 md:col-span-2 lg:col-span-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">HANDOFF UNAVAILABLE</span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The handoff could not be evaluated or prepared because configuration, capability, or required storage was unavailable. Must not silently become eligible.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="eligibility-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual release-handoff eligibility states and their authority boundaries.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">State</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Meaning</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Permitted Next Action</th>
                <th scope="col" className="px-4 py-3 w-1/4">Must Not Imply</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ELIGIBLE FOR HANDOFF</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured handoff requirements are satisfied.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A permitted handoff package may be prepared.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Deployment authorization or deployment success.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REVIEW REQUIRED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A configured human-review requirement remains unresolved.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record or request the configured review action.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Automatic approval.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">NOT ELIGIBLE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A configured requirement prevents release handoff.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Revise, reevaluate, revalidate, or close according to policy.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">The candidate may proceed.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">STALE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Inputs or evidence no longer match the evaluated scope.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Start a new evaluation or validation as required.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Old eligibility remains current.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">HANDOFF UNAVAILABLE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">The handoff could not be evaluated or prepared.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record the unavailable reason.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Successful preparation.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* RELEASE HANDOFF PACKAGE */}
      <section className="space-y-4" aria-labelledby="handoff-package-heading">
        <h3 id="handoff-package-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Release Handoff Package
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The release handoff package acts as a structured payload representing evaluated evidence and status:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              Permitted Handoff Package Content
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>candidate or revision reference</li>
              <li>Risk Decision reference</li>
              <li>Validation Bundle reference when required</li>
              <li>acknowledgment or review reference</li>
              <li>effective configuration reference</li>
              <li>evaluated scope</li>
              <li>tested scope</li>
              <li>known limitations</li>
              <li>required owner actions</li>
              <li>permitted remediation reference</li>
              <li>permitted artifact references</li>
              <li>handoff eligibility state</li>
              <li>handoff preparation outcome</li>
              <li>external target reference when configured</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50/50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-800 block uppercase">
              STRICTLY PROHIBITED CONTENT
            </span>
            <ul className="list-disc pl-4 text-red-800 space-y-1 text-[11px] font-mono">
              <li>production credentials</li>
              <li>deployment tokens</li>
              <li>private keys</li>
              <li>raw authorization headers</li>
              <li>unrestricted Context Pack content</li>
              <li>unrestricted validation logs</li>
              <li>unrestricted production data</li>
              <li>direct production commands</li>
              <li>model output presented as approval</li>
              <li>fabricated deployment status</li>
            </ul>
          </div>
        </div>

        <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed text-[11px]">
          <strong>Authority Boundary:</strong> A Release Handoff Package is not deployment approval, a deployment command, or evidence that production changed.
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* EXTERNAL DELIVERY BOUNDARY */}
      <section className="space-y-4" aria-labelledby="external-boundary-heading">
        <h3 id="external-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          External Delivery Boundary
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          After a permitted release handoff is prepared, deployment authorization and execution cross into an independently controlled external delivery boundary.
        </p>

        <div className="border border-stone-200 rounded p-4 bg-white max-w-4xl text-xs space-y-3">
          <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
            Boundary Principles
          </span>
          <ul className="list-disc pl-4 text-stone-600 space-y-1.5 text-[11px]">
            <li><strong>Independent Controls:</strong> External delivery controls remain independently responsible for security, scheduling, and validation.</li>
            <li><strong>External Authorization:</strong> Deployment authorization must be established by the independently controlled external delivery system. A verified integration may later provide an external outcome reference without transferring deployment authority to RIFTLESS.</li>
            <li><strong>External Environment:</strong> Environment selection (e.g., staging, production) remains external.</li>
            <li><strong>External Secrets:</strong> Production credentials, keys, and tokens remain strictly external.</li>
            <li><strong>External Lifecycle:</strong> Deployment execution, rollback, health checks, and release completion remain entirely external.</li>
            <li><strong>No Outcome Inference:</strong> The success or failure of an external deployment must not be inferred from handoff preparation.</li>
            <li><strong>Verified Integration Only:</strong> External outcomes may be referenced later only when a verified, secure integration is configured and implemented.</li>
          </ul>
        </div>

        <Callout type="warning">
          RIFTLESS review authorization must not be reused as an unrestricted production-deployment credential or approval token.
        </Callout>

        <Callout type="note">
          No CI/CD platform, deployment provider, database migration runner, or environment-promotion system is selected by this target contract.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* DECISION AND VALIDATION MAPPING */}
      <section className="space-y-4" aria-labelledby="mapping-heading">
        <h3 id="mapping-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Decision and Validation Mapping
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The handoff evaluation maps the active deterministic decision state and validation results to a conceptual eligibility:
        </p>

        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="mapping-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual relationship between RIFTLESS review states and release-handoff eligibility.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Review Condition</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Handoff Interpretation</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Required Additional Condition</th>
                <th scope="col" className="px-4 py-3 w-1/4">Prohibited Interpretation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ALLOW WITH REQUIRED VALIDATION PASSED</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">May be eligible for handoff.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Recorded handoff requirements and current revision.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Automatic deployment approval.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ALLOW WITH REQUIRED VALIDATION MISSING</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Not yet eligible.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required validation must complete successfully.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">ALLOW bypasses validation.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WARN WITH REQUIRED REVIEW COMPLETE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">May be eligible when configured policy permits.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Recorded review result and required validation.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">WARN became ALLOW.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WARN WITH REVIEW INCOMPLETE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Review required.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured acknowledgment or human-review result.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Automatic handoff eligibility.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">BLOCK</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Not eligible.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Change must be revised and deterministically reevaluated.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Model output or acknowledgment clears BLOCK.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">FAILED REQUIRED VALIDATION</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Not eligible.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Candidate revision and validation must be revised or rerun.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Failure represented as successful evidence.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">STALE REVISION OR EVIDENCE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Stale.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">New evaluation or validation as required.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Old eligibility remains current.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* TARGET OPERATION SHAPES */}
      <section className="space-y-4" aria-labelledby="operation-shapes-heading">
        <h3 id="operation-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Target Operation Shapes
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          These conceptual interfaces describe the target operations for evaluating handoff eligibility and planning packages:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
          {/* Block 1 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL HANDOFF ELIGIBILITY CHECK <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
            </span>
            <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive current candidate reference
receive current Risk Decision
receive required Validation Bundle
receive required acknowledgment or review reference
receive effective handoff requirements
check revision and scope consistency
record missing or stale requirements
return target handoff eligibility state`}
            </pre>
          </div>

          {/* Block 2 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL HANDOFF PREPARATION <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
            </span>
            <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive eligible handoff result
select permitted source references
exclude prohibited values
assemble evaluated and tested scope
record limitations and owner actions
prepare target Release Handoff Package
record preparation success or failure
return permitted handoff package reference`}
            </pre>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
          Exact delivery APIs, CI/CD operations, deployment commands, environment identifiers, credentials, and external result payloads will be documented only after an independently authorized deployment integration is implemented and versioned.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* REEVALUATION */}
      <section className="space-y-4" aria-labelledby="reevaluation-heading">
        <h3 id="reevaluation-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Handoff Reevaluation
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          Handoff status represents a static snapshot of evaluated change inputs. A new handoff evaluation should be required when any of the following occur:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              Reevaluation Triggers
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>candidate content changes</li>
              <li>repository revision changes</li>
              <li>Risk Decision changes</li>
              <li>relevant policy changes</li>
              <li>Validation Bundle becomes stale</li>
              <li>validation scope changes materially</li>
              <li>acknowledgment or review state changes</li>
              <li>handoff requirements change</li>
              <li>permitted artifact references change materially</li>
              <li>external target mapping changes</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              Target Evaluation Rules
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>previous handoff result remains referenced</li>
              <li>successor identifies its evaluated inputs</li>
              <li>old eligibility does not automatically apply to changed input</li>
              <li>old handoff preparation does not prove current deployment eligibility</li>
              <li>stale handoff packages remain distinguishable</li>
              <li>model explanation alone does not reestablish eligibility</li>
            </ul>
          </div>
        </div>

        <Callout type="target">
          The final handoff identifier, supersession, expiration, and history model must be derived from implemented artifact contracts and delivery integrations.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* DEPLOYMENT HANDOFF FAILURE BEHAVIOR */}
      <section className="space-y-4" aria-labelledby="failure-behavior-heading">
        <h3 id="failure-behavior-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Deployment Handoff Failure Behavior
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target handoff contract defines non-success behavior when required inputs, review states, package preparation, storage, or external delivery availability cannot be established.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl text-xs">
          {/* HANDOFF CONFIGURATION UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">HANDOFF CONFIGURATION UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>eligibility cannot be established</li>
              <li>no successful handoff result is fabricated</li>
            </ul>
          </div>

          {/* REQUIRED DECISION UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REQUIRED DECISION UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>preparation must not begin</li>
              <li>UI must not infer status</li>
            </ul>
          </div>

          {/* REQUIRED VALIDATION UNAVAILABLE OR FAILED */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REQUIRED VALIDATION UNAVAILABLE OR FAILED</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>eligible status must not be recorded</li>
              <li>failure or unavailable state remains visible</li>
            </ul>
          </div>

          {/* REVIEW REQUIREMENT INCOMPLETE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REVIEW REQUIREMENT INCOMPLETE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>state remains REVIEW REQUIRED</li>
              <li>no automatic approval occurs</li>
            </ul>
          </div>

          {/* REVISION STALE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REVISION STALE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>previous handoff result must not appear current</li>
              <li>new evaluation is required</li>
            </ul>
          </div>

          {/* PROHIBITED CONTENT DETECTED */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PROHIBITED CONTENT DETECTED</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>handoff package must not expose the prohibited value</li>
              <li>failure reason should not reproduce the secret</li>
            </ul>
          </div>

          {/* HANDOFF PACKAGE INVALID */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">HANDOFF PACKAGE INVALID</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>external delivery handoff must not proceed</li>
              <li>protected state must not infer success</li>
            </ul>
          </div>

          {/* HANDOFF STORAGE UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">HANDOFF STORAGE UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>package must not be reported as successfully preserved</li>
              <li>eligibility result and package storage remain distinct</li>
            </ul>
          </div>

          {/* EXTERNAL DELIVERY UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">EXTERNAL DELIVERY UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>RIFTLESS handoff preparation and external delivery availability remain distinct</li>
              <li>no deployment result is fabricated</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* DEPLOYMENT HANDOFF INVARIANTS */}
      <section className="space-y-4" aria-labelledby="invariants-heading">
        <h3 id="invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          Deployment Handoff Invariants
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target deployment-handoff contract defines the following invariants:
        </p>

        <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">CANDIDATE SCOPE REMAINS IDENTIFIABLE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">RISK DECISION REMAINS DETERMINISTIC.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION EVIDENCE REMAINS SCOPE-BOUND.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">REVIEW REQUIREMENTS REMAIN EXPLICIT.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS NON-AUTHORIZING.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">BLOCK REMAINS NOT ELIGIBLE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">STALE EVIDENCE DOES NOT BECOME CURRENT.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">HANDOFF ELIGIBILITY REMAINS DISTINCT FROM DEPLOYMENT AUTHORIZATION.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">HANDOFF PREPARATION REMAINS DISTINCT FROM DEPLOYMENT EXECUTION.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">DEPLOYMENT EXECUTION REMAINS EXTERNAL.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">DEPLOYMENT SUCCESS REMAINS UNINFERRED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN OUTSIDE THE HANDOFF PACKAGE.</div>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
          These statements describe target deployment-handoff requirements, not proof that CI/CD integration, deployment authorization, production execution, rollback, or external outcome reporting has already been implemented.
        </p>
      </section>
    </section>
  );
}
