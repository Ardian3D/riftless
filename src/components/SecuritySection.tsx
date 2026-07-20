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

export function SecuritySection() {
  return (
    <section id="security" aria-labelledby="security-heading" className="space-y-8 animate-none scroll-mt-24">
      {/* Title & Lead */}
      <div className="space-y-4">
        <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
          OPERATIONS
        </span>
        <h2 id="security-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
          SECURITY
        </h2>
        
        <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
          RIFTLESS security boundaries limit how untrusted inputs, credentials, model context, executable validation, artifacts, writeback operations, and external handoffs may interact with protected system capabilities.
        </p>

        <Callout type="target" title="TARGET SECURITY CONTRACT">
          This section describes the target security contract. Identity providers, authentication protocols, secret stores, encryption mechanisms, network controls, runtime isolation, audit infrastructure, and incident-response integrations remain undefined until repository-backed security controls are implemented and verified.
        </Callout>
      </div>

      <hr className="border-stone-200/50" />

      {/* CORE SECURITY PRINCIPLES */}
      <section className="space-y-4" aria-labelledby="core-principles-heading">
        <h3 id="core-principles-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          CORE SECURITY PRINCIPLES
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              UNTRUSTED BY DEFAULT
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Repository content, SQL, metadata descriptions, comments, logs, external responses, and previous model output should be treated as data rather than control instructions.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              LEAST CAPABILITY
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Each component should receive only the configured capability, data scope, credentials, and operation permissions required for its assigned task.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SERVER-SIDE SECRETS
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Credentials, tokens, private keys, authorization headers, and secret environment values must remain outside browser code, model context, ordinary artifacts, and organizational metadata records.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              BOUNDED CONTEXT
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Model requests, validator inputs, metadata reads, repository reads, and writeback content should remain limited to configured and relevant scope.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              EXPLICIT AUTHORIZATION
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              A capability being enabled or available must not be treated as authorization for a protected operation.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              SEPARATED AUTHORITY
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Model analysis, deterministic policy, executable validation, writeback authorization, and external deployment authorization remain distinct responsibilities.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TRACEABLE NON-SUCCESS
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              Rejected, unavailable, indeterminate, partial, and failed security-control outcomes should remain visible rather than silently becoming success.
            </p>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              NO SECURITY BY PRESENTATION
            </span>
            <p className="text-stone-600 leading-relaxed text-[11px]">
              UI color, labels, icons, or optimistic client state must not be the source of truth for authorization or security status.
            </p>
          </div>
        </div>

        <Callout type="note">
          Documentation of a security boundary is not evidence that its runtime control has been implemented, tested, or independently verified.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* TARGET SECURITY FLOW */}
      <section className="space-y-4" aria-labelledby="security-flow-heading">
        <h3 id="security-flow-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET SECURITY CONTROL FLOW
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target security flow describes the content, scope, and authorization checks required before a protected component operation may be considered.
        </p>

        {/* FLOW CONTAINER */}
        <div className="border border-stone-200 rounded p-6 bg-stone-50/50 max-w-5xl space-y-6">
          <div className="font-mono text-[10px] font-bold text-stone-500 uppercase tracking-wider block border-b border-stone-200 pb-2">
            Target Security Control Flow
          </div>
          
          {/* Desktop horizontal flow */}
          <div className="hidden lg:flex items-center gap-1 font-mono text-[8px] font-bold text-stone-700">
            <div className="flex-1 border border-stone-300 bg-stone-100 rounded p-2 text-center shadow-sm uppercase text-stone-700">
              <span className="block text-[6px] text-stone-500">UNTRUSTED</span>
              Untrusted Input
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700">
              <span className="block text-[6px] text-stone-500">PROCESSING</span>
              Intake Boundary
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-700">
              <span className="block text-[6px] text-stone-500">PROCESSING</span>
              Scope & Content Filtering
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-amber-300 bg-amber-50/10 rounded p-2 text-center shadow-sm uppercase text-amber-900">
              <span className="block text-[6px] text-[#F2A93B]">WARN CHECK</span>
              Authorization Requirement Check
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-2 text-center shadow-sm uppercase text-[#556b03]">
              <span className="block text-[6px] text-[#A8CD16]">SIGNAL LIME</span>
              Permitted Bounded Op
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-white rounded p-2 text-center shadow-sm uppercase text-stone-600">
              <span className="block text-[6px] text-stone-400">PROCESSING</span>
              Result & Limitation Rec
            </div>
            <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
            
            <div className="flex-1 border border-stone-300 bg-stone-100 rounded p-2 text-center shadow-sm uppercase text-stone-500">
              <span className="block text-[6px] text-stone-400">NEXT STAGE</span>
              Protected Next-Stage Check
            </div>
          </div>

          {/* Mobile Flow Sequence */}
          <div className="lg:hidden space-y-2 font-mono text-[10px] font-bold">
            <div className="border border-stone-300 bg-stone-100 rounded p-2 text-center uppercase text-stone-700">
              <span className="block text-[8px] text-stone-500 font-sans">UNTRUSTED</span>
              Untrusted Input
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              <span className="block text-[8px] text-stone-500 font-sans">PROCESSING</span>
              Intake Boundary
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-700">
              <span className="block text-[8px] text-stone-500 font-sans">PROCESSING</span>
              Scope & Content Filtering
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-amber-300 bg-amber-50/10 rounded p-2 text-center uppercase text-amber-900">
              <span className="block text-[8px] text-[#F2A93B] font-sans">WARN CHECK</span>
              Authorization Requirement Check
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-[#A8CD16] bg-[#A8CD16]/10 rounded p-2 text-center uppercase text-[#556b03]">
              <span className="block text-[8px] text-[#A8CD16] font-sans">SIGNAL LIME</span>
              Permitted Bounded Operation
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-white rounded p-2 text-center uppercase text-stone-600">
              <span className="block text-[8px] text-stone-400 font-sans">PROCESSING</span>
              Result & Limitation Recording
            </div>
            <div className="text-center text-stone-400 text-xs" aria-hidden="true">&darr;</div>
            
            <div className="border border-stone-300 bg-stone-100 rounded p-2 text-center uppercase text-stone-500">
              <span className="block text-[8px] text-stone-400 font-sans">NEXT STAGE</span>
              Protected Next-Stage Check
            </div>
          </div>

          {/* SUPPORTING BOUNDARIES */}
          <div className="space-y-2 pt-4 border-t border-stone-200">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              Supporting Security Boundaries
            </span>
            <ul className="list-disc pl-5 text-stone-600 space-y-1 text-xs font-mono">
              <li>SERVER-SIDE CREDENTIAL BOUNDARY</li>
              <li>MODEL-CONTEXT BOUNDARY</li>
              <li>ISOLATED-EXECUTION BOUNDARY</li>
              <li>ARTIFACT AND LOG BOUNDARY</li>
              <li>WRITEBACK CONTENT BOUNDARY</li>
              <li>EXTERNAL DELIVERY BOUNDARY</li>
            </ul>
          </div>

          {/* BLOCKED PATHS */}
          <div className="space-y-3 pt-4 border-t border-stone-200">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
              Blocked Paths (Security Transitions Rejected)
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-[10px] font-bold">
              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>BROWSER CLIENT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>SERVER-SIDE CREDENTIALS</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>UNTRUSTED CONTENT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>CONTROL INSTRUCTIONS</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>MODEL OUTPUT</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>AUTHORIZATION</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>VALIDATION WORKER</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>UNRESTRICTED PRODUCTION MUTATION</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>PROHIBITED SECRET</span>
                  <span className="mx-2 text-stone-400" aria-hidden="true">&times;</span>
                  <span>ARTIFACT OR LOG PERSISTENCE</span>
                </div>
                <span className="bg-red-100 text-red-800 px-1.5 py-0.5 rounded text-[8px] uppercase font-black">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between border border-red-200 bg-red-50/30 rounded p-3 text-red-900">
                <div>
                  <span>STALE AUTHORIZATION</span>
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

      {/* TRUST ZONES */}
      <section className="space-y-4" aria-labelledby="trust-zones-heading">
        <h3 id="trust-zones-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TRUST ZONES
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target security contract describes seven conceptual trust zones with separated data, capability, and authority responsibilities.
        </p>

        <div className="space-y-6 max-w-5xl text-xs">
          {/* ZONE A */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase">
              A. BROWSER AND PUBLIC UI
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>display permitted review information</li>
                  <li>submit bounded user input</li>
                  <li>request server-side operations through configured interfaces when implementation exists</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must not:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>receive server-side credentials</li>
                  <li>determine authorization from client state</li>
                  <li>execute validators directly</li>
                  <li>perform destination writeback directly</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ZONE B */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              B. CHANGE INTAKE BOUNDARY
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>receive repository references</li>
                  <li>receive submitted SQL or schema-change references</li>
                  <li>normalize permitted change data</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>treat submitted content as untrusted</li>
                  <li>enforce configured scope</li>
                  <li>reject unsupported or prohibited input</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ZONE C */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              C. RIFTLESS CONTROL PLANE
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>coordinate configured integrations</li>
                  <li>evaluate operation prerequisites</li>
                  <li>enforce protected transition requirements</li>
                  <li>record target authorization and result references</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must not:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>treat model output as authorization</li>
                  <li>fabricate successful predecessor states</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ZONE D */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              D. MODEL REQUEST ZONE
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May receive:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>explicit requested task</li>
                  <li>redacted Context Pack</li>
                  <li>proposed change</li>
                  <li>configured policy constraints</li>
                  <li>permitted source references</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must not receive:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>credentials</li>
                  <li>raw authorization headers</li>
                  <li>internal authorization secrets</li>
                  <li>unrestricted repository exports</li>
                  <li>unrestricted logs</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ZONE E */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              E. ISOLATED EXECUTION ZONE
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May receive:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>authorized Validation Plan</li>
                  <li>bounded fixtures</li>
                  <li>configured validator requirements</li>
                  <li>permitted candidate references</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must not:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>perform unrestricted production writes</li>
                  <li>authorize itself</li>
                  <li>deploy changes</li>
                  <li>perform metadata writeback</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ZONE F */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              F. AUTHORIZED WRITEBACK ZONE
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>receive permitted record categories</li>
                  <li>apply configured destination mappings</li>
                  <li>record organizational review memory</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must not:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>operate without recorded authorization</li>
                  <li>present failure as success</li>
                  <li>expose prohibited values</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ZONE G */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-955 block uppercase">
              G. EXTERNAL DELIVERY ZONE
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-mono text-[9px] font-bold text-stone-500 uppercase block">May:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>independently authorize and execute deployment</li>
                </ul>
              </div>
              <div>
                <span className="font-mono text-[9px] font-bold text-red-500 uppercase block">Must remain:</span>
                <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                  <li>outside RIFTLESS production-deployment authority</li>
                  <li>responsible for its own credentials, environment controls, execution, and rollback</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* TRUST-ZONE TABLE */}
      <section className="space-y-4" aria-labelledby="trust-zone-table-heading">
        <h3 id="trust-zone-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TRUST ZONES MATRIX
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following table defines conceptual trust zones, permitted responsibilities, prohibited capabilities, and security requirements:
        </p>

        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-5xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="trust-zones-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual RIFTLESS trust zones and their security boundaries.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[20%]">Trust Zone</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Permitted Responsibility</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Prohibited Capability</th>
                <th scope="col" className="px-4 py-3 w-[30%]">Security Requirement</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">BROWSER AND PUBLIC UI</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Display permitted information and submit bounded requests.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Server-side credentials or direct protected operations.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Client state must not be the authorization source of truth.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CHANGE INTAKE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Normalize configured input scope.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Treat repository or submitted content as trusted instructions.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Input filtering and explicit non-success handling.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTROL PLANE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Coordinate configured policy and protected transitions.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Fabricate predecessor success or delegate authority to a model.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Authorization and result state remain separately recorded.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">MODEL REQUEST ZONE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Receive bounded advisory context.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Credentials, unrestricted content, and state-transition authority.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Allowlist, redaction, and explicit task separation.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ISOLATED EXECUTION</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Execute configured validators against bounded inputs.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Production mutation, deployment, writeback, and self-authorization.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Operation and credential scope remain restricted.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">AUTHORIZED WRITEBACK</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Submit authorized organizational metadata records.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Unauthorized mutation or secret-bearing content.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configured mappings, redaction, and recorded authorization.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">EXTERNAL DELIVERY</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Apply independently controlled deployment authorization and execution.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Reuse RIFTLESS review state as unrestricted deployment credentials.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Deployment authority remains external.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* AUTHENTICATION AND AUTHORIZATION */}
      <section className="space-y-4" aria-labelledby="auth-boundary-heading">
        <h3 id="auth-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          AUTHENTICATION AND AUTHORIZATION
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target security contract distinguishes identity, capability availability, operation-specific authorization, and resulting operation outcomes.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              IDENTITY OR AUTHENTICATION
            </span>
            <span className="text-[9px] font-mono text-stone-400 block -mt-1">PURPOSE</span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Establish who or what is requesting an operation after implementation defines the identity mechanism.
            </p>
            <p className="font-semibold text-red-500 font-mono text-[9px] uppercase mt-2">MUST NOT IMPLY:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>identity provider is already selected</li>
              <li>login protocol is already available</li>
              <li>authentication alone authorizes an operation</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              CAPABILITY AVAILABILITY
            </span>
            <span className="text-[9px] font-mono text-stone-400 block -mt-1">PURPOSE</span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Indicate that an integration, validator, destination, or external system may be reachable.
            </p>
            <p className="font-semibold text-red-500 font-mono text-[9px] uppercase mt-2">MUST NOT IMPLY:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>current operation is permitted</li>
              <li>credentials may be reused for another capability</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              OPERATION AUTHORIZATION
            </span>
            <span className="text-[9px] font-mono text-stone-400 block -mt-1">PURPOSE</span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Record permission for a specific protected operation and evaluated scope.
            </p>
            <p className="font-semibold text-stone-500 font-mono text-[9px] uppercase mt-2">MUST IDENTIFY WHEN RELEVANT:</p>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>operation category</li>
              <li>candidate or revision reference</li>
              <li>required predecessor references</li>
              <li>permitted scope and limitations</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              OPERATION RESULT
            </span>
            <span className="text-[9px] font-mono text-stone-400 block -mt-1">PURPOSE</span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Record whether the authorized operation completed, partially completed, failed, was rejected, or remained unavailable.
            </p>
          </div>
        </div>

        {/* STATIC STATEMENT */}
        <div className="p-4 border border-stone-300 bg-stone-50 rounded max-w-2xl">
          <div className="font-mono text-xs font-bold text-stone-900 text-center uppercase tracking-wide leading-relaxed">
            AUTHENTICATED &ne; CAPABILITY AVAILABLE &ne; OPERATION AUTHORIZED &ne; OPERATION COMPLETED &ne; OPERATION SUCCESSFUL
          </div>
        </div>

        <p className="text-sm text-stone-600 leading-relaxed max-w-4xl">
          Each transition point requires verifying that predecessor results have been explicitly preserved, configured constraints are satisfied, and active policy supports proceeding. Human acknowledgment is not a universal authorization token, model output cannot authenticate or authorize, a previous authorization may not apply after scope changes, and destination acceptance does not create retroactive authorization.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* CREDENTIAL AND SECRET BOUNDARY */}
      <section className="space-y-4" aria-labelledby="secret-boundary-heading">
        <h3 id="secret-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          CREDENTIAL AND SECRET BOUNDARY
        </h3>
        
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target credential contract requires credential values to remain outside untrusted, browser-visible, model, artifact, writeback, and handoff boundaries.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase text-amber-800">
              MUST REMAIN SERVER-SIDE
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>DataHub credentials</li>
              <li>GitHub credentials</li>
              <li>DeepSeek credentials</li>
              <li>artifact-storage credentials</li>
              <li>external-delivery credentials</li>
              <li>access tokens</li>
              <li>private keys</li>
              <li>raw authorization headers</li>
              <li>webhook secrets</li>
              <li>secret environment values</li>
              <li>credential-bearing connection strings</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-800 block uppercase">
              MUST NOT ENTER
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>browser-visible configuration</li>
              <li>model context</li>
              <li>repository comments</li>
              <li>ordinary artifacts</li>
              <li>validation summaries</li>
              <li>Writeback Records</li>
              <li>Release Handoff Packages</li>
              <li>public documentation examples</li>
              <li>error messages exposed to users</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase">
              MAY BE REFERENCED CONCEPTUALLY
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>configured server-side connection reference</li>
              <li>credential availability status</li>
              <li>secret-resolution failure category</li>
              <li>permitted capability reference</li>
            </ul>
          </div>
        </div>

        <Callout type="warning" title="CREDENTIAL ISOLATION WARNING">
          A connection reference is not a credential value and must not resolve into a secret inside browser-visible content, model requests, logs, artifacts, or metadata writeback.
        </Callout>

        <Callout type="note">
          The final secret storage, rotation, revocation, and access-audit mechanism remains undefined. No specific secret manager solution is mandated or configured within this tier.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* UNTRUSTED CONTENT */}
      <section className="space-y-4" aria-labelledby="untrusted-content-heading">
        <h3 id="untrusted-content-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          UNTRUSTED CONTENT
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target security contract requires repository content, metadata, comments, logs, and external responses to be treated as untrusted data rather than control-plane instructions.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TREAT AS UNTRUSTED DATA
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>repository files</li>
              <li>SQL comments</li>
              <li>dbt model comments</li>
              <li>pull-request descriptions</li>
              <li>metadata descriptions</li>
              <li>asset documentation</li>
              <li>ownership text</li>
              <li>query text</li>
              <li>validator output</li>
              <li>error messages</li>
              <li>previous model responses</li>
              <li>external-delivery responses</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TARGET PROCESSING RULES
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>content must not override configured policy</li>
              <li>content must not expand tool or data access</li>
              <li>content must not become system instructions</li>
              <li>content must not authorize another operation</li>
              <li>content must remain distinguishable from control-plane instructions</li>
              <li>model response must remain advisory</li>
              <li>executable proposals require deterministic review and validation</li>
              <li>unsupported references must not become evidence</li>
            </ul>
          </div>
        </div>

        <Callout type="warning" title="INSTRUCTION PROTECTION WARNING">
          Instructions embedded in source files, metadata, logs, or retrieved content must not be interpreted as RIFTLESS authorization.
        </Callout>

        <Callout type="note">
          These requirements describe target prompt-injection and untrusted-content boundaries. Do not claim a complete prompt-injection defense has been implemented.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* MODEL SECURITY BOUNDARY */}
      <section className="space-y-4" aria-labelledby="model-security-heading">
        <h3 id="model-security-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          MODEL SECURITY BOUNDARY
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target model boundary separates DeepSeek advisory output from deterministic policy, authorization, validation evidence, writeback, and deployment responsibilities.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              DEEPSEEK MAY
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>explain changes</li>
              <li>propose remediation</li>
              <li>summarize supplied evidence</li>
              <li>expose assumptions</li>
              <li>suggest validation ideas</li>
              <li>explain failures</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">
              DEEPSEEK MUST NOT
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>assign or clear ALLOW, WARN, or BLOCK</li>
              <li>create authorization</li>
              <li>execute validators</li>
              <li>access credentials</li>
              <li>mutate GitHub</li>
              <li>mutate DataHub</li>
              <li>perform deployment</li>
              <li>present unsupported claims as evidence</li>
              <li>provide human acknowledgment</li>
              <li>select recovery authorization</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TARGET REQUEST CONTROLS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>explicit task definition</li>
              <li>bounded request context</li>
              <li>allowlisted fields only</li>
              <li>configured redaction requirements applied or checked before request submission</li>
              <li>source references when available</li>
              <li>request size checked against configured limits</li>
              <li>strict separation between instructions and untrusted data</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              TARGET RESPONSE CONTROLS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>required response-shape checks</li>
              <li>assumptions remain explicit</li>
              <li>unsupported claims remain non-evidence</li>
              <li>malformed output is rejected</li>
              <li>response status is recorded separately from run authorization</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* REPOSITORY AND METADATA SECURITY */}
      <section className="space-y-4" aria-labelledby="repo-metadata-heading">
        <h3 id="repo-metadata-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          REPOSITORY AND METADATA SECURITY
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REPOSITORY BOUNDARY
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>process only configured repositories and scope</li>
              <li>record evaluated base and head references when applicable</li>
              <li>avoid unrestricted repository exports</li>
              <li>exclude secret-bearing files</li>
              <li>prevent stale revisions from inheriting current status</li>
              <li>treat diff content as insufficient for downstream-impact proof by itself</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              METADATA BOUNDARY
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>request only configured metadata categories</li>
              <li>select relevant assets and relationships</li>
              <li>exclude unrelated personal or sensitive metadata</li>
              <li>preserve source references where available</li>
              <li>apply allowlist and redaction before model context or writeback</li>
              <li>metadata availability does not authorize a protected operation</li>
            </ul>
          </div>
        </div>

        <p className="text-sm text-stone-600 leading-relaxed max-w-4xl">
          Repository access, metadata access, model access, validation execution, and writeback access should remain independently configurable. Availability or authorization in one zone must not grant capability in another zone.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* VALIDATION EXECUTION SECURITY */}
      <section className="space-y-4" aria-labelledby="validation-security-heading">
        <h3 id="validation-security-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          VALIDATION EXECUTION SECURITY
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-[#556b03] block uppercase">
              MAY RECEIVE WHEN AUTHORIZED
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>candidate reference</li>
              <li>Validation Plan</li>
              <li>selected validator configuration</li>
              <li>bounded fixtures</li>
              <li>permitted dbt project references</li>
              <li>expected-result references</li>
              <li>artifact destination references</li>
              <li>redaction requirements</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">
              MUST NOT RECEIVE OR PERFORM
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>unrestricted production-write credentials</li>
              <li>direct production mutations</li>
              <li>deployment operations</li>
              <li>metadata writeback</li>
              <li>self-authorization</li>
              <li>unrestricted repository content</li>
              <li>unrestricted production exports</li>
              <li>browser credentials</li>
              <li>unrelated secrets</li>
            </ul>
          </div>
        </div>

        <div className="space-y-2 max-w-3xl text-xs text-stone-600">
          <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">TARGET WORKER REQUIREMENTS</span>
          <p className="leading-relaxed">
            Candidate and revision must remain identifiable, required validators remain explicit, commands or operations remain bounded, result and storage success remain separate, validator output passes content filtering before persistence, and worker availability does not imply authorization.
          </p>
        </div>

        <Callout type="note">
          The final process, container, network, filesystem, and resource-isolation mechanisms remain undefined until implementation.
        </Callout>
      </section>

      <hr className="border-stone-200/50" />

      {/* ARTIFACT AND LOG SECURITY */}
      <section className="space-y-4" aria-labelledby="artifact-security-heading">
        <h3 id="artifact-security-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          ARTIFACT AND LOG SECURITY
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase text-amber-800">
              MAY BE PRESERVED WHEN PERMITTED
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>artifact type and reference</li>
              <li>run reference</li>
              <li>source references</li>
              <li>evaluated scope</li>
              <li>decision reasons</li>
              <li>validator outcomes</li>
              <li>tested scope</li>
              <li>failure category</li>
              <li>permitted diagnostics</li>
              <li>limitations</li>
              <li>predecessor and successor references</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-stone-50 space-y-2">
            <span className="font-mono text-[10px] font-bold text-red-900 block uppercase">
              MUST BE EXCLUDED
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px] font-mono">
              <li>credentials</li>
              <li>access tokens</li>
              <li>private keys</li>
              <li>raw authorization headers</li>
              <li>secret environment values</li>
              <li>unrestricted repository exports</li>
              <li>unrestricted metadata exports</li>
              <li>unrestricted validation logs</li>
              <li>unrelated sensitive data</li>
              <li>hidden model reasoning</li>
              <li>fabricated success states</li>
            </ul>
          </div>
        </div>

        <div className="space-y-2 max-w-3xl text-xs text-stone-600">
          <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">SECURITY REQUIREMENTS</span>
          <p className="leading-relaxed">
            Diagnostic content must be filtered before persistence, redacted values must not be copied into failure reasons, artifact links must not embed secrets, storage success remains distinct from stage success, public or browser-visible artifacts must contain only permitted content, and retention rules must remain configured and referenceable.
          </p>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* WRITEBACK AND HANDOFF SECURITY */}
      <section className="space-y-4" aria-labelledby="writeback-handoff-security-heading">
        <h3 id="writeback-handoff-security-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          WRITEBACK AND HANDOFF SECURITY
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              WRITEBACK REQUIREMENTS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>recorded authorization is required</li>
              <li>permitted record categories remain explicit</li>
              <li>destination mappings remain configured</li>
              <li>prohibited values remain excluded</li>
              <li>decision status and destination outcome remain distinct</li>
              <li>BLOCK or failure may be preserved but never represented as approval</li>
              <li>destination completion does not imply deployment authorization</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              HANDOFF REQUIREMENTS
            </span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>Release Handoff Package contains only permitted references and scope information</li>
              <li>production credentials remain external</li>
              <li>direct deployment commands remain excluded</li>
              <li>handoff eligibility remains distinct from deployment authorization</li>
              <li>external deployment outcome is not inferred</li>
              <li>stale handoff packages do not remain current</li>
            </ul>
          </div>
        </div>

        <div className="p-4 border border-stone-300 bg-stone-50 rounded max-w-2xl">
          <div className="font-mono text-xs font-bold text-stone-900 text-center uppercase tracking-wide leading-relaxed">
            Organizational-memory persistence and external deployment execution are separate security domains with separate authorization requirements.
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* REDACTION AND ALLOWLIST */}
      <section className="space-y-4" aria-labelledby="redaction-allowlist-heading">
        <h3 id="redaction-allowlist-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          REDACTION AND ALLOWLIST
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl text-xs">
          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              ALLOWLIST PURPOSE
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Identify the categories and fields permitted to enter:
            </p>
            <ul className="list-disc pl-4 text-stone-600 space-y-0.5 text-[11px] font-mono">
              <li>Context Pack</li>
              <li>model request</li>
              <li>validator input</li>
              <li>artifact content</li>
              <li>writeback content</li>
              <li>handoff package</li>
            </ul>
          </div>

          <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
              REDACTION PURPOSE
            </span>
            <p className="text-stone-600 text-[11px] leading-relaxed">
              Remove, replace, or reject prohibited values before a target boundary is crossed.
            </p>
          </div>
        </div>

        <div className="space-y-3 max-w-5xl text-xs">
          <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">TARGET HANDLING RESULTS</span>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div className="border border-stone-200 rounded p-3 bg-white space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-900 block uppercase">PERMITTED</span>
              <p className="text-stone-600 leading-relaxed text-[11px]">Content may proceed within its configured scope.</p>
            </div>
            <div className="border border-stone-200 rounded p-3 bg-white space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-900 block uppercase">REDACTED</span>
              <p className="text-stone-600 leading-relaxed text-[11px]">Prohibited value is removed or replaced without exposing the original value.</p>
            </div>
            <div className="border border-stone-200 rounded p-3 bg-white space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-900 block uppercase">REJECTED</span>
              <p className="text-stone-600 leading-relaxed text-[11px]">Processing does not proceed because the content cannot be safely bounded.</p>
            </div>
            <div className="border border-stone-200 rounded p-3 bg-white space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-900 block uppercase">REVIEW REQUIRED</span>
              <p className="text-stone-600 leading-relaxed text-[11px]">A human or policy-defined decision is required because automatic handling is insufficient.</p>
            </div>
            <div className="border border-stone-200 rounded p-3 bg-white space-y-1">
              <span className="font-mono text-[9px] font-bold text-stone-900 block uppercase">CONTROL UNAVAILABLE</span>
              <p className="text-stone-600 leading-relaxed text-[11px]">The required filtering or redaction control could not complete.</p>
            </div>
          </div>
        </div>

        <p className="text-sm text-stone-600 leading-relaxed max-w-4xl">
          These are conceptual handling results, not official enums or proof of a runtime redaction engine. Redaction failure must not silently permit content, required context removed by redaction remains an explicit limitation, redacted values must not remain available in ordinary error output, allowlist availability does not authorize an operation, and model output does not bypass redaction.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* SECURITY CONTROL TABLE */}
      <section className="space-y-4" aria-labelledby="security-control-heading">
        <h3 id="security-control-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          SECURITY CONTROLS
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following table outlines conceptual security controls applied across RIFTLESS target boundaries:
        </p>

        <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-5xl">
          <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="security-controls-table">
            <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
              Conceptual security controls applied across RIFTLESS target boundaries.
            </caption>
            <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[20%]">Control Area</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[25%]">Protected Boundary</th>
                <th scope="col" className="px-4 py-3 border-r border-stone-200 w-[30%]">Required Behavior</th>
                <th scope="col" className="px-4 py-3 w-[25%]">Must Not Imply</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 bg-white">
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">INPUT SCOPE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Repository and submitted change intake.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Process only configured and relevant input scope.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Input content is trusted.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">MODEL CONTEXT</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">DeepSeek request assembly.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Allowlisted, redacted, bounded context only.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Model output is authorized.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">EXECUTION SCOPE</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Validation worker.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Bounded inputs and permitted validator operations.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Worker may mutate production.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACT CONTENT</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Evidence and failure records.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Permitted references and filtered diagnostics.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Artifact storage proves stage success.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITEBACK CONTENT</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Organizational metadata destination.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Authorized categories and configured mappings.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Persistence equals approval.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">HANDOFF CONTENT</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">External delivery handoff.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Scope-bound references without deployment secrets.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Deployment occurred.</td>
              </tr>
              <tr>
                <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">AUTHORIZATION</th>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Protected stage transitions.</td>
                <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Operation-specific and predecessor-aware authorization.</td>
                <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Authentication or availability alone is sufficient.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* TARGET OPERATION SHAPES */}
      <section className="space-y-4" aria-labelledby="operation-shapes-heading">
        <h3 id="operation-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          TARGET OPERATION SHAPES
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The following conceptual definitions outline the target interface boundaries for security validation, authorization checks, and security result recording:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-5xl text-xs">
          {/* Block 1 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL CONTENT BOUNDARY CHECK
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive target boundary category
receive candidate content references
receive configured allowlist and redaction references
identify prohibited value categories
record permitted, redacted, rejected, or unavailable result
return target content-boundary result`}
            </pre>
          </div>

          {/* Block 2 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL OPERATION AUTHORIZATION CHECK
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive requested protected operation
receive candidate and scope references
receive required predecessor artifact references
receive applicable policy requirements
check authorization applicability
record permitted, rejected, review-required, or unavailable result
return target authorization-check result`}
            </pre>
          </div>

          {/* Block 3 */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
              CONCEPTUAL SECURITY RESULT RECORDING
            </span>
            <span className="text-[8px] font-mono text-stone-400 block -mt-1">NON-EXECUTABLE TARGET INTERFACE</span>
            <pre className="bg-stone-50 border border-stone-200 p-3 rounded text-[11px] font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive security-control outcome
exclude prohibited values
record affected boundary and scope
record limitations and failure reason
associate permitted predecessor references
return target security-result reference`}
            </pre>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
          Exact identity APIs, access-control formats, secret-resolution calls, encryption mechanisms, network controls, redaction implementations, and audit-event schemas will be documented only after repository-backed security controls are implemented and versioned.
        </p>
      </section>

      <hr className="border-stone-200/50" />

      {/* SECURITY FAILURE BEHAVIOR */}
      <section className="space-y-4" aria-labelledby="security-failure-behavior-heading">
        <h3 id="security-failure-behavior-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          SECURITY FAILURE BEHAVIOR
        </h3>
        <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
          The target security contract defines non-success behavior when identity, authorization, filtering, execution, artifact, writeback, or handoff controls cannot complete.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl text-xs">
          {/* AUTHENTICATION OR IDENTITY UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHENTICATION OR IDENTITY UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>protected operation must not infer authorization</li>
              <li>identity failure remains visible</li>
            </ul>
          </div>

          {/* AUTHORIZATION MISSING OR INVALID */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHORIZATION MISSING OR INVALID</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>protected operation must not begin</li>
              <li>capability availability must not bypass authorization</li>
            </ul>
          </div>

          {/* SCOPE MISMATCH */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">SCOPE MISMATCH</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>current operation must not use authorization from another candidate, revision, destination, or scope</li>
              <li>new authorization may be required</li>
            </ul>
          </div>

          {/* REDACTION OR ALLOWLIST FAILURE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REDACTION OR ALLOWLIST FAILURE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>prohibited content must not cross the target boundary</li>
              <li>missing required context remains visible</li>
            </ul>
          </div>

          {/* SECRET DETECTED IN OUTPUT */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">SECRET DETECTED IN OUTPUT</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>output must not be persisted, exposed, or submitted with the prohibited value</li>
              <li>failure reason must not reproduce the secret</li>
            </ul>
          </div>

          {/* UNTRUSTED CONTENT ATTEMPTS CONTROL OVERRIDE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">UNTRUSTED CONTENT ATTEMPTS CONTROL OVERRIDE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>embedded instruction remains data</li>
              <li>configured control-plane policy remains authoritative</li>
            </ul>
          </div>

          {/* VALIDATION EXECUTION BOUNDARY UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION EXECUTION BOUNDARY UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>validation must not be reported as safely executed</li>
              <li>successful evidence must not be inferred</li>
            </ul>
          </div>

          {/* ARTIFACT OR LOG FILTERING UNAVAILABLE */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ARTIFACT OR LOG FILTERING UNAVAILABLE</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>affected content must not be reported as safely persisted</li>
              <li>stage outcome and storage outcome remain distinct</li>
            </ul>
          </div>

          {/* WRITEBACK SECURITY CHECK FAILED */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">WRITEBACK SECURITY CHECK FAILED</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>metadata operation must not proceed</li>
              <li>non-success reason may be preserved without exposing prohibited content</li>
            </ul>
          </div>

          {/* HANDOFF SECURITY CHECK FAILED */}
          <div className="border border-stone-200 rounded p-4 bg-white space-y-1 md:col-span-2 lg:col-span-1">
            <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">HANDOFF SECURITY CHECK FAILED</span>
            <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
              <li>Release Handoff Package must not be prepared or exposed with prohibited content</li>
              <li>deployment status must not be fabricated</li>
            </ul>
          </div>
        </div>
      </section>

      <hr className="border-stone-200/50" />

      {/* SECURITY INVARIANTS */}
      <section className="space-y-4" aria-labelledby="security-invariants-heading">
        <h3 id="security-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
          SECURITY INVARIANTS
        </h3>
        
        <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-4xl space-y-3 font-mono text-xs">
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">UNTRUSTED CONTENT REMAINS DATA.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN SERVER-SIDE.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">CLIENT STATE REMAINS NON-AUTHORIZING.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS ADVISORY.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">AUTHORIZATION REMAINS OPERATION-SPECIFIC.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">CAPABILITY AVAILABILITY REMAINS DISTINCT FROM AUTHORIZATION.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">EXECUTION REMAINS BOUNDED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">PRODUCTION MUTATION REMAINS OUTSIDE VALIDATION.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">ARTIFACTS REMAIN FILTERED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK REMAINS SEPARATELY AUTHORIZED.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">HANDOFF REMAINS DISTINCT FROM DEPLOYMENT.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">STALE AUTHORIZATION DOES NOT BECOME CURRENT.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">NON-SUCCESS DOES NOT BECOME SUCCESS.</div>
          </div>
          <div className="h-px bg-stone-200" />
          <div className="space-y-1">
            <div className="font-bold text-[var(--color-riftless-ink)]">SECURITY-CONTROL SUCCESS REMAINS EXPLICIT.</div>
          </div>
        </div>

        <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-4xl">
          These statements describe target security requirements, not proof that authentication, authorization, secret management, runtime isolation, encryption, network policy, redaction, security monitoring, or incident response has already been implemented.
        </p>
      </section>
    </section>
  );
}
