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

export function ApiReferenceSection() {
  return (
    <section id="api-reference" aria-labelledby="api-reference-heading" className="space-y-8 animate-none scroll-mt-24">
      {/* 1. Title, Lead, and TARGET Callout */}
      <div className="space-y-4">
        <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
          REFERENCE
        </span>
        <h2 id="api-reference-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
          API REFERENCE
        </h2>
        
        <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
          The target RIFTLESS API contract defines bounded operations for review intake, context assembly, deterministic decisions, advisory remediation, validation, artifact access, writeback, recovery, handoff preparation, and operational visibility.
        </p>

        <Callout type="target" title="TARGET CAPABILITY">
          This section describes conceptual API boundaries only. Endpoint paths, HTTP methods, authentication protocols, request schemas, response schemas, status codes, pagination rules, rate limits, and versioning mechanisms remain undefined until a repository-backed API is implemented and versioned.
        </Callout>
      </div>

      <hr className="border-stone-200/50" />

      {/* 2. CORE API PRINCIPLES */}
      <section className="space-y-4" aria-labelledby="core-api-principles-heading">
        <h3 id="core-api-principles-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          CORE API PRINCIPLES
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              BOUNDED OPERATIONS
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Each request should identify one configured operation and its relevant candidate, run, revision, or artifact scope.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SERVER-SIDE PROTECTED ACTIONS
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Validation execution, writeback, authorization checks, credential resolution, and protected integrations must remain server-side.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              EXPLICIT PREDECESSORS
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Protected operations should reference required predecessor artifacts instead of relying on optimistic client state.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              OPERATION-SPECIFIC AUTHORIZATION
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Authentication, capability availability, and authorization remain distinct.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              EXPLICIT NON-SUCCESS
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Invalid, rejected, unauthorized, unavailable, stale, partial, and failed results should remain distinguishable.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REFERENCE-BASED RESPONSES
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Responses should prefer permitted artifact and result references rather than duplicating unrestricted source content.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2 lg:col-span-3">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              NO AUTHORITY BY TRANSPORT
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A successful API transport response does not mean a Risk Decision is ALLOW, validation passed, writeback completed, or deployment occurred.
            </p>
          </div>
        </div>

        <Callout type="note">
          An API contract describes how an operation may be requested and reported. It does not grant the operation authority by itself.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* 3. TARGET API FLOW */}
      <section className="space-y-4" aria-labelledby="target-api-flow-heading">
        <h3 id="target-api-flow-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET API OPERATION FLOW
        </h3>
        
        <div className="border border-stone-200 rounded p-6 bg-stone-50/50 max-w-5xl space-y-6">
          <div className="font-mono text-[10px] font-bold text-stone-500 uppercase tracking-wider block border-b border-stone-200 pb-2">
            Target API Operation Flow
          </div>
          
          {/* Desktop horizontal flow */}
          <div className="hidden lg:flex flex-wrap items-center gap-1 font-mono text-[8px] font-bold text-stone-700 leading-tight">
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              CLIENT OR INTEGRATION REQUEST
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              REQUEST BOUNDARY
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              INPUT AND SCOPE CHECK
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              AUTHORIZATION REQUIREMENT CHECK
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-2 text-center shadow-sm uppercase text-[#556b03] min-w-[120px]">
              TARGET OPERATION
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700 min-w-[120px]">
              RESULT OR FAILURE RECORDING
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-stone-100 rounded p-2 text-center shadow-sm uppercase text-stone-500 min-w-[120px]">
              BOUNDED RESPONSE
            </div>
          </div>

          {/* Mobile vertical Flow Sequence */}
          <div className="lg:hidden space-y-2 font-mono text-[10px] font-bold">
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              CLIENT OR INTEGRATION REQUEST
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              REQUEST BOUNDARY
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              INPUT AND SCOPE CHECK
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              AUTHORIZATION REQUIREMENT CHECK
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-2 text-center uppercase text-[#556b03]">
              TARGET OPERATION
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              RESULT OR FAILURE RECORDING
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-stone-100 rounded p-2 text-center uppercase text-stone-500">
              BOUNDED RESPONSE
            </div>
          </div>

          {/* SUPPORTING REFERENCES */}
          <div className="space-y-2 pt-4 border-t border-stone-200">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              Supporting References
            </span>
            <ul className="list-disc pl-5 text-stone-600 space-y-1 text-xs font-mono">
              <li>REQUEST REFERENCE</li>
              <li>RUN OR CANDIDATE REFERENCE</li>
              <li>REVISION REFERENCE</li>
              <li>EFFECTIVE CONFIGURATION REFERENCE</li>
              <li>PREDECESSOR ARTIFACT REFERENCES</li>
              <li>AUTHORIZATION REFERENCE WHEN REQUIRED</li>
            </ul>
          </div>

          {/* BLOCKED PATHS */}
          <div className="space-y-3 pt-4 border-t border-stone-200">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              Blocked Paths (Transitions Rejected)
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-[10px] font-bold">
              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>BROWSER CLIENT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>SERVER-SIDE CREDENTIALS</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>MODEL OUTPUT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>API AUTHORIZATION</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>STALE REVISION</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>CURRENT OPERATION RESULT</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div className="flex flex-wrap items-center">
                  <span>INVALID PREDECESSOR STATE</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>PROTECTED OPERATION</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900 md:col-span-2">
                <div className="flex flex-wrap items-center">
                  <span>UNFILTERED OUTPUT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>PUBLIC RESPONSE</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black shrink-0 ml-2">BLOCKED</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* 4. API ACTORS AND AUTHORITY */}
      <section className="space-y-4" aria-labelledby="api-actors-heading">
        <h3 id="api-actors-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          API ACTORS
        </h3>
        
        <div className="space-y-6 max-w-5xl text-xs">
          {/* ACTOR 1 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
            <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
              PUBLIC OR BROWSER CLIENT
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-[10px]">
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-emerald-700 block uppercase">MAY:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
                  <li>submit bounded requests</li>
                  <li>read permitted public or review data</li>
                  <li>reference existing run or artifact identifiers</li>
                </ul>
              </div>
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-red-700 block uppercase">MUST NOT:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
                  <li>receive server-side credentials</li>
                  <li>directly execute validators</li>
                  <li>directly perform writeback</li>
                  <li>determine authorization from local state</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ACTOR 2 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase tracking-wider">
              CONTROL PLANE
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-[10px]">
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-emerald-700 block uppercase">MAY:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
                  <li>validate request scope</li>
                  <li>resolve predecessor artifacts</li>
                  <li>check configured authorization requirements</li>
                  <li>coordinate target operations</li>
                  <li>record operation results</li>
                </ul>
              </div>
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-red-700 block uppercase">MUST NOT:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
                  <li>fabricate predecessor success</li>
                  <li>accept model output as authorization</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ACTOR 3 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase tracking-wider">
              INTEGRATION ADAPTER
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-[10px]">
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-emerald-700 block uppercase">MAY:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
                  <li>perform a permitted DataHub, GitHub, DeepSeek, or external integration operation</li>
                </ul>
              </div>
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-red-700 block uppercase">MUST NOT:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
                  <li>expand its configured scope</li>
                  <li>create authorization</li>
                  <li>reinterpret deterministic decisions</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ACTOR 4 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase tracking-wider">
              VALIDATION WORKER
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-[10px]">
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-emerald-700 block uppercase">MAY:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
                  <li>execute an authorized Validation Plan against bounded inputs</li>
                </ul>
              </div>
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-red-700 block uppercase">MUST NOT:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
                  <li>authorize itself</li>
                  <li>perform writeback</li>
                  <li>deploy changes</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ACTOR 5 */}
          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase tracking-wider">
              EXTERNAL DELIVERY SYSTEM
            </span>
            <div className="space-y-1">
              <span className="text-[9px] font-bold text-emerald-700 block uppercase font-mono">MAY:</span>
              <p className="text-stone-600 text-[11px] leading-relaxed">
                independently authorize and execute deployment
              </p>
            </div>
            <div className="pt-2 border-t border-stone-200/60 text-stone-600 text-[11px] font-semibold">
              Must remain outside RIFTLESS deployment authority.
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* 5. CONCEPTUAL OPERATION GROUPS */}
      <section className="space-y-4" aria-labelledby="operation-groups-heading">
        <h3 id="operation-groups-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          OPERATION GROUPS
        </h3>
        
        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-5xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="api-operation-groups-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual RIFTLESS API operation groups and their authority boundaries.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[20%]">Operation Group</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Target Purpose</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Required Source</th>
                <th scope="col" className="px-4 py-3 w-[30%]">Authority Boundary</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REVIEW INTAKE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Submit or reference a proposed change.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Bounded submitted input or repository reference.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Does not authorize evaluation or execution by itself.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RUN STATUS</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Read permitted lifecycle and artifact references.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Run reference.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Displayed status does not replace recorded artifacts.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTEXT ASSEMBLY</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Request bounded organizational context assembly.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Change Request and configured metadata scope.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Context does not create a Risk Decision.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK EVALUATION</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Request configured deterministic policy evaluation.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Change Request, Context Pack, and effective configuration.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Only deterministic evaluation may create the target Risk Decision.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REMEDIATION ASSISTANCE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Request advisory explanation or proposal.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Permitted change and redacted context.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Model output remains advisory.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Prepare or execute configured validation.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Current Risk Decision, Validation Plan, and authorization.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Validation evidence does not authorize deployment or writeback independently.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACT ACCESS</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Read permitted artifacts and relationships.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Run or artifact reference.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Artifact retrieval does not change run state.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITEBACK</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Prepare or execute an authorized metadata operation.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Decision, required evidence, mapping, and authorization.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Destination completion does not imply approval.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RECOVERY</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Classify failure or request a permitted recovery path.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Failure Record and predecessor references.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Recovery does not rewrite historical failure.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">HANDOFF PREPARATION</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Evaluate or prepare a Release Handoff Package.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Current decision, required validation, review state, and revision.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Handoff preparation is not deployment.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">OBSERVABILITY</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Read permitted operational signals and source references.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Run, event, or artifact references.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top font-mono text-[10px]">Observability remains non-authorizing.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* 6. CONCEPTUAL REQUEST CONTRACT */}
      <section className="space-y-4" aria-labelledby="request-contract-heading">
        <h3 id="request-contract-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          REQUEST CONTRACT
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase tracking-wider">
              TARGET REQUEST CONTENT MAY INCLUDE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>conceptual operation category</li>
              <li>request reference</li>
              <li>run reference when available</li>
              <li>candidate or revision reference</li>
              <li>effective configuration reference</li>
              <li>predecessor artifact references</li>
              <li>authorization reference when required</li>
              <li>requested scope</li>
              <li>permitted input references</li>
              <li>explicit requested action</li>
              <li>client correlation reference when permitted</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-900 block uppercase tracking-wider">
              MUST NOT CONTAIN
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>server-side credentials</li>
              <li>private keys</li>
              <li>raw authorization headers in ordinary operation content</li>
              <li>unrestricted repository exports</li>
              <li>unrestricted Context Pack content</li>
              <li>unrestricted validation logs</li>
              <li>private model reasoning</li>
              <li>fabricated predecessor references</li>
            </ul>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] italic">
          The exact field names and serialization format remain undefined.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* 7. CONCEPTUAL RESPONSE CONTRACT */}
      <section className="space-y-4" aria-labelledby="response-contract-heading">
        <h3 id="response-contract-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          RESPONSE CONTRACT
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              TARGET RESPONSE MAY INCLUDE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>request reference</li>
              <li>operation category</li>
              <li>accepted or rejected request state</li>
              <li>result reference</li>
              <li>artifact reference</li>
              <li>Failure Record reference</li>
              <li>current run or stage reference</li>
              <li>limitations</li>
              <li>stale or superseded indication</li>
              <li>authorization requirement indication</li>
              <li>permitted diagnostic reference</li>
              <li>storage outcome when relevant</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-4">
            <div className="space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                AUTHORITY BOUNDARY
              </span>
              <p className="text-stone-600 text-[11px] leading-relaxed">
                A response reports the API operation result. It does not create authorization or replace the referenced artifact.
              </p>
            </div>

            <Callout type="warning" title="TRANSPORT SUCCESS WARNING">
              A transport-level success response must not be interpreted as proof that the requested business operation completed successfully.
            </Callout>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* 8. CONCEPTUAL OPERATION RESULT STATES */}
      <section className="space-y-4" aria-labelledby="result-states-heading">
        <h3 id="result-states-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          OPERATION RESULT STATES
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following states represent the conceptual results of API requests, distinct from official API enums:
        </p>

        <div className="space-y-4 max-w-5xl text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RECEIVED</span>
              <p className="text-stone-600 text-[11px] leading-relaxed">The request crossed the initial API boundary.</p>
            </div>
            
            <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ACCEPTED FOR PROCESSING</span>
              <p className="text-stone-600 text-[11px] leading-relaxed">The request passed initial structure and scope checks.</p>
            </div>

            <div className="border border-red-200 rounded p-4 bg-red-50/20 space-y-1">
              <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">REJECTED</span>
              <p className="text-red-800 text-[11px] leading-relaxed">The request did not satisfy content, scope, policy, or security requirements.</p>
            </div>

            <div className="border border-amber-200 rounded p-4 bg-amber-50/10 space-y-1">
              <span className="font-mono text-[10px] font-bold text-amber-900 block uppercase">AUTHORIZATION REQUIRED</span>
              <p className="text-amber-800 text-[11px] leading-relaxed">A protected operation cannot continue without a valid operation-specific authorization state.</p>
            </div>

            <div className="border border-red-200 rounded p-4 bg-red-50/20 space-y-1">
              <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">INVALID</span>
              <p className="text-red-800 text-[11px] leading-relaxed">The request or required predecessor references were malformed or inconsistent.</p>
            </div>

            <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
              <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">IN PROGRESS</span>
              <p className="text-stone-600 text-[11px] leading-relaxed">The operation has not yet produced a final recorded result.</p>
            </div>

            <div className="border border-[#A8CD16]/40 rounded p-4 bg-lime-50/10 space-y-1">
              <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase">COMPLETED</span>
              <p className="text-[#556b03] text-[11px] leading-relaxed">The requested target operation completed for its recorded scope.</p>
            </div>

            <div className="border border-amber-200 rounded p-4 bg-amber-50/10 space-y-1">
              <span className="font-mono text-[10px] font-bold text-amber-900 block uppercase">PARTIAL</span>
              <p className="text-amber-800 text-[11px] leading-relaxed">Only part of the permitted operation completed.</p>
            </div>

            <div className="border border-red-200 rounded p-4 bg-red-50/20 space-y-1">
              <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">FAILED</span>
              <p className="text-red-800 text-[11px] leading-relaxed">The operation could not complete.</p>
            </div>

            <div className="border border-red-200 rounded p-4 bg-red-50/20 space-y-1">
              <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">UNAVAILABLE</span>
              <p className="text-red-800 text-[11px] leading-relaxed">A required capability or dependency was unavailable.</p>
            </div>

            <div className="border border-red-200 rounded p-4 bg-red-50/20 space-y-1 md:col-span-2">
              <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">STALE</span>
              <p className="text-red-800 text-[11px] leading-relaxed">The request or result no longer matches the current candidate, revision, or operation scope.</p>
            </div>
          </div>

          <div className="p-4 border border-stone-300 bg-stone-50 rounded max-w-2xl">
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-xs leading-relaxed font-mono">
              <li>RECEIVED is not ACCEPTED</li>
              <li>ACCEPTED is not COMPLETED</li>
              <li>COMPLETED does not imply ALLOW, passed validation, approval, or deployment</li>
              <li>PARTIAL is not COMPLETED</li>
              <li>FAILED and REJECTED remain distinct</li>
              <li>STALE must not appear current</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* 9. ERROR AND NON-SUCCESS MODEL */}
      <section className="space-y-4" aria-labelledby="error-categories-heading">
        <h3 id="error-categories-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          ERROR AND NON-SUCCESS CATEGORIES
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following conceptual categories partition failure conditions without relying on implementation details:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REQUEST STRUCTURE ERROR
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The submitted operation shape could not be interpreted.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SCOPE ERROR
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The requested repository, run, revision, asset, or operation was outside configured scope.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              AUTHENTICATION UNAVAILABLE
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Identity could not be established after implementation defines authentication.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              AUTHORIZATION MISSING OR INVALID
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The protected operation lacked applicable authorization.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              PREDECESSOR STATE ERROR
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Required artifact or lifecycle state was missing, stale, or inconsistent.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              POLICY OR VALIDATION ERROR
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Required deterministic evaluation or validation could not complete.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              DEPENDENCY UNAVAILABLE
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A required integration, validator, destination, or external system was unavailable.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              CONTENT SECURITY ERROR
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Prohibited or unredacted content was detected.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              PERSISTENCE ERROR
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              The operation result or artifact could not be successfully preserved.
            </p>
          </div>
        </div>

        <div className="p-4 border border-stone-300 bg-stone-50 rounded max-w-2xl text-xs text-stone-600 leading-relaxed font-mono">
          <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase mb-1">CLARIFICATIONS</span>
          <ul className="list-disc pl-4 space-y-0.5">
            <li>no error automatically becomes ALLOW</li>
            <li>an API error does not erase previously recorded artifacts</li>
            <li>error responses must not reproduce credentials or secret values</li>
            <li>exact status-code mapping remains undefined</li>
          </ul>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* 10. SECURITY BOUNDARY */}
      <section className="space-y-4" aria-labelledby="api-security-boundary-heading">
        <h3 id="api-security-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          API SECURITY BOUNDARY
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target API security contract defines the following boundary requirements:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SECURITY BOUNDARY PROTOCOLS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-sans">
              <li>protected operations remain server-side</li>
              <li>authorization remains operation-specific</li>
              <li>previous authorization must not automatically apply after scope changes</li>
              <li>browser code must not receive server-side credentials</li>
              <li>model output cannot authenticate or authorize</li>
              <li>client-provided artifact references must be validated</li>
              <li>response filtering occurs before browser or external exposure</li>
              <li>unrestricted logs must not appear in responses</li>
              <li>stale revision and scope mismatch remain explicit</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-6 bg-stone-50/50 flex flex-col justify-center items-center font-mono text-xs text-center space-y-3">
            <div className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">
              AUTHORITY DISCONNECTIONS
            </div>
            <div className="text-stone-800 leading-relaxed space-y-1 text-sm font-bold uppercase">
              <div>AUTHENTICATED</div>
              <div className="text-stone-300 text-xs font-normal" aria-hidden="true">&ne;</div>
              <div>AUTHORIZED</div>
              <div className="text-stone-300 text-xs font-normal" aria-hidden="true">&ne;</div>
              <div>ACCEPTED</div>
              <div className="text-stone-300 text-xs font-normal" aria-hidden="true">&ne;</div>
              <div>COMPLETED</div>
              <div className="text-stone-300 text-xs font-normal" aria-hidden="true">&ne;</div>
              <div>SUCCESSFUL</div>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* 11. ARTIFACT AND REFERENCE ACCESS */}
      <section className="space-y-4" aria-labelledby="artifact-access-heading">
        <h3 id="artifact-access-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          ARTIFACT ACCESS
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase tracking-wider">
              TARGET ARTIFACT ACCESS MAY SUPPORT
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>permitted artifact retrieval by reference</li>
              <li>relationship lookup between predecessor and successor artifacts</li>
              <li>current versus superseded status</li>
              <li>permitted failure and limitation references</li>
              <li>tested-scope and evaluated-scope references</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-900 block uppercase tracking-wider">
              MUST NOT:
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>expose credentials</li>
              <li>expose unrestricted logs</li>
              <li>expose unrestricted source content</li>
              <li>silently reinterpret incompatible contract versions</li>
              <li>treat artifact retrieval as authorization</li>
              <li>mutate artifacts through a read operation</li>
            </ul>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] italic">
          Endpoint paths, query parameters, pagination style, database keys, and artifact ID formats remain undefined.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* 12. VERSIONING AND COMPATIBILITY */}
      <section className="space-y-4" aria-labelledby="api-versioning-heading">
        <h3 id="api-versioning-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          API VERSIONING
        </h3>
        
        <div className="border border-stone-200 rounded p-4 bg-white space-y-3 max-w-5xl text-xs">
          <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
            TARGET REQUIREMENTS
          </span>
          <ul className="list-disc pl-5 text-stone-600 space-y-1 text-[11px]">
            <li>API contract version should remain identifiable once implemented</li>
            <li>request and response interpretation should follow the applicable contract version</li>
            <li>incompatible behavior should not silently reinterpret older clients</li>
            <li>deprecated operations should remain distinguishable</li>
            <li>artifact-contract version and API version must not be assumed identical</li>
            <li>migration behavior remains undefined</li>
          </ul>
        </div>

        <Callout type="target" title="TARGET CAPABILITY">
          The final URL versioning, header versioning, schema negotiation, deprecation, and compatibility strategy must be derived from the implemented API.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* 13. NON-EXECUTABLE OPERATION SHAPES */}
      <section className="space-y-4" aria-labelledby="api-operation-shapes-heading">
        <h3 id="api-operation-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET OPERATION SHAPES
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following pseudo-interfaces describe the logical execution structure of target operations:
        </p>

        <div className="space-y-6 max-w-5xl">
          {/* Block 1 */}
          <div className="space-y-1">
            <div className="flex items-center justify-between px-4 py-2 bg-stone-800 text-stone-300 text-[10px] font-mono rounded-t border-b border-stone-700">
              <span>CONCEPTUAL API REQUEST HANDLING</span>
              <span className="text-[#A8CD16]">NON-EXECUTABLE TARGET INTERFACE</span>
            </div>
            <pre className="p-4 bg-stone-900 rounded-b text-stone-100 font-mono text-xs overflow-x-auto leading-relaxed">
{`receive target operation category
receive bounded request and source references
validate structure and configured scope
resolve required predecessor artifacts
check authorization requirements
invoke permitted target operation
record result or non-success outcome
return bounded target response`}
            </pre>
          </div>

          {/* Block 2 */}
          <div className="space-y-1">
            <div className="flex items-center justify-between px-4 py-2 bg-stone-800 text-stone-300 text-[10px] font-mono rounded-t border-b border-stone-700">
              <span>CONCEPTUAL ARTIFACT READ</span>
              <span className="text-[#A8CD16]">NON-EXECUTABLE TARGET INTERFACE</span>
            </div>
            <pre className="p-4 bg-stone-900 rounded-b text-stone-100 font-mono text-xs overflow-x-auto leading-relaxed">
{`receive permitted artifact reference
check access and content boundaries
resolve contract version
retrieve permitted artifact fields
exclude prohibited values
return target artifact-read result`}
            </pre>
          </div>

          {/* Block 3 */}
          <div className="space-y-1">
            <div className="flex items-center justify-between px-4 py-2 bg-stone-800 text-stone-300 text-[10px] font-mono rounded-t border-b border-stone-700">
              <span>CONCEPTUAL PROTECTED OPERATION</span>
              <span className="text-[#A8CD16]">NON-EXECUTABLE TARGET INTERFACE</span>
            </div>
            <pre className="p-4 bg-stone-900 rounded-b text-stone-100 font-mono text-xs overflow-x-auto leading-relaxed">
{`receive protected operation request
receive operation-specific authorization reference
check candidate, revision, and predecessor consistency
execute or coordinate permitted server-side operation
record operation and persistence outcomes separately
return target protected-operation result`}
            </pre>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-4xl mt-4">
          Exact endpoint paths, HTTP methods, headers, request payloads, response payloads, status codes, authentication flows, pagination, streaming, rate limits, and SDK behavior will be documented only after the repository-backed API is implemented and versioned.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* 14. API FAILURE BEHAVIOR */}
      <section className="space-y-4" aria-labelledby="api-failure-behavior-heading">
        <h3 id="api-failure-behavior-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          API FAILURE BEHAVIOR
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          {/* BEHAVIOR 1 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REQUEST INVALID
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
              <li>operation must not begin</li>
              <li>malformed input remains explicit</li>
            </ul>
          </div>

          {/* BEHAVIOR 2 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SCOPE MISMATCH
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
              <li>request must not use authorization from another scope</li>
              <li>new authorization may be required</li>
            </ul>
          </div>

          {/* BEHAVIOR 3 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              AUTHORIZATION UNAVAILABLE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
              <li>protected operation must not execute</li>
              <li>capability availability must not bypass authorization</li>
            </ul>
          </div>

          {/* BEHAVIOR 4 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              PREDECESSOR REFERENCE MISSING
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
              <li>operation remains unresolved</li>
              <li>protected next stage must not infer success</li>
            </ul>
          </div>

          {/* BEHAVIOR 5 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              DEPENDENCY UNAVAILABLE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
              <li>operation must not be reported as completed</li>
              <li>dependency status and operation result remain distinct</li>
            </ul>
          </div>

          {/* BEHAVIOR 6 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              RESPONSE FILTERING FAILURE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
              <li>prohibited content must not be exposed</li>
              <li>failure reason must not reproduce the secret</li>
            </ul>
          </div>

          {/* BEHAVIOR 7 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              RESULT PERSISTENCE UNAVAILABLE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
              <li>operation result must not be reported as successfully preserved</li>
              <li>operation completion and persistence remain distinct</li>
            </ul>
          </div>

          {/* BEHAVIOR 8 */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              STALE REQUEST OR RESULT
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-sans">
              <li>old status must not appear current</li>
              <li>reevaluation or a new request may be required</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* 15. API INVARIANTS */}
      <section className="space-y-4" aria-labelledby="api-invariants-heading">
        <h3 id="api-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          API INVARIANTS
        </h3>
        
        <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">REQUEST SCOPE REMAINS IDENTIFIABLE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">PROTECTED OPERATIONS REMAIN SERVER-SIDE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">AUTHORIZATION REMAINS OPERATION-SPECIFIC.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS NON-AUTHORIZING.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">PREDECESSOR STATES REMAIN EXPLICIT.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">STALE REFERENCES DO NOT BECOME CURRENT.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">TRANSPORT SUCCESS DOES NOT IMPLY BUSINESS SUCCESS.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">PARTIAL DOES NOT BECOME COMPLETED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">FAILURE DOES NOT BECOME SUCCESS.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">ARTIFACTS REMAIN THE SOURCE OF TRUTH.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN EXCLUDED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">OPERATION SUCCESS REMAINS DISTINCT FROM PERSISTENCE.</div>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
          These statements describe target API requirements, not proof that routes, authentication, authorization middleware, schemas, workers, persistence, SDKs, or deployment infrastructure have already been implemented.
        </p>
      </section>
    </section>
  );
}
