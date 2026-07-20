/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect, ReactNode } from 'react';
import { DeploymentHandoffSection } from '../components/DeploymentHandoffSection';
import { FailureRecoverySection } from '../components/FailureRecoverySection';
import { SecuritySection } from '../components/SecuritySection';
import { ObservabilitySection } from '../components/ObservabilitySection';
import { ApiReferenceSection } from '../components/ApiReferenceSection';

interface NavigationGroup {
  title: string;
  items: string[];
}

const GROUPS: NavigationGroup[] = [
  {
    title: 'GETTING STARTED',
    items: ['Introduction', 'Core Concepts', 'Quickstart']
  },
  {
    title: 'ARCHITECTURE',
    items: ['System Overview', 'Trust Boundaries', 'Run Lifecycle']
  },
  {
    title: 'INTEGRATIONS',
    items: ['DataHub', 'GitHub', 'DeepSeek']
  },
  {
    title: 'REFERENCE',
    items: ['Configuration', 'Artifact Contracts', 'Risk Decisions', 'Validation', 'Writeback', 'Deployment Handoff', 'API Reference']
  },
  {
    title: 'OPERATIONS',
    items: ['Failure Recovery', 'Security', 'Observability']
  }
];

const itemToHash = (item: string) => {
  if (item === 'Deployment Handoff') return '#deployment';
  return `#${item.toLowerCase().replace(/\s+/g, '-')}`;
};

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

export function DocsPage() {
  const [activeSection, setActiveSection] = useState('Introduction');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSectionClick = (item: string) => {
    const hash = itemToHash(item);
    window.location.hash = hash;
    setActiveSection(item);
    setMobileMenuOpen(false);
  };

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (!hash) {
        setActiveSection('Introduction');
        return;
      }
      for (const group of GROUPS) {
        const matched = group.items.find(item => itemToHash(item) === hash);
        if (matched) {
          setActiveSection(matched);
          return;
        }
      }
    };

    handleHashChange();

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [activeSection]);

  return (
    <div className="flex-grow w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 flex flex-col">
      
      {/* A. Docs top header */}
      <header className="border-b border-stone-200 pb-8 mb-8 space-y-4">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase">
            RIFTLESS DOCUMENTATION
          </span>
          <span className="h-1.5 w-1.5 rounded-full bg-[#A8CD16]" />
          <span className="text-[9px] font-mono tracking-wider bg-stone-100 border border-stone-200/80 px-1.5 py-0.5 text-[var(--color-riftless-ink)] uppercase font-semibold">
            TARGET IMPLEMENTATION DOCUMENTATION
          </span>
        </div>
        
        <h1 className="text-3xl sm:text-4xl font-display font-extrabold tracking-tight text-[var(--color-riftless-ink)] leading-none uppercase">
          BUILD WITH CONTEXT.<br className="hidden sm:inline" />
          OPERATE WITH EVIDENCE.
        </h1>
        
        <p className="text-sm sm:text-base text-[var(--color-riftless-graph-gray)] max-w-2xl leading-relaxed">
          Technical documentation for integrating, configuring, and operating the RIFTLESS data change guardian.
        </p>
      </header>

      {/* B & C. Navigation + Content Layout */}
      <div className="lg:grid lg:grid-cols-12 lg:gap-10 items-start flex-grow">
        
        {/* Mobile Navigation Trigger (only visible on mobile) */}
        <div className="lg:hidden mb-6">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav-panel"
            className="w-full flex items-center justify-between px-4 py-3 bg-stone-100 border border-stone-200 text-xs font-mono text-[var(--color-riftless-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--color-riftless-ink)] transition-colors duration-150 rounded"
          >
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[var(--color-riftless-graph-gray)] uppercase">MENU:</span>
              <span className="font-bold uppercase tracking-tight">{activeSection}</span>
            </div>
            <svg className={`w-4 h-4 transition-transform duration-150 ${mobileMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {/* Mobile Menu Dropdown Panel */}
          {mobileMenuOpen && (
            <nav id="mobile-nav-panel" className="mt-1 bg-stone-50 border border-stone-200 rounded p-4 space-y-4 max-h-[60vh] overflow-y-auto shadow-sm" aria-label="Mobile Documentation Navigation">
              {GROUPS.map(group => (
                <div key={group.title} className="space-y-1">
                  <span className="text-[9px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-bold block pt-1 border-b border-stone-200/40 pb-0.5">
                    {group.title}
                  </span>
                  <div className="space-y-0.5 pt-1 pl-1">
                    {group.items.map(item => {
                      const isSelected = activeSection === item;
                      return (
                        <button
                          key={item}
                          onClick={() => handleSectionClick(item)}
                          aria-current={isSelected ? 'location' : undefined}
                          className={`w-full text-left text-xs py-1.5 px-2 transition-colors duration-150 rounded ${
                            isSelected
                              ? 'bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] font-medium'
                              : 'text-stone-600 hover:text-[var(--color-riftless-ink)] hover:bg-stone-100'
                          }`}
                        >
                          {item}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </nav>
          )}
        </div>

        {/* Desktop Sidebar (visible on large screen) */}
        <aside className="hidden lg:block lg:col-span-3 lg:sticky lg:top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pr-6 border-r border-stone-200/50" aria-label="Documentation Navigation">
          <nav className="space-y-6">
            {GROUPS.map(group => (
              <div key={group.title} className="space-y-2">
                <h3 className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
                  {group.title}
                </h3>
                <ul className="space-y-1">
                  {group.items.map(item => {
                    const isSelected = activeSection === item;
                    return (
                      <li key={item}>
                        <button
                          onClick={() => handleSectionClick(item)}
                          aria-current={isSelected ? 'location' : undefined}
                          className={`w-full text-left text-xs py-1.5 px-2.5 transition-colors duration-150 rounded border ${
                            isSelected
                              ? 'bg-[var(--color-riftless-ink)] border-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] font-medium'
                              : 'border-transparent text-stone-600 hover:text-[var(--color-riftless-ink)] hover:bg-stone-100/50'
                          } focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-riftless-ink)]`}
                        >
                          {item}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        </aside>

        {/* C. Content Canvas Area */}
        <main className="lg:col-span-9 max-w-[72ch] w-full" aria-label="Documentation Content">
          {activeSection === 'Introduction' ? (
            <article className="space-y-8">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Introduction
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  RIFTLESS reviews proposed data changes before they create downstream fallout.
                </p>
              </div>

              {/* Callout Target */}
              <Callout type="target">
                This documentation describes the target implementation model unless a capability is explicitly marked as available.
              </Callout>

              <hr className="border-stone-200" />

              {/* Subsection: WHAT RIFTLESS DOES */}
              <section className="space-y-4">
                <h3 className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  What RIFTLESS Does
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The core objective of the guardian is to prevent downstream database drift and pipeline breakages through context-aware static analysis.
                </p>
                <ul className="list-disc pl-5 space-y-3 text-sm text-[var(--color-riftless-ink)] leading-relaxed">
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">Assembles DataHub context:</strong> Map current live schema metadata, lineage associations, and downstream dependencies.
                  </li>
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">Evaluates deterministic risk:</strong> Test changes against precise, version-controlled contract files.
                  </li>
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">Proposes compatible remediation:</strong> Offer alternative structural path suggestions if validation tests fail.
                  </li>
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">Validates executable evidence:</strong> Ensure verification scripts prove system invariant integrity.
                  </li>
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">Writes the decision back:</strong> Persist and register signed change status manifests.
                  </li>
                </ul>
              </section>

              {/* Callout Note */}
              <Callout type="note">
                For more detailed specifications about our testing rules, see the <code className="px-1.5 py-0.5 bg-stone-100 border border-stone-200 rounded font-mono text-xs text-[var(--color-riftless-ink)]">Validation</code> section in the reference guides.
              </Callout>

              <hr className="border-stone-200" />

              {/* Subsection: WHAT RIFTLESS DOES NOT DO */}
              <section className="space-y-4">
                <h3 className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  What RIFTLESS Does Not Do
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  RIFTLESS is explicitly built as a deterministic guardrail, enforcing strict validation boundaries. It maintains the following non-goals:
                </p>
                <ul className="list-decimal pl-5 space-y-3 text-sm text-[var(--color-riftless-ink)] leading-relaxed">
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">AI does not authorize production changes:</strong> Model pipelines solely propose resolutions; rule-based checkers maintain absolute veto power.
                  </li>
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">Model output is not treated as evidence:</strong> Verification must always be verified programmatically through executable tests.
                  </li>
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">Validation cannot be bypassed:</strong> Decoupled systems do not allow emergency overrides without cryptographically signed overrides.
                  </li>
                  <li>
                    <strong className="font-semibold text-[var(--color-riftless-ink)]">Secrets are never sent as model context:</strong> Secure metadata filters sanitize credentials and inline variables before processing.
                  </li>
                </ul>
              </section>

              {/* Callout Warning */}
              <Callout type="warning">
                Emergency keys must be locked down in external secure key storage (Vault/KMS). Never bypass standard pull-request checks in production.
              </Callout>

              <hr className="border-stone-200" />

              {/* Subsection: CORE OPERATING PRINCIPLE */}
              <section className="space-y-4">
                <h3 className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Core Operating Principle
                </h3>
                
                {/* Blockquote principle */}
                <div className="border-l-4 border-[var(--color-riftless-ink)] bg-stone-100 p-6 rounded-r">
                  <p className="font-mono text-sm sm:text-base font-bold tracking-tight text-[var(--color-riftless-ink)] uppercase leading-relaxed">
                    DEEPSEEK PROPOSES.<br />
                    DETERMINISTIC RULES AUTHORIZE.<br />
                    EXECUTABLE TESTS PROVE.
                  </p>
                </div>
              </section>

              <hr className="border-stone-200" />

              {/* Table and Code specifications showcase */}
              <section className="space-y-6 pb-6">
                <h3 className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Reference Foundations
                </h3>
                
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  To illustrate documentation styling, here are native foundations for technical specifications, configurations, and tables.
                </p>

                {/* Code Block */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between px-4 py-2 bg-stone-800 text-stone-300 text-[10px] font-mono rounded-t border-b border-stone-700">
                    <span>riftless.config.yaml</span>
                    <span className="text-[#A8CD16]">YAML</span>
                  </div>
                  <pre className="p-4 bg-stone-900 rounded-b text-stone-100 font-mono text-xs overflow-x-auto leading-relaxed">
{`version: "1.0"
metadata:
  app: "riftless-guardian"
  capabilities: ["MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API"]

integrity_checks:
  datahub_connection: true
  rules:
    - name: "no-breaking-column-removals"
      severity: "critical"
    - name: "require-evidence-tests"
      severity: "warning"

secrets_redaction:
  enabled: true
  patterns:
    - "api_key"
    - "token"
    - "password"`}
                  </pre>
                </div>

                {/* Table */}
                <div className="overflow-x-auto border border-stone-200 rounded">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="integrity-checks-table">
                    <thead className="bg-stone-50">
                      <tr>
                        <th className="px-4 py-3 font-semibold uppercase text-stone-700">Integrity Check</th>
                        <th className="px-4 py-3 font-semibold uppercase text-stone-700">Severity</th>
                        <th className="px-4 py-3 font-semibold uppercase text-stone-700">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <td className="px-4 py-3 font-sans font-medium text-stone-900">datahub_connection</td>
                        <td className="px-4 py-3 text-red-600 font-semibold">Critical</td>
                        <td className="px-4 py-3 text-emerald-600 font-medium">Active</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-sans font-medium text-stone-900">no-breaking-column-removals</td>
                        <td className="px-4 py-3 text-red-600 font-semibold">Critical</td>
                        <td className="px-4 py-3 text-emerald-600 font-medium">Active</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-sans font-medium text-stone-900">require-evidence-tests</td>
                        <td className="px-4 py-3 text-amber-600 font-semibold">Warning</td>
                        <td className="px-4 py-3 text-emerald-600 font-medium">Active</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </article>
          ) : activeSection === 'Core Concepts' ? (
            <article id="core-concepts" aria-labelledby="core-concepts-heading" className="space-y-8 animate-none">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="core-concepts-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Core Concepts
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  RIFTLESS turns every proposed data change into a governed review run with explicit inputs, decisions, evidence, and organizational memory.
                </p>
              </div>

              {/* Lifecycle contract chain */}
              <div className="space-y-3 my-8">
                <div className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  TARGET REVIEW CONTRACT CHAIN
                </div>
                <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-3 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[10px]">
                  {/* CHANGE REQUEST */}
                  <div className="flex-1 p-2.5 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    CHANGE REQUEST
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  {/* CONTEXT PACK */}
                  <div className="flex-1 p-2.5 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    CONTEXT PACK
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  {/* RISK DECISION */}
                  <div className="flex-1 p-2.5 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    RISK DECISION
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  {/* REMEDIATION PLAN */}
                  <div className="flex-1 p-2.5 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    REMEDIATION PLAN
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  {/* VALIDATION BUNDLE */}
                  <div className="flex-1 p-2.5 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    VALIDATION BUNDLE
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  {/* WRITEBACK RECORD */}
                  <div className="flex-1 p-2.5 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    WRITEBACK RECORD
                  </div>
                </div>
              </div>

              <hr className="border-stone-200" />

              {/* Six Core Concepts */}
              <section className="space-y-8" aria-label="Six Core Concepts">
                
                {/* 1. CHANGE REQUEST */}
                <div className="space-y-3">
                  <h3 id="concept-change-request" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                    A. Change Request
                  </h3>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    A <strong className="font-semibold text-[var(--color-riftless-ink)]">Change Request</strong> represents a proposed data structural or semantic change before it is physically applied to any live production environments.
                  </p>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    The original submitted input is preserved as an immutable run artifact. Common input types evaluated include:
                  </p>
                  <ul className="list-disc pl-5 space-y-2 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                    <li>Raw SQL schema migration files (e.g., DDL scripts)</li>
                    <li>dbt model updates and configuration diffs</li>
                    <li>Active schema alteration payloads</li>
                    <li>Pull request diff parameters from repository hooks</li>
                    <li>Downstream ownership assignments or data policy definitions</li>
                  </ul>
                </div>

                <hr className="border-stone-200/50" />

                {/* 2. CONTEXT PACK */}
                <div className="space-y-3">
                  <h3 id="concept-context-pack" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                    B. Context Pack
                  </h3>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    A Context Pack assembles relevant metadata available through the configured DataHub integration.
                  </p>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    Instead of scanning isolated code in a vacuum, the guardian extracts critical relational context:
                  </p>
                  <ul className="list-disc pl-5 space-y-2 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                    <li>schema definitions</li>
                    <li>column lineage</li>
                    <li>observed query usage</li>
                    <li>ownership metadata</li>
                    <li>governance tags</li>
                    <li>quality signals</li>
                    <li>declared ML dependencies</li>
                  </ul>
                  <Callout type="note">
                    More metadata does not automatically produce a safer decision. Context must remain relevant, bounded, and redacted.
                  </Callout>
                </div>

                <hr className="border-stone-200/50" />

                {/* 3. RISK DECISION */}
                <div className="space-y-3">
                  <h3 id="concept-risk-decision" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                    C. Risk Decision
                  </h3>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    The deterministic risk engine processes the Change Request alongside its Context Pack to produce an authoritative status:
                  </p>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
                    <div className="p-3 rounded border border-emerald-200 bg-emerald-50/40 text-center">
                      <span className="font-mono text-xs font-bold text-emerald-800 uppercase">ALLOW</span>
                      <p className="text-[10px] text-emerald-700/90 mt-1 font-mono">No configured blocking rule was triggered within the evaluated scope.</p>
                    </div>
                    <div className="p-3 rounded border border-amber-200 bg-amber-50/40 text-center">
                      <span className="font-mono text-xs font-bold text-amber-800 uppercase">WARN</span>
                      <p className="text-[10px] text-amber-700/90 mt-1 font-mono">Review may continue, but identified impact requires acknowledgment or human review.</p>
                    </div>
                    <div className="p-3 rounded border border-red-200 bg-red-50/40 text-center">
                      <span className="font-mono text-xs font-bold text-red-800 uppercase">BLOCK</span>
                      <p className="text-[10px] text-red-700/90 mt-1 font-mono">A configured policy or contract rule prevents the run from advancing.</p>
                    </div>
                  </div>

                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    DeepSeek may help analyze and explain the proposed change, but it does not authorize the final decision. Configured deterministic rules and policy gates determine whether the run may advance. Each target decision record should include diagnostic reasons and references to affected downstream assets.
                  </p>
                </div>

                <hr className="border-stone-200/50" />

                {/* 4. REMEDIATION PLAN */}
                <div className="space-y-3">
                  <h3 id="concept-remediation-plan" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                    D. Remediation Plan
                  </h3>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    When a Change Request is flagged or blocked, DeepSeek proposes a compatible <strong className="font-semibold text-[var(--color-riftless-ink)]">Remediation Plan</strong> designed to resolve compatibility risks without bypassing policy or validation.
                  </p>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    The remediation maps out specific corrective or staged migration actions:
                  </p>
                  <ul className="list-disc pl-5 space-y-2 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                    <li>Proposed generation of backward-compatibility proxy views</li>
                    <li>Coordinated column renames with dual-write periods</li>
                    <li>Downstream query adjustment scripts and code patches</li>
                    <li>Staged deprecation windows with automated notifications</li>
                    <li>Explicit owner action requests routed to corresponding teams</li>
                  </ul>
                  <Callout type="warning">
                    A generated remediation is a proposal, not executable evidence.
                  </Callout>
                </div>

                <hr className="border-stone-200/50" />

                {/* 5. VALIDATION BUNDLE */}
                <div className="space-y-3">
                  <h3 id="concept-validation-bundle" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                    E. Validation Bundle
                  </h3>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    Every proposed remediation plan or change must produce executable evidence within an isolated validation environment.
                  </p>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    The bundle packages specific programmatic validations to run against isolated target systems:
                  </p>
                  <ul className="list-disc pl-5 space-y-2 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                    <li>SQLGlot cross-dialect compilation and AST mapping checks</li>
                    <li>Local DuckDB verification instances running against sample fixtures</li>
                    <li>dbt compilation commands and schema assertions</li>
                    <li>Deterministic code policy linters and security boundary checkers</li>
                  </ul>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    A successful Validation Bundle shows that the tested proposal passed the configured validators within the tested scope. It is not a universal guarantee that no downstream failure can occur. Crucially, the Validation Bundle preserves full logs, execution environment contexts, terminal commands, explicit failure reasons, and raw diagnostic output.
                  </p>
                </div>

                <hr className="border-stone-200/50" />

                {/* 6. WRITEBACK RECORD */}
                <div className="space-y-3">
                  <h3 id="concept-writeback-record" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                    F. Writeback Record
                  </h3>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    After an authorized run completes, results can be written back to the configured organizational metadata catalog to act as durable, versioned organizational memory.
                  </p>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    The <strong className="font-semibold text-[var(--color-riftless-ink)]">Writeback Record</strong> updates the source metadata hub with the following target records:
                  </p>
                  <ul className="list-disc pl-5 space-y-2 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                    <li>risk tag</li>
                    <li>decision document</li>
                    <li>deprecation note</li>
                    <li>owner action</li>
                    <li>validation result</li>
                    <li>incident status</li>
                    <li>artifact references</li>
                  </ul>
                  <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                    After an authorized run completes, RIFTLESS can write the decision, validation outcome, and relevant artifact references back to DataHub. This allows future reviews to reuse previously recorded context and decisions.
                  </p>
                  <p className="text-sm font-semibold text-[var(--color-riftless-ink)] leading-relaxed">
                    The next review should inherit what the previous review learned.
                  </p>
                </div>
              </section>

              <hr className="border-stone-200" />

              {/* Operating model callout */}
              <Callout type="target" title="CORE OPERATING PRINCIPLE">
                DEEPSEEK PROPOSES.<br />
                DETERMINISTIC RULES AUTHORIZE.<br />
                EXECUTABLE TESTS PROVE.<br />
                DATAHUB PRESERVES THE DECISION.
              </Callout>

              <hr className="border-stone-200" />

              {/* Comparison Table */}
              <section className="space-y-4" aria-labelledby="concepts-comparison-table-heading">
                <h3 id="concepts-comparison-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Concepts Comparison Matrix
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The following table details the operational breakdown, physical requirements, and authoritative layers of the target review engine.
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="concepts-comparison-table">
                    <caption className="sr-only">Core Concepts comparison matrix mapping responsibility, evidence, and authority.</caption>
                    <thead className="bg-stone-50">
                      <tr>
                        <th scope="col" className="px-4 py-3 font-semibold uppercase text-stone-700">Concept</th>
                        <th scope="col" className="px-4 py-3 font-semibold uppercase text-stone-700">Primary Responsibility</th>
                        <th scope="col" className="px-4 py-3 font-semibold uppercase text-stone-700">Evidence Required</th>
                        <th scope="col" className="px-4 py-3 font-semibold uppercase text-stone-700">Final Authority</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 font-sans font-medium text-stone-900 text-left">Context Pack</th>
                        <td className="px-4 py-3 font-sans text-stone-600">Assembles relevant DataHub metadata for the proposed change.</td>
                        <td className="px-4 py-3 text-stone-500">Retrieved metadata, source references, and redaction record.</td>
                        <td className="px-4 py-3 text-stone-500">No authorization role; DataHub is the configured metadata source.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 font-sans font-medium text-stone-900 text-left">Risk Decision</th>
                        <td className="px-4 py-3 font-sans text-stone-600">Evaluates configured deterministic policies for ALLOW, WARN, or BLOCK.</td>
                        <td className="px-4 py-3 text-stone-500">Policy results, decision reasons, and affected asset references.</td>
                        <td className="px-4 py-3 text-stone-500">Deterministic risk rules and configured policy gates.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 font-sans font-medium text-stone-900 text-left">Remediation Plan</th>
                        <td className="px-4 py-3 font-sans text-stone-600">Proposes compatible migration or repair options.</td>
                        <td className="px-4 py-3 text-stone-500">Generated proposal, assumptions, and referenced context.</td>
                        <td className="px-4 py-3 text-stone-500">No authority until the proposal is validated and authorized.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 font-sans font-medium text-stone-900 text-left">Validation Bundle</th>
                        <td className="px-4 py-3 font-sans text-stone-600">Executes configured validators against the proposed change or remediation.</td>
                        <td className="px-4 py-3 text-stone-500">Commands, environment details, logs, test results, and artifact references.</td>
                        <td className="px-4 py-3 text-stone-500">Configured executable validators and deterministic policy checks.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 font-sans font-medium text-stone-900 text-left">Writeback Record</th>
                        <td className="px-4 py-3 font-sans text-stone-600">Persists the authorized decision and its evidence to organizational metadata.</td>
                        <td className="px-4 py-3 text-stone-500">Decision result, validation outcome, failure reason when applicable, and artifact references.</td>
                        <td className="px-4 py-3 text-stone-500">RIFTLESS control-plane authorization; DataHub stores the resulting record.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </article>
          ) : activeSection === 'Quickstart' ? (
            <article id="quickstart" aria-labelledby="quickstart-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="quickstart-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Quickstart
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  Set up the target review workflow, connect the required context sources, and prepare a first governed data change.
                </p>
              </div>

              {/* Target disclaimer */}
              <Callout type="target">
                This quickstart describes the target local workflow. Commands and interfaces marked as illustrative must be replaced with repository-backed instructions once the corresponding backend capability is implemented.
              </Callout>

              {/* Quickstart overview flow */}
              <div className="space-y-3 my-8">
                <div className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  TARGET FIRST-RUN WORKFLOW
                </div>
                <div className="flex flex-col md:flex-row md:items-center gap-1.5 md:gap-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px] overflow-x-auto">
                  <div className="flex-1 min-w-[80px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    PREPARE
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[80px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    CONFIGURE
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[80px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    CONNECT
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[80px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    SUBMIT
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[80px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    REVIEW
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[80px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    VALIDATE
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[80px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    PRESERVE
                  </div>
                </div>
              </div>

              <hr className="border-stone-200" />

              {/* Step 1 — Prerequisites */}
              <section className="space-y-3" aria-labelledby="step-1-heading">
                <h3 id="step-1-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  1. Prepare the environment
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Before initializing the target review workflow, ensure you have gathered the following conceptual and environment requirements:
                </p>
                <ul className="list-disc pl-5 space-y-2 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                  <li>a local checkout of the RIFTLESS repository</li>
                  <li>access to a configured DataHub environment</li>
                  <li>credentials for the selected GitHub integration</li>
                  <li>access to the configured DeepSeek API</li>
                  <li>a proposed SQL, schema, or dbt change</li>
                  <li>an isolated validation environment</li>
                  <li>optional access to a dbt project when dbt validation is enabled</li>
                </ul>
                <Callout type="note">
                  Use development or sandbox credentials during setup. Do not begin with production-write permissions.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Step 2 — Configuration */}
              <section className="space-y-3" aria-labelledby="step-2-heading">
                <h3 id="step-2-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  2. Define the review configuration
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Store configuration parameters in a declarative project manifest file. Below is an illustrative example of the main configuration concepts managed by the guardian:
                </p>
                
                {/* Illustrative Config Code Block */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between px-4 py-2 bg-stone-800 text-stone-300 text-[10px] font-mono rounded-t border-b border-stone-700">
                    <span>riftless.config.yaml</span>
                    <span className="text-[#A8CD16] font-semibold">TARGET CONFIGURATION EXAMPLE - NON-EXECUTABLE</span>
                  </div>
                  <pre className="p-4 bg-stone-900 rounded-b text-stone-100 font-mono text-xs overflow-x-auto leading-relaxed">
{`# Illustrative configuration shape only.
# This is not yet the repository-backed schema.

datahub:
  connection: "<configured-server-side-connection>"

repository:
  scope: "<configured-repository-scope>"

policies:
  risk: "<configured-risk-policy>"
  redaction: "<configured-redaction-policy>"

validators:
  enabled:
    - "sqlglot"
    - "duckdb"
    - "dbt"
    - "deterministic-policy"

writeback:
  mode: "<configured-writeback-mode>"

artifacts:
  location: "<configured-artifact-storage-location>"`}
                  </pre>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Step 3 — Credentials and Redaction */}
              <section className="space-y-3" aria-labelledby="step-3-heading">
                <h3 id="step-3-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  3. Configure credentials safely
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Establish isolated environments for your credentials to enforce strict exposure controls. The table below outlines how system credentials must be handled:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="credentials-safe-table">
                    <caption className="sr-only">Table mapping credentials, their usage, and strict server-side safety exposure rules.</caption>
                    <thead className="bg-stone-50">
                      <tr>
                        <th scope="col" className="px-4 py-3 font-semibold uppercase text-stone-700">Credential</th>
                        <th scope="col" className="px-4 py-3 font-semibold uppercase text-stone-700">Used By</th>
                        <th scope="col" className="px-4 py-3 font-semibold uppercase text-stone-700">Exposure Rule</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 font-sans font-medium text-stone-900 text-left">DataHub credential</th>
                        <td className="px-4 py-3 font-sans text-stone-600">Target server-side DataHub read and authorized writeback integration.</td>
                        <td className="px-4 py-3 text-red-600 font-bold">Server-side only.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 font-sans font-medium text-stone-900 text-left">GitHub credential</th>
                        <td className="px-4 py-3 font-sans text-stone-600">Target repository event and review integration.</td>
                        <td className="px-4 py-3 text-red-600 font-bold">Server-side only.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 font-sans font-medium text-stone-900 text-left">DeepSeek API credential</th>
                        <td className="px-4 py-3 font-sans text-stone-600">Target remediation planning and explanation using redacted context.</td>
                        <td className="px-4 py-3 text-red-600 font-bold">Server-side only.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <Callout type="warning">
                  Secrets must never be included in model context, generated artifacts, browser-visible configuration, or validation logs.
                </Callout>

                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target model request should contain only the redacted Context Pack, proposed change, and configured policy constraints.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Step 4 — Prepare a change */}
              <section className="space-y-3" aria-labelledby="step-4-heading">
                <h3 id="step-4-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  4. Prepare the proposed change
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Create a localized schema alteration file representing your intent. The example below renames a critical identifier column:
                </p>

                {/* Example Proposed Change Code Block */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between px-4 py-2 bg-stone-800 text-stone-300 text-[10px] font-mono rounded-t border-b border-stone-700">
                    <span>migrations/001_rename_customer.sql</span>
                    <span className="text-[#A8CD16] font-semibold">EXAMPLE PROPOSED CHANGE</span>
                  </div>
                  <pre className="p-4 bg-stone-900 rounded-b text-stone-100 font-mono text-xs overflow-x-auto leading-relaxed">
{`ALTER TABLE analytics.orders
RENAME COLUMN customer_id TO account_id;`}
                  </pre>
                </div>

                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  This change is intentionally incomplete as a compatibility strategy. RIFTLESS must evaluate downstream references before the change may advance.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Step 5 — Submit the review */}
              <section className="space-y-3" aria-labelledby="step-5-heading">
                <h3 id="step-5-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  5. Submit a review
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Submit your proposed migration query block to the target review gate:
                </p>

                {/* Pseudo CLI Code Block */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between px-4 py-2 bg-stone-800 text-stone-300 text-[10px] font-mono rounded-t border-b border-stone-700">
                    <span>Terminal</span>
                    <span className="text-amber-500 font-semibold">NON-EXECUTABLE TARGET INTERFACE</span>
                  </div>
                  <pre className="p-4 bg-stone-900 rounded-b text-stone-100 font-mono text-xs overflow-x-auto leading-relaxed">
{`riftless review ./migrations/001_rename_customer.sql`}
                  </pre>
                </div>

                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The final command or API request will be documented after the backend interface is implemented and versioned.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Step 6 — Review the decision */}
              <section className="space-y-3" aria-labelledby="step-6-heading">
                <h3 id="step-6-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  6. Inspect the risk decision
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  In the target workflow, the deterministic policy engine evaluates the input scope and produces one of three distinct statuses:
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
                  <div className="p-3 rounded border border-emerald-200 bg-emerald-50/40 text-center">
                    <span className="font-mono text-xs font-bold text-emerald-800 uppercase">ALLOW</span>
                    <p className="text-[10px] text-emerald-700/90 mt-1 font-mono">No configured blocking rule was triggered within the evaluated scope.</p>
                  </div>
                  <div className="p-3 rounded border border-amber-200 bg-amber-50/40 text-center">
                    <span className="font-mono text-xs font-bold text-amber-800 uppercase">WARN</span>
                    <p className="text-[10px] text-amber-700/90 mt-1 font-mono">The run requires acknowledgment or human review before advancing.</p>
                  </div>
                  <div className="p-3 rounded border border-red-200 bg-red-50/40 text-center">
                    <span className="font-mono text-xs font-bold text-red-800 uppercase">BLOCK</span>
                    <p className="text-[10px] text-red-700/90 mt-1 font-mono">A configured policy or contract rule prevents the run from advancing.</p>
                  </div>
                </div>

                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target review output should include:
                </p>
                <ul className="list-disc pl-5 space-y-1.5 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                  <li>decision status</li>
                  <li>decision reasons</li>
                  <li>affected assets</li>
                  <li>referenced policies</li>
                  <li>Context Pack reference</li>
                  <li>proposed remediation when applicable</li>
                </ul>
              </section>

              <hr className="border-stone-200/50" />

              {/* Step 7 — Validate the proposal */}
              <section className="space-y-3" aria-labelledby="step-7-heading">
                <h3 id="step-7-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  7. Validate executable evidence
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Remediated suggestions or raw proposals must undergo executable validation using your project's configured sandbox tests:
                </p>
                <ul className="list-disc pl-5 space-y-2 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                  <li>SQLGlot compilation and schema mapping verification</li>
                  <li>Local DuckDB database integrity runs against fixtures</li>
                  <li>dbt compilation and test command executions</li>
                  <li>Deterministic policy constraint and compliance checks</li>
                </ul>

                <Callout type="warning">
                  A remediation proposal cannot advance solely because it appears reasonable. The configured validation steps must produce executable evidence.
                </Callout>

                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation runner should preserve an evidence trail including:
                </p>
                <ul className="list-disc pl-5 space-y-1.5 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                  <li>executed commands</li>
                  <li>environment details</li>
                  <li>logs</li>
                  <li>test outcomes</li>
                  <li>failure reason when applicable</li>
                  <li>artifact references</li>
                </ul>
              </section>

              <hr className="border-stone-200/50" />

              {/* Step 8 — Preserve the result */}
              <section className="space-y-3" aria-labelledby="step-8-heading">
                <h3 id="step-8-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  8. Preserve the authorized result
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  After authorization, the target writeback record may include:
                </p>
                <ul className="list-disc pl-5 space-y-1.5 text-xs text-[var(--color-riftless-ink)] leading-relaxed font-mono">
                  <li>risk tag</li>
                  <li>decision document</li>
                  <li>deprecation note</li>
                  <li>owner action</li>
                  <li>validation result</li>
                  <li>incident status</li>
                  <li>artifact references</li>
                </ul>
              </section>

              <hr className="border-stone-200" />

              {/* Completion checklist */}
              <section className="space-y-4" aria-labelledby="checklist-heading">
                <h3 id="checklist-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  First Review Checklist
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Verify your local environment satisfies all operational checkpoints before initiating target pipeline evaluations:
                </p>
                <ul className="space-y-3 font-mono text-xs text-[var(--color-riftless-ink)] border border-stone-200 rounded p-5 bg-stone-50/50 max-w-md">
                  <li className="flex items-start gap-2.5">
                    <span className="text-[#A8CD16] font-bold text-sm leading-none">✓</span>
                    <span>Context source configured</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="text-[#A8CD16] font-bold text-sm leading-none">✓</span>
                    <span>Credentials remain server-side</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="text-[#A8CD16] font-bold text-sm leading-none">✓</span>
                    <span>Proposed change captured</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="text-[#A8CD16] font-bold text-sm leading-none">✓</span>
                    <span>Risk decision generated</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="text-[#A8CD16] font-bold text-sm leading-none">✓</span>
                    <span>Policy reasons available</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="text-[#A8CD16] font-bold text-sm leading-none">✓</span>
                    <span>Validation evidence produced</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="text-[#A8CD16] font-bold text-sm leading-none">✓</span>
                    <span>Writeback authorization recorded</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="text-[#A8CD16] font-bold text-sm leading-none">✓</span>
                    <span>Artifacts preserved</span>
                  </li>
                </ul>
              </section>
            </article>
          ) : activeSection === 'System Overview' ? (
            <section id="system-overview" aria-labelledby="system-overview-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="system-overview-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  System Overview
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  RIFTLESS coordinates context assembly, deterministic decision-making, remediation planning, isolated validation, and evidence preservation around a proposed data change.
                </p>
              </div>

              {/* Target disclaimer */}
              <Callout type="target">
                This section describes the target system architecture. Individual components may remain illustrative until their repository-backed implementation is available.
              </Callout>

              {/* High-level system flow */}
              <div className="space-y-3 my-8">
                <div className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  TARGET CONTROL FLOW
                </div>
                <div className="flex flex-col md:flex-row md:items-center gap-1.5 md:gap-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px] overflow-x-auto">
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    CHANGE INPUT
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    CONTEXT ASSEMBLY
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    RISK DECISION
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    REMEDIATION
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    VALIDATION
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-[var(--color-riftless-ink)] shadow-sm">
                    WRITEBACK
                  </div>
                </div>
              </div>

              <hr className="border-stone-200" />

              {/* System boundaries subsection */}
              <section className="space-y-6" aria-labelledby="system-boundaries-heading">
                <h3 id="system-boundaries-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  System Boundaries
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target RIFTLESS architecture isolates functions into distinct processing zones to protect underlying schemas and catalog states:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* A. CHANGE SOURCES */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">A. Change Sources</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Target inputs may originate from:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>GitHub pull request changes</li>
                      <li>SQL migration files</li>
                      <li>dbt model changes</li>
                      <li>schema alteration requests</li>
                      <li>ownership or governance updates</li>
                    </ul>
                  </div>

                  {/* B. RIFTLESS CONTROL PLANE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">B. Riftless Control Plane</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Target responsibilities include:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>receive and normalize a proposed change</li>
                      <li>assemble the Context Pack</li>
                      <li>evaluate deterministic risk rules</li>
                      <li>request remediation proposals when required</li>
                      <li>authorize validation steps</li>
                      <li>preserve run state and artifact references</li>
                      <li>authorize configured writeback behavior</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">
                      The control plane owns orchestration and authorization. The model does not.
                    </p>
                  </div>

                  {/* C. ISOLATED EXECUTION */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">C. Isolated Execution</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Target responsibilities include:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>execute configured validation commands</li>
                      <li>run SQLGlot analysis</li>
                      <li>run DuckDB fixtures</li>
                      <li>run dbt compilation or tests when configured</li>
                      <li>preserve logs and test outcomes</li>
                      <li>return evidence without direct production mutation</li>
                    </ul>
                    <div className="mt-2 text-[11px] bg-amber-50 border-l-2 border-[#F2A93B] p-2 text-amber-900">
                      <strong>WARNING:</strong> The validation worker must not receive unrestricted production-write credentials.
                    </div>
                  </div>

                  {/* D. EXTERNAL SERVICES */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">D. External Services</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Document target dependencies that coordinate with RIFTLESS:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>DataHub metadata catalog</li>
                      <li>GitHub integration endpoints</li>
                      <li>DeepSeek API endpoint</li>
                      <li>configured artifact storage location</li>
                      <li>configured validation tools</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] italic border-t border-stone-100 pt-2">
                      External integrations are evaluated on target paths and may be modified once configuration is stable.
                    </p>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Component responsibility table */}
              <section className="space-y-4" aria-labelledby="components-heading">
                <h3 id="components-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Component Responsibilities
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Every system module has localized responsibilities, deterministic inputs, produced outputs, and safety role definitions:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="component-responsibilities-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target system components, responsibilities, inputs, outputs, and authorization boundaries.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Component</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Primary Responsibility</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Receives</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Produces</th>
                        <th scope="col" className="px-4 py-3">Authorization Role</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CHANGE INGESTION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Normalize the proposed change into a review input.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Repository diff, SQL, schema, dbt, or policy input.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Change Request artifact.</td>
                        <td className="px-4 py-3 text-stone-600 align-top font-semibold">No deployment authority.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTEXT PACK BUILDER</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Assemble relevant configured DataHub metadata.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Change Request and metadata references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Redacted Context Pack.</td>
                        <td className="px-4 py-3 text-stone-600 align-top font-semibold">No decision authority.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DETERMINISTIC RISK ENGINE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Evaluate configured policy and contract rules.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Change Request and Context Pack.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">ALLOW, WARN, or BLOCK decision with reasons.</td>
                        <td className="px-4 py-3 text-stone-900 align-top font-semibold">Determines whether the run may advance within configured policy.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DEEPSEEK REMEDIATION PLANNER</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Propose explanations and compatible remediation options.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Redacted Context Pack, proposed change, and policy constraints.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Remediation proposal and assumptions.</td>
                        <td className="px-4 py-3 text-stone-600 align-top font-semibold">No authorization role.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ISOLATED VALIDATION WORKER</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Execute configured validation steps.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Proposed change or remediation plan.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Validation Bundle containing executable evidence.</td>
                        <td className="px-4 py-3 text-stone-600 align-top font-semibold">Provides evidence; does not independently authorize production deployment.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITEBACK ADAPTER</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Persist authorized decision records to configured organizational metadata.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Authorized decision and evidence references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Target DataHub writeback record.</td>
                        <td className="px-4 py-3 text-stone-600 align-top font-semibold">Writes only after control-plane authorization.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Data movement subsection */}
              <section className="space-y-4" aria-labelledby="data-movement-heading">
                <h3 id="data-movement-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Data Movement
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target workflow separates data movement into explicit paths so that context, model requests, validation evidence, and authorized writeback remain independently governed.
                </p>

                <div className="space-y-4 max-w-3xl">
                  {/* Read Path */}
                  <div className="p-4 bg-stone-50/50 border border-stone-200 rounded font-mono text-[10px]">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--color-riftless-graph-gray)] block mb-2">
                      READ PATH
                    </span>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-stone-700">DATAHUB</span>
                      <span className="text-[var(--color-riftless-graph-gray)] font-bold">→</span>
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded text-stone-600">METADATA REFERENCES</span>
                      <span className="text-[var(--color-riftless-graph-gray)] font-bold">→</span>
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded text-stone-600">REDACTED CONTEXT PACK</span>
                      <span className="text-[var(--color-riftless-graph-gray)] font-bold">→</span>
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-[var(--color-riftless-ink)]">GROUNDED REVIEW INPUT</span>
                    </div>
                  </div>

                  {/* Model Path */}
                  <div className="p-4 bg-stone-50/50 border border-stone-200 rounded font-mono text-[10px]">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--color-riftless-graph-gray)] block mb-2">
                      MODEL PATH
                    </span>
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="flex items-center gap-1">
                        <span className="px-2 py-1 bg-white border border-stone-200 rounded text-stone-600">REDACTED CONTEXT PACK</span>
                        <span className="text-[var(--color-riftless-graph-gray)] font-bold">+</span>
                        <span className="px-2 py-1 bg-white border border-stone-200 rounded text-stone-600">PROPOSED CHANGE</span>
                        <span className="text-[var(--color-riftless-graph-gray)] font-bold">+</span>
                        <span className="px-2 py-1 bg-white border border-stone-200 rounded text-stone-600">POLICY CONSTRAINTS</span>
                      </div>
                      <span className="text-[var(--color-riftless-graph-gray)] font-bold">→</span>
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-stone-700">DEEPSEEK</span>
                      <span className="text-[var(--color-riftless-graph-gray)] font-bold">→</span>
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-[var(--color-riftless-ink)]">REMEDIATION PROPOSAL</span>
                    </div>
                  </div>

                  {/* Validation Path */}
                  <div className="p-4 bg-stone-50/50 border border-stone-200 rounded font-mono text-[10px]">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--color-riftless-graph-gray)] block mb-2">
                      VALIDATION PATH
                    </span>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded text-stone-600">PROPOSED CHANGE OR REMEDIATION</span>
                      <span className="text-[var(--color-riftless-graph-gray)] font-bold">→</span>
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-stone-700">ISOLATED VALIDATION</span>
                      <span className="text-[var(--color-riftless-graph-gray)] font-bold">→</span>
                      <span className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-[var(--color-riftless-ink)]">LOGS, TEST RESULTS, AND ARTIFACT REFERENCES</span>
                    </div>
                  </div>

                  {/* Writeback Path */}
                  <div className="p-4 bg-stone-50/50 border border-stone-200 rounded font-mono text-[10px]">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--color-riftless-graph-gray)] block mb-2">
                      WRITEBACK PATH
                    </span>
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="flex items-center gap-1">
                        <span className="px-2 py-1 bg-white border border-stone-200 rounded text-stone-600">AUTHORIZED DECISION</span>
                        <span className="text-[var(--color-riftless-graph-gray)] font-bold">+</span>
                        <span className="px-2 py-1 bg-white border border-[#A8CD16]/30 bg-[#A8CD16]/5 rounded text-[#A8CD16] font-bold">VALIDATION OUTCOME</span>
                      </div>
                      <span className="text-[var(--color-riftless-graph-gray)] font-bold">→</span>
                      <span className="px-2 py-1 bg-white border border-[#A8CD16]/30 bg-[#A8CD16]/5 rounded font-bold text-[#A8CD16]">CONFIGURED DATAHUB WRITEBACK</span>
                    </div>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Secrets and redaction guardrail */}
              <section className="space-y-4" aria-labelledby="secrets-guardrail-heading">
                <h3 id="secrets-guardrail-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Secrets and Redaction Guardrail
                </h3>
                <Callout type="warning">
                  Server-side credentials must never be included in model context, generated artifacts, browser-visible configuration, or validation logs.
                </Callout>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl my-6">
                  <div className="border border-stone-200 rounded p-4 bg-stone-50/50">
                    <span className="text-[10px] font-mono tracking-wider font-bold text-red-600 uppercase block mb-2">SERVER-SIDE ONLY</span>
                    <ul className="list-disc pl-5 space-y-1 text-xs font-mono text-stone-700">
                      <li>DataHub credentials</li>
                      <li>GitHub credentials</li>
                      <li>DeepSeek API credentials</li>
                      <li>artifact storage credentials</li>
                    </ul>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-stone-50/50">
                    <span className="text-[10px] font-mono tracking-wider font-bold text-[#A8CD16] uppercase block mb-2">MODEL-CONTEXT ALLOWLIST</span>
                    <ul className="list-disc pl-5 space-y-1 text-xs font-mono text-stone-700">
                      <li>redacted Context Pack</li>
                      <li>proposed change</li>
                      <li>configured policy constraints</li>
                    </ul>
                  </div>
                </div>

                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target request assembly process must exclude secrets before model context is created. Configured redaction rules should remove or reject prohibited values before a model request is sent. Runtime verification is required to confirm that no credential or restricted value is exposed.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Operating Authority */}
              <section className="space-y-4" aria-labelledby="authority-heading">
                <h3 id="authority-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Authority Model
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target authority model separates advisory model output, deterministic policy decisions, executable validation evidence, and authorized metadata writeback.
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-4 font-mono">
                  <div className="space-y-2 border-b border-stone-200 pb-4">
                    <div className="text-sm font-bold text-[var(--color-riftless-ink)] uppercase">DEEPSEEK PROPOSES.</div>
                    <div className="text-sm font-bold text-[var(--color-riftless-ink)] uppercase">DETERMINISTIC RULES AUTHORIZE.</div>
                    <div className="text-sm font-bold text-[var(--color-riftless-ink)] uppercase">EXECUTABLE TESTS PROVE.</div>
                    <div className="text-sm font-bold text-[var(--color-riftless-ink)] uppercase">DATAHUB PRESERVES THE DECISION.</div>
                  </div>

                  <ul className="list-disc pl-5 space-y-2 text-xs text-stone-700 leading-relaxed">
                    <li>The model output is strictly advisory, providing diagnostic rationales and compatible suggestions.</li>
                    <li>The deterministic policy engine decides whether the run may advance within configured policy constraints.</li>
                    <li>Validation evidence produced through execution of actual tests is required where configured to verify correctness.</li>
                    <li>The target writeback adapter may persist a decision only after control-plane authorization has been recorded.</li>
                    <li>No component, agent, or runner can bypass configured policies or required validation gates.</li>
                  </ul>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Failure isolation note */}
              <section className="space-y-4" aria-labelledby="failure-isolation-heading">
                <h4 id="failure-isolation-heading" className="text-xs font-mono tracking-wider uppercase text-stone-500 font-semibold">
                  Failure Isolation
                </h4>
                <Callout type="note">
                  A failure in DataHub access, model availability, validation execution, or writeback must stop the affected stage without erasing previously captured artifacts.
                </Callout>
              </section>
            </section>
          ) : activeSection === 'Trust Boundaries' ? (
            <section id="trust-boundaries" aria-labelledby="trust-boundaries-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="trust-boundaries-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Trust Boundaries
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  RIFTLESS separates untrusted change inputs, advisory model output, deterministic authorization, isolated execution, and metadata writeback into explicit trust zones.
                </p>
              </div>

              {/* TARGET callout */}
              <Callout type="target">
                This section describes the target trust model. Every boundary must be enforced by repository-backed controls and verified through runtime tests before it is treated as an implemented security guarantee.
              </Callout>

              {/* Static trust flow */}
              <div className="space-y-3 my-8">
                <div className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  TARGET TRUST FLOW
                </div>
                {/* Horizontal on md+, wrap/vertical on mobile */}
                <div className="flex flex-col md:flex-row md:items-center gap-1.5 md:gap-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px] overflow-x-auto">
                  <div className="flex-1 min-w-[110px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    UNTRUSTED CHANGE INPUT
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[110px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    CONTROL PLANE INTAKE
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[110px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    REDACTED CONTEXT
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[110px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    ADVISORY MODEL PROPOSAL
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[110px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    DETERMINISTIC POLICY GATE
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[110px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    ISOLATED VALIDATION
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[110px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    AUTHORIZED WRITEBACK
                  </div>
                </div>

                {/* Blocked Path Visualizer */}
                <div className="mt-4 p-3 border border-red-200/50 bg-red-50/10 rounded-r border-l-4 border-red-500 max-w-xl">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 font-mono text-[9px]">
                    <span className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-stone-700">
                      ADVISORY MODEL OUTPUT
                    </span>
                    <span className="text-red-600 font-extrabold text-sm text-center px-1" aria-label="blocked">×</span>
                    <span className="px-2 py-1 bg-white border border-red-200 text-red-700 rounded font-bold bg-red-50/20">
                      DIRECT PRODUCTION WRITE
                    </span>
                    <span className="sm:ml-auto px-1.5 py-0.5 bg-red-100 text-red-800 rounded font-bold uppercase tracking-wider text-[8px]">
                      BLOCKED
                    </span>
                  </div>
                </div>
              </div>

              <hr className="border-stone-200" />

              {/* Trust Zones subsection */}
              <section className="space-y-6" aria-labelledby="trust-zones-heading">
                <h3 id="trust-zones-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Trust Zones
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target trust model segments data flows into five security domains:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* A. EXTERNAL INPUT ZONE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">A. External Input Zone</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      May receive:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>GitHub pull request diff</li>
                      <li>SQL migration</li>
                      <li>dbt model change</li>
                      <li>schema alteration request</li>
                      <li>ownership or governance update</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">
                      Trust position:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>input is treated as untrusted</li>
                      <li>input must be normalized before evaluation</li>
                      <li>original submitted input should be preserved as a run artifact</li>
                    </ul>
                    <p className="text-xs text-red-700 font-semibold">
                      Must not directly trigger production mutation, provide authorization, or introduce secrets into model context.
                    </p>
                  </div>

                  {/* B. RIFTLESS CONTROL PLANE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">B. Riftless Control Plane</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Target responsibilities:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>normalize the Change Request</li>
                      <li>assemble relevant context</li>
                      <li>apply redaction policy</li>
                      <li>evaluate deterministic risk rules</li>
                      <li>coordinate remediation requests</li>
                      <li>authorize validation stages</li>
                      <li>record run state and artifact references</li>
                      <li>authorize configured writeback behavior</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">
                      The control plane coordinates the run and records authorization decisions. The model does not own this authority.
                    </p>
                  </div>

                  {/* C. MODEL REQUEST ZONE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">C. Model Request Zone</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      May receive only:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>redacted Context Pack</li>
                      <li>proposed change</li>
                      <li>configured policy constraints</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-1 font-semibold">
                      May produce:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>explanation</li>
                      <li>assumptions</li>
                      <li>remediation proposal</li>
                      <li>compatibility suggestions</li>
                    </ul>
                    <p className="text-xs text-red-700 font-semibold">
                      Must not receive DataHub credentials, GitHub credentials, DeepSeek API credentials, artifact storage credentials, unrestricted production data, or unrestricted validation logs containing secrets.
                    </p>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold">
                      Model output is advisory and cannot authorize validation, deployment, or writeback.
                    </p>
                  </div>

                  {/* D. ISOLATED EXECUTION ZONE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">D. Isolated Execution Zone</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      May receive:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>proposed change</li>
                      <li>remediation proposal</li>
                      <li>configured validation commands</li>
                      <li>fixtures or bounded test data</li>
                      <li>policy references</li>
                      <li>artifact destinations</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-1 font-semibold">
                      May produce:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>validation logs</li>
                      <li>test outcomes</li>
                      <li>failure reasons</li>
                      <li>artifact references</li>
                      <li>Validation Bundle</li>
                    </ul>
                    <p className="text-xs text-red-700 font-semibold">
                      Must not receive unrestricted production-write credentials, mutate production systems directly, authorize its own result, or bypass deterministic policy checks.
                    </p>
                  </div>

                  {/* E. AUTHORIZED WRITEBACK ZONE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3 md:col-span-2">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">E. Authorized Writeback Zone</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      May receive:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>recorded authorization decision</li>
                      <li>risk status</li>
                      <li>validation outcome</li>
                      <li>decision reasons</li>
                      <li>artifact references</li>
                      <li>owner actions</li>
                      <li>failure status when applicable</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-1 font-semibold">
                      May produce:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs font-mono text-stone-700 leading-relaxed">
                      <li>target DataHub risk tag</li>
                      <li>decision document</li>
                      <li>deprecation note</li>
                      <li>validation result</li>
                      <li>incident status</li>
                      <li>owner action record</li>
                    </ul>
                    <p className="text-xs text-red-700 font-semibold">
                      Must not write an unvalidated proposal as verified evidence, accept model output as authorization, or run before control-plane authorization is recorded.
                    </p>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Boundary responsibility table */}
              <section className="space-y-4" aria-labelledby="boundary-table-heading">
                <h3 id="boundary-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Boundary Responsibility Matrix
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The trust rules governing inputs, outputs, authority levels, and constraints are systematically mapped below:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="boundary-responsibility-matrix-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target trust zones, permitted inputs, permitted outputs, and prohibited authority.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Trust Zone</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Permitted Inputs</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Permitted Outputs</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Authority</th>
                        <th scope="col" className="px-4 py-3">Prohibited Behavior</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">EXTERNAL INPUT</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Repository diff, SQL, dbt, schema, or policy change.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Normalized Change Request.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 align-top font-bold">None.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Direct execution or writeback.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTROL PLANE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Change Request, metadata references, policy configuration.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Context Pack, risk decision, authorization record.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-900 align-top font-bold">May determine whether the run advances within configured policy.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Bypassing required validation or redaction.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">MODEL REQUEST</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Redacted Context Pack, proposed change, policy constraints.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Explanation and remediation proposal.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 align-top font-bold">Advisory only.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Authorization, direct execution, or direct writeback.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ISOLATED VALIDATION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Proposed change or remediation, validators, bounded fixtures.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Validation Bundle and artifact references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 align-top font-bold">Produces evidence only.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Production mutation or self-authorization.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITEBACK ADAPTER</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Recorded authorization and evidence references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Configured organizational metadata record.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-900 align-top font-bold">Writes only after control-plane authorization.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Persisting an unauthorized decision as approved.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Explicit Blocked Paths */}
              <section className="space-y-4" aria-labelledby="blocked-paths-heading">
                <h3 id="blocked-paths-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Blocked Paths
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target trust model explicitly restricts and rejects the following execution paths:
                </p>

                <div className="space-y-4 max-w-3xl">
                  <div className="border-l-2 border-red-500 pl-4 py-1 space-y-1">
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="font-bold text-stone-800">MODEL OUTPUT</span>
                      <span className="text-red-600 font-extrabold" aria-hidden="true">×</span>
                      <span className="font-bold text-stone-800">DIRECT PRODUCTION MUTATION</span>
                      <span className="text-[9px] bg-red-100 text-red-800 font-bold px-1.5 py-0.5 rounded uppercase">BLOCKED</span>
                    </div>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Model recommendations are strictly advisory and cannot bypass automated validation steps or write directly to critical database targets.
                    </p>
                  </div>

                  <div className="border-l-2 border-red-500 pl-4 py-1 space-y-1">
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="font-bold text-stone-800">BROWSER CLIENT</span>
                      <span className="text-red-600 font-extrabold" aria-hidden="true">×</span>
                      <span className="font-bold text-stone-800">SERVER-SIDE CREDENTIAL ACCESS</span>
                      <span className="text-[9px] bg-red-100 text-red-800 font-bold px-1.5 py-0.5 rounded uppercase">BLOCKED</span>
                    </div>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      All secrets, API credentials, and catalog auth keys must remain protected within the server context and never be exposed to browser execution blocks.
                    </p>
                  </div>

                  <div className="border-l-2 border-red-500 pl-4 py-1 space-y-1">
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="font-bold text-stone-800">UNVALIDATED REMEDIATION</span>
                      <span className="text-red-600 font-extrabold" aria-hidden="true">×</span>
                      <span className="font-bold text-stone-800">VERIFIED EVIDENCE STATUS</span>
                      <span className="text-[9px] bg-red-100 text-red-800 font-bold px-1.5 py-0.5 rounded uppercase">BLOCKED</span>
                    </div>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Any proposed model remediation remains an unverified draft until isolated tests execute and generate concrete evidence logs.
                    </p>
                  </div>

                  <div className="border-l-2 border-red-500 pl-4 py-1 space-y-1">
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="font-bold text-stone-800">VALIDATION WORKER</span>
                      <span className="text-red-600 font-extrabold" aria-hidden="true">×</span>
                      <span className="font-bold text-stone-800">SELF-AUTHORIZATION</span>
                      <span className="text-[9px] bg-red-100 text-red-800 font-bold px-1.5 py-0.5 rounded uppercase">BLOCKED</span>
                    </div>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Execution runners compile evidence but lack the authority to independently update policy rules or approve their own outcomes.
                    </p>
                  </div>

                  <div className="border-l-2 border-red-500 pl-4 py-1 space-y-1">
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="font-bold text-stone-800">UNAUTHORIZED DECISION</span>
                      <span className="text-red-600 font-extrabold" aria-hidden="true">×</span>
                      <span className="font-bold text-stone-800">DATAHUB WRITEBACK</span>
                      <span className="text-[9px] bg-red-100 text-red-800 font-bold px-1.5 py-0.5 rounded uppercase">BLOCKED</span>
                    </div>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Metadata updates and risk tags will not write to the catalog unless the central control plane officially records a successful policy decision.
                    </p>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Model-Context Boundary Subsection */}
              <section className="space-y-4" aria-labelledby="model-context-boundary-heading">
                <h3 id="model-context-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Model-Context Boundary
                </h3>
                <Callout type="warning">
                  A field is not safe for model context merely because it appears inside metadata. Configured redaction and allowlist rules must evaluate the value before request assembly.
                </Callout>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl my-6">
                  <div className="border border-stone-200 rounded p-4 bg-stone-50/50">
                    <span className="text-[10px] font-mono tracking-wider font-bold text-[#A8CD16] uppercase block mb-2">MODEL-CONTEXT ALLOWLIST</span>
                    <ul className="list-disc pl-5 space-y-1 text-xs font-mono text-stone-700">
                      <li>redacted Context Pack</li>
                      <li>proposed change</li>
                      <li>configured policy constraints</li>
                      <li>bounded schema references</li>
                      <li>relevant lineage references</li>
                      <li>required ownership metadata</li>
                    </ul>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-stone-50/50">
                    <span className="text-[10px] font-mono tracking-wider font-bold text-stone-500 uppercase block mb-2">SERVER-SIDE ONLY</span>
                    <ul className="list-disc pl-5 space-y-1 text-xs font-mono text-stone-700">
                      <li>DataHub credentials</li>
                      <li>GitHub credentials</li>
                      <li>DeepSeek API credentials</li>
                      <li>artifact storage credentials</li>
                      <li>internal authorization records</li>
                      <li>unrestricted raw logs</li>
                      <li>secret environment variables</li>
                    </ul>
                  </div>
                </div>

                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Runtime tests should verify that prohibited values are rejected or removed before any model request is sent. The target design requires explicit data classification, configured redaction rules, and runtime tests to reduce the risk of prohibited values entering model context.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Authorization Sequence Subsection */}
              <section className="space-y-4" aria-labelledby="auth-sequence-heading">
                <h3 id="auth-sequence-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Authorization Sequence
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target lifecycle defines the following ordered state progression:
                </p>

                <ol className="list-decimal pl-5 space-y-2 text-sm text-stone-700 font-mono leading-relaxed max-w-2xl">
                  <li><strong>CHANGE NORMALIZED:</strong> Input format converted to a generic Change Request.</li>
                  <li><strong>CONTEXT ASSEMBLED:</strong> Configured organizational and catalog metadata is fetched.</li>
                  <li><strong>SECRETS EXCLUDED:</strong> Configured redaction rules must remove or reject prohibited values before model request assembly.</li>
                  <li><strong>DETERMINISTIC RISK EVALUATED:</strong> Policies run to determine initial block/allow status.</li>
                  <li><strong>REMEDIATION PROPOSED WHEN REQUIRED:</strong> Compatible changes are drafted if block/warn occurs.</li>
                  <li><strong>VALIDATION EVIDENCE PRODUCED:</strong> Bounded execution builds concrete outcomes.</li>
                  <li><strong>AUTHORIZATION RECORDED:</strong> Required policy decisions, validation outcomes, and authorization state are recorded.</li>
                  <li><strong>WRITEBACK PERMITTED:</strong> The control plane may permit configured metadata writeback after the required authorization state is recorded.</li>
                </ol>

                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  A later stage may proceed only when its required predecessor state and authorization record are available.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Trust Invariants Subsection */}
              <section className="space-y-4" aria-labelledby="trust-invariants-heading">
                <h3 id="trust-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Trust Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target trust model defines static authority constraints for each component:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">THE MODEL MAY PROPOSE.</div>
                    <div className="text-stone-500">IT MAY NOT AUTHORIZE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">THE VALIDATION WORKER MAY PROVE.</div>
                    <div className="text-stone-500">IT MAY NOT DEPLOY.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">THE WRITEBACK ADAPTER MAY PERSIST.</div>
                    <div className="text-stone-500">IT MAY NOT DECIDE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">THE CONTROL PLANE MAY AUTHORIZE.</div>
                    <div className="text-stone-500">IT MAY NOT BYPASS POLICY.</div>
                  </div>
                </div>

                <Callout type="target">
                  No component should be able to silently elevate its own authority.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Boundary Failure Behavior Subsection */}
              <section className="space-y-4" aria-labelledby="boundary-failure-heading">
                <h3 id="boundary-failure-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Boundary Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target trust architecture enforces deterministic failure modes under anomalous runtime conditions:
                </p>

                <div className="space-y-4 max-w-2xl font-mono text-xs">
                  <div className="p-4 border border-stone-200 bg-stone-50/30 rounded">
                    <span className="font-bold text-stone-900 block mb-1">Redaction failure:</span>
                    <p className="text-stone-600 leading-relaxed">The model request must not be sent.</p>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/30 rounded">
                    <span className="font-bold text-stone-900 block mb-1">Policy evaluation failure:</span>
                    <p className="text-stone-600 leading-relaxed">The run must not advance.</p>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/30 rounded">
                    <span className="font-bold text-stone-900 block mb-1">Validation environment failure:</span>
                    <p className="text-stone-600 leading-relaxed">The result must not be marked validated.</p>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/30 rounded">
                    <span className="font-bold text-stone-900 block mb-1">Authorization record missing:</span>
                    <p className="text-stone-600 leading-relaxed">The writeback must not proceed.</p>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/30 rounded">
                    <span className="font-bold text-stone-900 block mb-1">Writeback failure:</span>
                    <p className="text-stone-600 leading-relaxed">The decision and evidence references should remain available for target retry handling.</p>
                  </div>
                </div>
              </section>
            </section>
          ) : activeSection === 'Run Lifecycle' ? (
            <section id="run-lifecycle" aria-labelledby="run-lifecycle-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="run-lifecycle-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Run Lifecycle
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  Every proposed change becomes a governed review run with explicit states, transition requirements, decision branches, and preserved evidence.
                </p>
              </div>

              {/* TARGET callout */}
              <Callout type="target">
                This section describes the target run-state model. State names and transitions remain architectural requirements until the repository-backed backend implementation is available and verified.
              </Callout>

              {/* Primary Run State Flow */}
              <section className="space-y-3 my-8" aria-labelledby="state-flow-title">
                <h3 id="state-flow-title" className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  TARGET RUN STATE FLOW
                </h3>
                {/* Horizontal on md+, wrap/vertical on mobile */}
                <div className="flex flex-col md:flex-row md:items-center gap-1.5 md:gap-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px] overflow-x-auto">
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    RECEIVED
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    CONTEXT ASSEMBLED
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    RISK DECIDED
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    REMEDIATION PLANNED
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    VALIDATING
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    VALIDATED
                  </div>
                  <div className="text-center text-stone-400 font-bold md:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="flex-1 min-w-[100px] p-2 bg-white border border-stone-200 text-center font-bold text-stone-700 shadow-sm">
                    WRITTEN BACK
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  Some runs may close before reaching every state because of policy decisions, validation failures, unavailable dependencies, or disabled writeback configuration.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* State Definitions Subsection */}
              <section className="space-y-6" aria-labelledby="state-definitions-heading">
                <h3 id="state-definitions-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  State Definitions
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target run-state model is designed around seven explicit operational states:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* RECEIVED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">A. RECEIVED</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold">Entry requirement:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>proposed change accepted by the target intake boundary</li>
                      <li>input format available for normalization</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">Target responsibilities:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>capture the original submitted input</li>
                      <li>assign a run reference</li>
                      <li>normalize supported change metadata</li>
                      <li>reject unreadable or unsupported input</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold pt-1">Produces:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>Change Request artifact</li>
                      <li>intake result</li>
                      <li>source references</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-ink)] font-semibold pt-1">Exit condition: <span className="font-mono text-stone-600 font-normal">normalized Change Request is available</span></p>
                  </div>

                  {/* CONTEXT ASSEMBLED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">B. CONTEXT ASSEMBLED</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold">Entry requirement:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>normalized Change Request exists</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">Target responsibilities:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>request relevant configured DataHub metadata</li>
                      <li>assemble bounded context</li>
                      <li>apply configured redaction and allowlist rules</li>
                      <li>record context source references</li>
                      <li>report missing required context</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold pt-1">Produces:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>redacted Context Pack</li>
                      <li>context source references</li>
                      <li>redaction record</li>
                      <li>context warnings or failure reason</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-ink)] font-semibold pt-1">Exit condition: <span className="font-mono text-stone-600 font-normal">required context is assembled, or the stage closes with an explicit context failure</span></p>
                  </div>

                  {/* RISK DECIDED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">C. RISK DECIDED</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold">Entry requirement:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>Change Request and required Context Pack are available</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">Target responsibilities:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>evaluate deterministic policy and contract rules</li>
                      <li>identify affected assets</li>
                      <li>produce decision reasons</li>
                      <li>assign ALLOW, WARN, or BLOCK</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold pt-1">Produces:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>Risk Decision</li>
                      <li>affected asset references</li>
                      <li>referenced policy results</li>
                      <li>decision reasons</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-ink)] font-semibold pt-1">Exit condition: <span className="font-mono text-stone-600 font-normal">deterministic decision is recorded</span></p>
                  </div>

                  {/* REMEDIATION PLANNED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">D. REMEDIATION PLANNED</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold">Entry requirement:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>remediation is required or explicitly requested</li>
                      <li>configured policy permits remediation planning</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">Target responsibilities:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>prepare a redacted model request</li>
                      <li>request compatible remediation options</li>
                      <li>record assumptions and referenced context</li>
                      <li>preserve the generated proposal as advisory output</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold pt-1">Produces:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>Remediation Plan</li>
                      <li>assumptions</li>
                      <li>compatibility proposal</li>
                      <li>referenced context</li>
                    </ul>
                    <p className="text-xs text-stone-600 font-semibold pt-1 italic">
                      A remediation proposal does not remove a WARN or BLOCK decision by itself. The proposed change must be reevaluated and validated through configured policy gates.
                    </p>
                    <p className="text-xs text-[var(--color-riftless-ink)] font-semibold pt-1">Exit condition: <span className="font-mono text-stone-600 font-normal">proposal is available for review or validation planning</span></p>
                  </div>

                  {/* VALIDATING */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">E. VALIDATING</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold">Entry requirement:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>validation is authorized</li>
                      <li>proposed change or remediation is available</li>
                      <li>configured validators are selected</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">Target responsibilities:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>execute bounded validation commands</li>
                      <li>run configured SQLGlot analysis</li>
                      <li>run DuckDB fixtures when configured</li>
                      <li>run dbt compilation or tests when configured</li>
                      <li>preserve logs and intermediate results</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold pt-1">Produces:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>validation logs</li>
                      <li>test outcomes</li>
                      <li>environment details</li>
                      <li>failure reasons</li>
                      <li>artifact references</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-ink)] font-semibold pt-1">Exit condition: <span className="font-mono text-stone-600 font-normal">configured validators complete or the validation environment fails</span></p>
                  </div>

                  {/* VALIDATED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">F. VALIDATED</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold">Entry requirement:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>required configured validators completed successfully within the tested scope</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">Target responsibilities:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>assemble executable evidence</li>
                      <li>preserve commands, results, and artifact references</li>
                      <li>record the evaluated scope</li>
                      <li>record limitations and skipped validators when applicable</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold pt-1">Produces:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>Validation Bundle</li>
                      <li>validation outcome</li>
                      <li>tested-scope statement</li>
                      <li>artifact references</li>
                    </ul>
                    <p className="text-xs text-red-700 font-semibold pt-1">
                      Warning: A VALIDATED state means the configured validators passed within the recorded test scope. It is not a universal guarantee that no downstream failure can occur.
                    </p>
                    <p className="text-xs text-[var(--color-riftless-ink)] font-semibold pt-1">Exit condition: <span className="font-mono text-stone-600 font-normal">the validation outcome and tested scope are recorded. Advancing to writeback additionally requires the configured authorization state.</span></p>
                  </div>

                  {/* WRITTEN BACK */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3 md:col-span-2">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase">G. WRITTEN BACK</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold">Entry requirement:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>required authorization state is recorded</li>
                      <li>writeback is enabled and configured</li>
                      <li>decision and evidence references are available</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] border-t border-stone-100 pt-2 font-semibold">Target responsibilities:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>prepare the configured metadata update</li>
                      <li>persist permitted decision records</li>
                      <li>record writeback result or failure reason</li>
                      <li>preserve references required for later review</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] font-semibold pt-1">May produce:</p>
                    <ul className="list-disc pl-4 space-y-0.5 text-xs font-mono text-stone-700">
                      <li>risk tag</li>
                      <li>decision document</li>
                      <li>deprecation note</li>
                      <li>validation result</li>
                      <li>owner action</li>
                      <li>incident status</li>
                      <li>artifact references</li>
                    </ul>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] pt-1">
                      WRITTEN BACK is a target terminal state only when configured writeback is enabled and completes successfully.
                    </p>
                    <p className="text-xs text-[var(--color-riftless-ink)] font-semibold pt-1">Exit condition: <span className="font-mono text-stone-600 font-normal">configured writeback succeeds, or an explicit writeback failure is recorded</span></p>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* State Responsibility Table */}
              <section className="space-y-4" aria-labelledby="state-table-heading">
                <h3 id="state-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  State Responsibility Matrix
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The complete matrix of review run states, requirements, artifact bindings, and exit scenarios is detailed below:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="state-responsibility-matrix-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target run states, entry requirements, produced artifacts, and exit conditions.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">State</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Entry Requirement</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Primary Responsibility</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Produces</th>
                        <th scope="col" className="px-4 py-3">Exit Condition</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RECEIVED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Proposed change accepted by target intake; input available for normalization.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Capture submitted input, assign run ref, normalize change metadata, reject unsupported.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Change Request, intake result, source refs.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Normalized Change Request is available.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTEXT ASSEMBLED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Normalized Change Request exists.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Request DataHub metadata, assemble context, apply redaction/allowlist, log warnings.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Redacted Context Pack, context source references, redaction record.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Required context is assembled or explicit failure.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK DECIDED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Change Request and Context Pack available.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Evaluate deterministic policy, identify affected assets, assign ALLOW/WARN/BLOCK status.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Risk Decision, asset refs, policy results, reasons.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Deterministic decision is recorded.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REMEDIATION PLANNED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Remediation required or requested; policy permits planning.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Prepare redacted request, query model for compatibility options, record assumptions.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Remediation Plan, assumptions, compatibility proposal.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Proposal is available for review or validation planning.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATING</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Validation authorized; change/remediation and validators selected.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Execute validation commands, run SQLGlot, run DuckDB fixtures, or dbt tests.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Validation logs, test outcomes, environment logs, failure details.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Validators complete or execution environment fails.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required configured validators complete successfully in scope.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Assemble evidence bundle, preserve results, record scope boundaries, note skipped tools.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Validation Bundle, validation outcome, tested-scope statement.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">the validation outcome and tested scope are recorded. Advancing to writeback additionally requires the configured authorization state.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITTEN BACK</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required authorization recorded, enabled, and references available.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Prepare configured metadata updates, write decision to catalog, preserve references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-500 font-mono text-[11px] align-top">Risk tag, decision document, validation results, owner actions.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Configured writeback succeeds or explicit failure recorded.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Risk Decision Branches */}
              <section className="space-y-4" aria-labelledby="risk-branches-heading">
                <h3 id="risk-branches-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Risk Decision Branches
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  During policy evaluation, three deterministic decision branches govern whether the change is allowed to advance:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl">
                  {/* ALLOW */}
                  <div className="border border-stone-200 rounded p-4 bg-stone-50/20 border-t-4 border-[#A8CD16]">
                    <span className="text-xs font-mono font-bold text-[#A8CD16] tracking-wider uppercase block mb-1">ALLOW</span>
                    <p className="text-[11px] font-mono text-stone-500 mb-2">
                      No configured blocking rule was triggered within the evaluated scope.
                    </p>
                    <p className="text-xs text-stone-700 leading-relaxed font-semibold">Target behavior:</p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>run may advance according to configured policy</li>
                      <li>remediation may be skipped when not required</li>
                      <li>required validation must still occur where configured</li>
                    </ul>
                  </div>

                  {/* WARN */}
                  <div className="border border-stone-200 rounded p-4 bg-stone-50/20 border-t-4 border-[#F2A93B]">
                    <span className="text-xs font-mono font-bold text-[#F2A93B] tracking-wider uppercase block mb-1">WARN</span>
                    <p className="text-[11px] font-mono text-stone-500 mb-2">
                      Identified impact requires acknowledgment or human review.
                    </p>
                    <p className="text-xs text-stone-700 leading-relaxed font-semibold">Target behavior:</p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>run pauses before protected later stages</li>
                      <li>reasons and affected assets remain visible</li>
                      <li>acknowledgment or policy-defined review is required</li>
                      <li>remediation may be proposed</li>
                      <li>warning does not automatically become approval</li>
                    </ul>
                  </div>

                  {/* BLOCK */}
                  <div className="border border-stone-200 rounded p-4 bg-stone-50/20 border-t-4 border-red-500">
                    <span className="text-xs font-mono font-bold text-red-600 tracking-wider uppercase block mb-1">BLOCK</span>
                    <p className="text-[11px] font-mono text-stone-500 mb-2">
                      A configured policy or contract rule prevents the run from advancing.
                    </p>
                    <p className="text-xs text-stone-700 leading-relaxed font-semibold">Target behavior:</p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>run cannot advance to validation or writeback</li>
                      <li>remediation proposal may be generated when configured</li>
                      <li>the change must be revised or reevaluated</li>
                      <li>model output cannot clear the block</li>
                      <li>only a new deterministic evaluation can produce a different decision</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Validation Failure Path */}
              <section className="space-y-4" aria-labelledby="val-failure-heading">
                <h3 id="val-failure-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validation Failure Path
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target trust model treats validation failures as distinct non-advancing branches:
                </p>

                {/* Static Flow */}
                <div className="flex flex-col sm:flex-row sm:items-center gap-1 bg-red-50/5 border border-red-200/40 p-3 rounded font-mono text-[9px] max-w-xl">
                  <div className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-stone-600">VALIDATING</div>
                  <div className="text-center text-red-400 font-bold sm:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-red-100 border border-red-200 text-red-700 rounded font-bold uppercase tracking-wider text-[8px]">VALIDATION FAILED</div>
                  <div className="text-center text-red-400 font-bold sm:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-stone-600">ARTIFACTS PRESERVED</div>
                  <div className="text-center text-red-400 font-bold sm:rotate-0 rotate-90" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 rounded font-bold text-stone-600">REVIEW REQUIRED OR RUN CLOSED</div>
                </div>

                <div className="space-y-2 text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl">
                  <p>When a configured validator fails:</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs text-stone-600">
                    <li>the run must not enter VALIDATED</li>
                    <li>writeback must not represent the proposal as verified</li>
                    <li>completed logs and test results should remain referenced</li>
                    <li>the failure reason should be recorded</li>
                    <li>policy may require human review, revision, or terminal closure</li>
                  </ul>
                  <p className="font-mono text-xs text-red-700 font-bold mt-2 uppercase">
                    FAILED EXECUTION DOES NOT ERASE PREVIOUSLY CAPTURED EVIDENCE.
                  </p>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Dependency Failure Behavior */}
              <section className="space-y-4" aria-labelledby="dep-failure-heading">
                <h3 id="dep-failure-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Dependency Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target lifecycle defines explicit non-advancing behavior when required integrations or execution environments are unavailable:
                </p>

                <div className="space-y-4 max-w-3xl font-mono text-xs">
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">DATAHUB READ UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>context assembly cannot complete when required metadata is unavailable</li>
                      <li>the run should stop or enter an explicit context-failure state</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">DEEPSEEK UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>no new remediation proposal is generated</li>
                      <li>deterministic risk results remain independent of model availability</li>
                      <li>the run may continue only when remediation is not required by policy</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">VALIDATION ENVIRONMENT UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>the run must not be marked validated</li>
                      <li>available pre-validation artifacts should remain referenced</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">DATAHUB WRITEBACK UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>the decision must not be reported as written back</li>
                      <li>the writeback failure reason should be recorded</li>
                      <li>decision and evidence references may remain available for target retry handling</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Run Artifact Trail */}
              <section className="space-y-4" aria-labelledby="artifact-trail-heading">
                <h3 id="artifact-trail-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Run Artifact Trail
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A target run may produce the following traceable artifact chain, depending on its decision path and enabled capabilities:
                </p>

                {/* Static chain */}
                <div className="flex flex-wrap items-center gap-1.5 bg-stone-100/40 border border-stone-200 p-4 rounded font-mono text-[9px] max-w-3xl overflow-x-auto">
                  <div className="px-2 py-1 bg-white border border-stone-200 text-stone-700 shadow-sm font-bold">INPUT DIFF</div>
                  <div className="text-stone-400 font-bold" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 text-stone-700 shadow-sm font-bold">CHANGE REQUEST</div>
                  <div className="text-stone-400 font-bold" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 text-stone-700 shadow-sm font-bold">CONTEXT PACK</div>
                  <div className="text-stone-400 font-bold" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 text-stone-700 shadow-sm font-bold">RISK DECISION</div>
                  <div className="text-stone-400 font-bold" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 text-stone-700 shadow-sm font-bold">REMEDIATION PLAN</div>
                  <div className="text-stone-400 font-bold" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 text-stone-700 shadow-sm font-bold">VALIDATION LOG</div>
                  <div className="text-stone-400 font-bold" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 text-stone-700 shadow-sm font-bold">VALIDATION BUNDLE</div>
                  <div className="text-stone-400 font-bold" aria-hidden="true">→</div>
                  <div className="px-2 py-1 bg-white border border-stone-200 text-stone-700 shadow-sm font-bold">WRITEBACK RECORD</div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
                  Not every run produces every artifact. For example, an ALLOW decision may not require remediation, while a failed validation run may never produce a successful Writeback Record.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl font-mono text-xs pt-2">
                  <div className="p-3 border border-stone-200 rounded">
                    <span className="font-bold text-stone-800">INPUT DIFF:</span> Original proposed change.
                  </div>
                  <div className="p-3 border border-stone-200 rounded">
                    <span className="font-bold text-stone-800">CHANGE REQUEST:</span> Normalized review input.
                  </div>
                  <div className="p-3 border border-stone-200 rounded">
                    <span className="font-bold text-stone-800">CONTEXT PACK:</span> Bounded and redacted organizational context.
                  </div>
                  <div className="p-3 border border-stone-200 rounded">
                    <span className="font-bold text-stone-800">RISK DECISION:</span> Deterministic status, reasons, and affected assets.
                  </div>
                  <div className="p-3 border border-stone-200 rounded">
                    <span className="font-bold text-stone-800">REMEDIATION PLAN:</span> Advisory compatibility proposal and assumptions.
                  </div>
                  <div className="p-3 border border-stone-200 rounded">
                    <span className="font-bold text-stone-800">VALIDATION LOG:</span> Executed commands, outputs, and failure details.
                  </div>
                  <div className="p-3 border border-stone-200 rounded">
                    <span className="font-bold text-stone-800">VALIDATION BUNDLE:</span> Recorded executable evidence within the tested scope.
                  </div>
                  <div className="p-3 border border-stone-200 rounded">
                    <span className="font-bold text-stone-800">WRITEBACK RECORD:</span> Configured metadata update produced after authorization.
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Transition Rules */}
              <section className="space-y-4" aria-labelledby="transition-rules-heading">
                <h3 id="transition-rules-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Transition Rules
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  State transitions must obey these rigid operational axioms:
                </p>

                <ul className="list-disc pl-5 space-y-2 text-xs text-stone-700 font-mono leading-relaxed max-w-2xl">
                  <li>a state transition must have an explicit predecessor</li>
                  <li>model output cannot advance run state by itself</li>
                  <li>deterministic policy gates control protected transitions</li>
                  <li>validation cannot be skipped when required by configured policy</li>
                  <li>a failed validator cannot produce VALIDATED</li>
                  <li>writeback requires recorded authorization</li>
                  <li>missing required context prevents risk evaluation</li>
                  <li>later-stage failure does not retroactively erase earlier artifacts</li>
                  <li>state and failure reasons should remain explainable</li>
                </ul>

                <Callout type="target">
                  A run state should never be inferred solely from UI presentation. The backend record must remain the source of truth once the run-state implementation exists.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Lifecycle Invariants */}
              <section className="space-y-4" aria-labelledby="lifecycle-invariants-heading">
                <h3 id="lifecycle-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Run Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target run-state architecture requires that these fundamental invariants are preserved:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">INPUTS REMAIN REFERENCED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">DECISIONS REMAIN EXPLAINABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS ADVISORY.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION REMAINS SCOPE-BOUND.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK REMAINS AUTHORIZED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">FAILURE REMAINS AUDITABLE.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe target requirements, not proof that persistent lifecycle enforcement has already been implemented.
                </p>
              </section>
            </section>
          ) : activeSection === 'DataHub' ? (
            <section id="datahub" aria-labelledby="datahub-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="datahub-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  DataHub Integration
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  DataHub provides the target metadata context used to evaluate downstream impact and the organizational destination used to preserve authorized review outcomes.
                </p>
              </div>

              {/* TARGET callout */}
              <Callout type="target">
                This section describes the target DataHub integration contract. Read operations, writeback behavior, metadata mappings, and configuration remain illustrative until implemented and verified against a repository-backed integration.
              </Callout>

              {/* Integration Role Subsection */}
              <section className="space-y-6" aria-labelledby="integration-role-heading">
                <h3 id="integration-role-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Integration Role
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target DataHub integration performs two primary roles within the RIFTLESS architecture to coordinate change metadata:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* READ CONTEXT */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase text-[var(--color-riftless-ink)]">Read Context</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      The target integration may retrieve relevant metadata needed to assemble a bounded Context Pack.
                    </p>
                    <p className="text-xs font-mono font-bold text-stone-500 uppercase tracking-wider">Target metadata categories:</p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 font-mono">
                      <li>schema definitions</li>
                      <li>column lineage</li>
                      <li>observed query usage</li>
                      <li>ownership metadata</li>
                      <li>governance tags</li>
                      <li>quality signals</li>
                      <li>declared ML dependencies</li>
                      <li>existing deprecation or incident context when available</li>
                    </ul>
                  </div>

                  {/* WRITE ORGANIZATIONAL MEMORY */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase text-[var(--color-riftless-ink)]">Write Organizational Memory</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      After authorization, the target integration may persist permitted review outcomes and references back to configured DataHub metadata.
                    </p>
                    <p className="text-xs font-mono font-bold text-stone-500 uppercase tracking-wider">Target writeback categories:</p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 font-mono">
                      <li>risk tag</li>
                      <li>decision document</li>
                      <li>deprecation note</li>
                      <li>owner action</li>
                      <li>validation result</li>
                      <li>incident status</li>
                      <li>artifact references</li>
                    </ul>
                  </div>
                </div>

                <div className="p-4 bg-stone-50 border border-stone-200 rounded max-w-4xl text-xs text-stone-700 leading-relaxed font-semibold">
                  DataHub supplies organizational context and stores permitted records. It does not authorize the risk decision.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Static DataHub Loop Flow */}
              <section className="space-y-4" aria-labelledby="context-loop-heading">
                <h3 id="context-loop-heading" className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  TARGET DATAHUB CONTEXT LOOP
                </h3>

                {/* Desktop Loop Diagram */}
                <div className="hidden md:block bg-stone-100/60 border border-stone-200 p-5 rounded font-mono text-[9px] max-w-4xl">
                  {/* Two rows showing circular loop */}
                  <div className="grid grid-cols-7 items-center text-center gap-1">
                    {/* Read Path row */}
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded">
                      DATAHUB METADATA
                    </div>
                    <div className="text-stone-400 font-bold">→ [READ]</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded">
                      CONTEXT REFERENCES
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded">
                      REDACTED CONTEXT PACK
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded">
                      DETERMINISTIC REVIEW
                    </div>

                    {/* Bridge Down */}
                    <div className="col-span-7 h-4 flex items-center justify-end pr-10">
                      <span className="text-stone-400 font-bold">↓</span>
                    </div>

                    {/* Writeback Path row reverse */}
                    <div className="p-2 bg-stone-50 border border-stone-200 text-stone-400 font-bold rounded">
                      DATAHUB METADATA
                    </div>
                    <div className="text-[#A8CD16] font-bold">← [WRITEBACK]</div>
                    <div className="p-2 bg-white border border-[#A8CD16] text-[#A8CD16] font-bold shadow-sm rounded">
                      AUTHORIZED WRITEBACK
                    </div>
                    <div className="text-stone-400 font-bold">←</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded">
                      VALIDATION OUTCOME
                    </div>
                    <div className="col-span-2"></div>
                  </div>

                  <div className="flex items-center justify-between mt-4 pt-3 border-t border-stone-200/60 text-[9px] text-stone-500">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-stone-400 rounded-full" />
                      <span>READ PATH</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-[#A8CD16] rounded-full" />
                      <span className="font-bold text-[#A8CD16]">WRITEBACK PATH</span>
                    </div>
                  </div>
                </div>

                {/* Mobile Loop Sequence */}
                <div className="md:hidden space-y-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px]">
                  <div className="text-[8px] font-bold text-stone-400 uppercase tracking-wider mb-2">READ PATH</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    DATAHUB METADATA
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    CONTEXT REFERENCES
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    REDACTED CONTEXT PACK
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    DETERMINISTIC REVIEW
                  </div>
                  
                  <div className="text-[8px] font-bold text-[#A8CD16] uppercase tracking-wider mt-4 mb-2">WRITEBACK PATH</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    VALIDATION OUTCOME
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-[#A8CD16] text-[#A8CD16] font-bold shadow-sm text-center">
                    AUTHORIZED WRITEBACK
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-stone-50 border border-stone-200 text-stone-400 font-bold text-center">
                    DATAHUB METADATA (ORGANIZATIONAL MEMORY)
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Context Read Path Subsection */}
              <section className="space-y-4" aria-labelledby="read-path-heading">
                <h3 id="read-path-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Context Read Path
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target metadata assembly progresses through the following sequential stages:
                </p>

                <ol className="list-decimal pl-5 space-y-2 text-xs text-stone-700 font-mono leading-relaxed max-w-2xl">
                  <li><strong>CHANGE REQUEST IDENTIFIED:</strong> A proposed change is evaluated against the target workspace.</li>
                  <li><strong>RELEVANT ASSETS RESOLVED:</strong> The specific datasets, schemas, and pipelines affected by the change are located.</li>
                  <li><strong>CONFIGURED METADATA REQUESTED:</strong> Only declared metadata categories are retrieved from the catalog.</li>
                  <li><strong>RESPONSE REFERENCES RECORDED:</strong> Available catalog source references and relevant version information should be recorded with the run context.</li>
                  <li><strong>VALUES FILTERED THROUGH REDACTION AND ALLOWLIST RULES:</strong> Configured redaction and allowlist rules must remove or reject prohibited values.</li>
                  <li><strong>CONTEXT PACK ASSEMBLED:</strong> Context Pack input is assembled from bounded metadata permitted by the configured rules.</li>
                </ol>

                <div className="space-y-2 text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl pt-2">
                  <p>Read path constraints:</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs text-stone-600">
                    <li>metadata should be requested only when relevant to the proposed change</li>
                    <li>missing optional metadata may produce a context warning</li>
                    <li>missing required metadata may prevent risk evaluation</li>
                    <li>retrieved metadata must retain source references</li>
                    <li>credentials and prohibited values must not enter model context</li>
                    <li>more metadata does not automatically produce a better decision</li>
                  </ul>
                </div>

                <Callout type="note">
                  A Context Pack should remain bounded to the assets, relationships, policies, and operational signals relevant to the evaluated change.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Context Mapping Table */}
              <section className="space-y-4" aria-labelledby="mapping-table-heading">
                <h3 id="mapping-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Context Mapping Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The relationship between raw DataHub metadata categories and their corresponding roles inside the RIFTLESS Context Pack:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="context-mapping-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target DataHub metadata categories and their role in the RIFTLESS Context Pack.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Metadata Category</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Review Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Target Context Output</th>
                        <th scope="col" className="px-4 py-3">Required or Conditional</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">SCHEMA DEFINITIONS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Understand current fields, types, and structural relationships.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Relevant schema references and affected field definitions.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required when structural compatibility is evaluated.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">COLUMN LINEAGE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify downstream dependencies and propagation paths.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Relevant upstream and downstream asset references.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional on availability and evaluated change type.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">QUERY USAGE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Understand observed operational references to affected assets.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Bounded usage references or aggregate signals.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">OWNERSHIP</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify accountable technical or business owners.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Relevant owner references.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional, but may be required by policy.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">GOVERNANCE TAGS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Apply configured handling or review requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Relevant policy and classification references.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required when referenced by configured policy.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">QUALITY SIGNALS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide recent context about known data-quality conditions.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Relevant quality status references.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ML DEPENDENCIES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify declared model or feature dependencies.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Relevant dependency references.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional on availability.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Model-Context Redaction Subsection */}
              <section className="space-y-4" aria-labelledby="boundary-heading">
                <h3 id="boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  DataHub-to-Model Boundary
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Data integration schemas are partitioned into bounded context and server-side secret boundaries before any AI generation is requested:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* MAY ENTER THE REDACTED CONTEXT PACK */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-[#A8CD16] tracking-wider uppercase">MAY ENTER THE REDACTED CONTEXT PACK</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>relevant schema references</li>
                      <li>bounded lineage references</li>
                      <li>required ownership metadata</li>
                      <li>configured governance constraints</li>
                      <li>relevant quality signals</li>
                      <li>declared dependency references</li>
                      <li>source references required for explanation</li>
                    </ul>
                  </div>

                  {/* MUST REMAIN SERVER-SIDE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-600 tracking-wider uppercase">MUST REMAIN SERVER-SIDE</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>DataHub credentials</li>
                      <li>raw authorization headers</li>
                      <li>secret environment values</li>
                      <li>unrestricted metadata exports</li>
                      <li>unrelated sensitive metadata</li>
                      <li>internal authorization records</li>
                      <li>unrestricted raw logs</li>
                    </ul>
                  </div>
                </div>

                <Callout type="warning">
                  Metadata origin does not make a value safe for model context. Configured redaction and allowlist rules must evaluate the value before request assembly.
                </Callout>

                <Callout type="note">
                  Runtime tests must verify that prohibited values are removed or rejected before any model request is sent.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Target DataHub Client Boundary Subsection */}
              <section className="space-y-4" aria-labelledby="client-resp-heading">
                <h3 id="client-resp-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Client Responsibilities
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target DataHub client adapter is responsible for coordinating configured server-side metadata operations:
                </p>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl">
                  <li>establish a configured server-side connection</li>
                  <li>request only required metadata</li>
                  <li>normalize returned references</li>
                  <li>preserve request and source references without storing secrets</li>
                  <li>surface unavailable or incomplete metadata</li>
                  <li>prepare permitted writeback operations</li>
                  <li>record writeback success or failure</li>
                  <li>avoid exposing credentials to browser code or model context</li>
                </ul>

                <p className="text-xs text-stone-600 leading-relaxed max-w-2xl italic font-semibold">
                  The target DataHub client acts as an integration adapter. It does not evaluate risk, authorize validation, or approve writeback independently.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Non-Executable Operation Shapes Subsection */}
              <section className="space-y-4" aria-labelledby="shapes-heading">
                <h3 id="shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Operation Shapes
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Illustrative interface specifications for metadata synchronization routines:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* Block 1 */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL READ OPERATION <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`resolve relevant asset references
request configured metadata categories
record source references
apply redaction and allowlist rules
return bounded Context Pack input`}
                    </pre>
                  </div>

                  {/* Block 2 */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL WRITEBACK OPERATION <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive recorded authorization
receive decision and validation references
prepare permitted metadata updates
submit configured writeback
record success or failure`}
                    </pre>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] italic">
                  Exact DataHub operations, request formats, and field mappings will be documented after the integration client is implemented and versioned.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Writeback Contract Subsection */}
              <section className="space-y-4" aria-labelledby="writeback-contract-heading">
                <h3 id="writeback-contract-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Authorized Writeback Contract
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract permits a configured metadata update only when the following conditions are satisfied:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  <div className="space-y-3">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">Entry requirements:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 leading-relaxed">
                      <li>control-plane authorization is recorded</li>
                      <li>decision status and reasons are available</li>
                      <li>validation outcome is available where required</li>
                      <li>relevant artifact references are available</li>
                      <li>writeback is enabled and configured</li>
                      <li>prohibited secret values are excluded</li>
                    </ul>

                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase pt-2">Target behavior:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 leading-relaxed">
                      <li>persist only permitted metadata fields</li>
                      <li>preserve association with the reviewed asset</li>
                      <li>record the writeback outcome</li>
                      <li>report rejected or unavailable writeback operations</li>
                      <li>avoid representing advisory model output as verified evidence</li>
                    </ul>
                  </div>

                  <div className="bg-red-50/20 border border-red-200/60 rounded p-5 space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-700 uppercase">Writeback must not proceed when:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 leading-relaxed">
                      <li>authorization is missing</li>
                      <li>a required validation has failed</li>
                      <li>the decision remains BLOCK</li>
                      <li>writeback configuration is disabled</li>
                      <li>required target mapping is unavailable</li>
                      <li>the requested record contains prohibited values</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Writeback Mapping Table */}
              <section className="space-y-4" aria-labelledby="writeback-table-heading">
                <h3 id="writeback-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Writeback Mapping Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target integration may associate RIFTLESS review outcomes with configured DataHub metadata destinations as described conceptually below:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="writeback-mapping-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target RIFTLESS review outcomes and their conceptual DataHub writeback purpose.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Review Record</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Required Inputs</th>
                        <th scope="col" className="px-4 py-3">Write Condition</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK TAG</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Expose the recorded review risk status.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Risk Decision and affected asset reference.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Recorded authorization and configured mapping.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DECISION DOCUMENT</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Preserve decision reasons, evaluated scope, and referenced policy results.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Risk Decision, reasons, and context references.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Recorded authorization.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DEPRECATION NOTE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record a staged compatibility or removal plan.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Authorized remediation or owner-approved deprecation plan.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Relevant approved decision path.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">OWNER ACTION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record required human follow-up.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Owner reference, required action, and decision reason.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Configured owner-action mapping.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION RESULT</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Preserve the validation outcome and artifact references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Validation Bundle or recorded failure result.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Configured validation writeback mapping.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">INCIDENT STATUS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record a relevant operational failure or blocked condition.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Failure reason and affected asset reference.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Configured incident mapping.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACT REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Link the decision record to preserved run evidence.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Artifact identifiers or storage references.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">References are permitted and do not contain secrets.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* DataHub Failure Behavior Subsection */}
              <section className="space-y-4" aria-labelledby="datahub-failure-heading-2">
                <h3 id="datahub-failure-heading-2" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  DataHub Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target integration defines explicit non-success behavior when DataHub reads, filtering, mappings, or writeback operations cannot complete:
                </p>

                <div className="space-y-4 max-w-3xl font-mono text-xs">
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">DATAHUB READ UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>required context cannot be assembled</li>
                      <li>risk evaluation must not proceed when required metadata is missing</li>
                      <li>context failure reason should be recorded</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">PARTIAL METADATA RESPONSE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>available references may be preserved</li>
                      <li>missing categories should be identified</li>
                      <li>configured policy determines whether the run may continue</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">REDACTION OR ALLOWLIST FAILURE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>model request must not be sent</li>
                      <li>prohibited values must not be silently accepted</li>
                      <li>failure reason should be recorded</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">WRITEBACK UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>decision must not be reported as written back</li>
                      <li>writeback failure reason should be recorded</li>
                      <li>decision and evidence references may remain available for target retry handling</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">WRITEBACK REJECTED:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>rejected fields or target mapping should be identified when available</li>
                      <li>no success status should be recorded</li>
                      <li>the original authorization record remains distinct from writeback success</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Target Configuration Areas Subsection */}
              <section className="space-y-4" aria-labelledby="config-heading">
                <h3 id="config-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Configuration Areas
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Core properties configured under target execution boundaries:
                </p>

                <div className="space-y-2 max-w-xl">
                  <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                    ILLUSTRATIVE CONFIGURATION GROUPS <span className="text-stone-400 font-normal">(NON-EXECUTABLE)</span>
                  </span>
                  <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`# Illustrative configuration shape only.
# This is not yet the repository-backed schema.

datahub:
  connection: "<configured-server-side-connection>"
  read_scope: "<configured-metadata-scope>"
  metadata_categories:
    - "<configured-category>"

  writeback:
    enabled: "<configured-boolean>"
    mappings: "<configured-writeback-mappings>"

redaction:
  policy: "<configured-redaction-policy>"`}
                  </pre>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* DataHub Invariants Subsection */}
              <section className="space-y-4" aria-labelledby="invariants-heading">
                <h3 id="invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  DataHub Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target DataHub contract defines the following integration invariants:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">CONTEXT REMAINS BOUNDED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">SOURCE REFERENCES REMAIN TRACEABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN SERVER-SIDE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">RISK AUTHORITY REMAINS DETERMINISTIC.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK REMAINS AUTHORIZED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK SUCCESS REMAINS EXPLICIT.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe target integration requirements, not proof that the DataHub client or writeback adapter has already been implemented.
                </p>
              </section>
            </section>
          ) : activeSection === 'GitHub' ? (
            <section id="github" aria-labelledby="github-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="github-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  GitHub Integration
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  GitHub provides the target repository context for proposed changes and a review surface for communicating recorded RIFTLESS decisions and evidence references.
                </p>
              </div>

              {/* TARGET callout */}
              <Callout type="target">
                This section describes the target GitHub integration contract. Repository event handling, permissions, review annotations, and status reporting remain illustrative until a repository-backed integration is implemented and verified.
              </Callout>

              {/* Integration Role Subsection */}
              <section className="space-y-6" aria-labelledby="github-role-heading">
                <h3 id="github-role-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Integration Role
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target integration performs two primary roles within the RIFTLESS architecture to coordinate change metadata:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* CHANGE INTAKE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase text-[var(--color-riftless-ink)]">Change Intake</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      The target integration may identify a proposed data change from a configured repository event or explicitly submitted repository reference.
                    </p>
                    <p className="text-xs font-mono font-bold text-stone-500 uppercase tracking-wider">Target intake context may include:</p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 font-mono">
                      <li>repository reference</li>
                      <li>pull request reference</li>
                      <li>base and head revision references</li>
                      <li>changed file references</li>
                      <li>relevant diff content</li>
                      <li>author or actor reference when permitted</li>
                      <li>target branch reference</li>
                      <li>repository metadata required by configured policy</li>
                    </ul>
                  </div>

                  {/* REVIEW REPORTING */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase text-[var(--color-riftless-ink)]">Review Reporting</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      After the required decision and validation states are recorded, the target integration may report permitted review information back to the configured GitHub review surface.
                    </p>
                    <p className="text-xs font-mono font-bold text-stone-500 uppercase tracking-wider">Target reporting information may include:</p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 font-mono">
                      <li>review status</li>
                      <li>risk decision</li>
                      <li>concise decision reasons</li>
                      <li>affected asset references</li>
                      <li>validation outcome</li>
                      <li>remediation proposal reference when applicable</li>
                      <li>artifact references</li>
                      <li>required human action</li>
                      <li>writeback status when relevant</li>
                    </ul>
                  </div>
                </div>

                <div className="p-4 bg-stone-50 border border-stone-200 rounded max-w-4xl text-xs text-stone-700 leading-relaxed font-semibold">
                  GitHub supplies repository context and displays permitted review results. It does not authorize the risk decision or validation outcome.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Static GitHub Review Flow */}
              <section className="space-y-4" aria-labelledby="github-flow-heading">
                <h3 id="github-flow-heading" className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  TARGET GITHUB REVIEW FLOW
                </h3>

                {/* Desktop Loop Diagram */}
                <div className="hidden md:block bg-stone-100/60 border border-stone-200 p-5 rounded font-mono text-[9px] max-w-4xl">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      REPOSITORY CHANGE
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      CHANGE INTAKE
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      NORMALIZED CHANGE REQUEST
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-amber-200 text-[#F2A93B] font-bold shadow-sm rounded text-center">
                      CONTEXT AND RISK REVIEW
                      <span className="block text-[8px] text-stone-400 font-normal uppercase mt-0.5">[REVIEW REQUIRED]</span>
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-lime-200 text-[#A8CD16] font-bold shadow-sm rounded text-center">
                      VALIDATION OUTCOME
                      <span className="block text-[8px] text-[#A8CD16] font-bold uppercase mt-0.5">[SUCCESSFUL]</span>
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      AUTHORIZED REVIEW RESULT
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      GITHUB REVIEW SURFACE
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between mt-4 pt-3 border-t border-stone-200/60 text-[9px] text-stone-500 gap-4">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-stone-400 rounded-full" />
                      <span>REPOSITORY & REVIEW PATH</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-[#A8CD16] rounded-full" />
                      <span className="font-bold text-[#A8CD16]">SUCCESSFUL VALIDATION/RESULT</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-[#F2A93B] rounded-full" />
                      <span className="font-bold text-[#F2A93B]">REVIEW REQUIRED</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-red-500 rounded-full" />
                      <span className="font-bold text-red-600">BLOCKED DECISION</span>
                    </div>
                  </div>
                </div>

                {/* Mobile Loop Sequence */}
                <div className="md:hidden space-y-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px]">
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    REPOSITORY CHANGE
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    CHANGE INTAKE
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    NORMALIZED CHANGE REQUEST
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-[#F2A93B] text-[#F2A93B] font-bold shadow-sm text-center">
                    CONTEXT AND RISK REVIEW
                    <span className="block text-[8px] text-stone-400 font-normal uppercase mt-0.5">[REVIEW REQUIRED]</span>
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    VALIDATION OUTCOME
                    <span className="block text-[8px] text-[#A8CD16] font-bold uppercase mt-0.5">[SUCCESSFUL]</span>
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    AUTHORIZED REVIEW RESULT
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    GITHUB REVIEW SURFACE
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Change Intake Path Subsection */}
              <section className="space-y-4" aria-labelledby="intake-path-heading">
                <h3 id="intake-path-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Change Intake Path
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target repository change intake progresses through the following sequential stages:
                </p>

                <ol className="list-decimal pl-5 space-y-2 text-xs text-stone-700 font-mono leading-relaxed max-w-2xl">
                  <li><strong>REPOSITORY REFERENCE RECEIVED:</strong> A proposed repository event or explicit reference is received by the target intake boundary.</li>
                  <li><strong>CONFIGURED CHANGE SCOPE IDENTIFIED:</strong> The target workspace determines the scope of evaluation based on config rules.</li>
                  <li><strong>RELEVANT FILE REFERENCES RESOLVED:</strong> Specific files related to schema, pipeline, or configuration changes are identified.</li>
                  <li><strong>DIFF CONTENT BOUNDED:</strong> The textual diff is extracted within size and semantic limits.</li>
                  <li><strong>PROHIBITED VALUES EXCLUDED:</strong> Credentials, secrets, and unsupported content are filtered out.</li>
                  <li><strong>CHANGE REQUEST NORMALIZED:</strong> A normalized Change Request is assembled from the permitted repository inputs.</li>
                  <li><strong>SOURCE REFERENCES RECORDED:</strong> Repository origin, available revision identifiers, and relevant change references should be recorded with the run context.</li>
                </ol>

                <div className="space-y-2 text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl pt-2">
                  <p>Intake path constraints and requirements:</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs text-stone-600">
                    <li>only configured repositories and scopes should be processed</li>
                    <li>unrelated files should not automatically enter the review context</li>
                    <li>the original repository and revision references should remain associated with the run</li>
                    <li>unreadable or unsupported changes should produce an explicit intake failure</li>
                    <li>repository credentials must remain server-side</li>
                    <li>secret-bearing file content must not automatically enter model context</li>
                    <li>repository content should be bounded to the evaluated change</li>
                  </ul>
                </div>

                <Callout type="note">
                  A repository diff is an input to the review. It is not sufficient by itself to describe downstream impact.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Intake Mapping Table */}
              <section className="space-y-4" aria-labelledby="intake-mapping-heading">
                <h3 id="intake-mapping-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Intake Mapping Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The relationship between raw repository inputs and their corresponding roles in the RIFTLESS Change Request:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="intake-mapping-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target GitHub repository inputs and their role in a normalized RIFTLESS Change Request.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Repository Input</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Review Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Target Change Request Output</th>
                        <th scope="col" className="px-4 py-3">Required or Conditional</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REPOSITORY REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify the configured source repository.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Repository source reference.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PULL REQUEST REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Associate the review with a proposed repository change.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Pull request reference when applicable.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional on intake method.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">BASE AND HEAD REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define the compared revision boundary.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Source revision references.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required for diff-based review.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CHANGED FILE REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify files relevant to the proposed change.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Bounded changed-file list.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required for repository diff review.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DIFF CONTENT</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Describe the proposed textual change.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Normalized change content and source locations.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required when the change is derived from a diff.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ACTOR REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide permitted ownership or review context.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Actor reference when available and allowed.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">TARGET BRANCH REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Apply configured repository or policy scope.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Branch or environment reference.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional on policy.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Repository-Context Boundary Subsection */}
              <section className="space-y-4" aria-labelledby="github-boundary-heading">
                <h3 id="github-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Repository-Context Boundary
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Repository data is partitioned into bounded change request structures and server-side secret boundaries before any model analysis is requested:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* MAY ENTER THE CHANGE REQUEST */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-[#A8CD16] tracking-wider uppercase">MAY ENTER THE CHANGE REQUEST</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>bounded repository reference</li>
                      <li>pull request reference</li>
                      <li>base and head revision references</li>
                      <li>relevant changed-file references</li>
                      <li>relevant diff content</li>
                      <li>permitted actor reference</li>
                      <li>configured branch or policy reference</li>
                    </ul>
                  </div>

                  {/* MUST REMAIN SERVER-SIDE OR EXCLUDED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-600 tracking-wider uppercase">MUST REMAIN SERVER-SIDE OR EXCLUDED</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>GitHub credentials</li>
                      <li>raw authorization headers</li>
                      <li>unrelated repository files</li>
                      <li>secret environment files</li>
                      <li>private keys</li>
                      <li>tokens embedded in source</li>
                      <li>unrestricted repository exports</li>
                      <li>internal authorization records</li>
                      <li>unrelated personal data</li>
                    </ul>
                  </div>
                </div>

                <Callout type="warning">
                  Repository content is not automatically safe for model context. Configured file filters, secret detection, redaction, and allowlist rules must evaluate content before request assembly.
                </Callout>

                <Callout type="note">
                  Runtime tests should verify that prohibited files and values are rejected or removed before any repository-derived content is sent to a model.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Target Access Boundary Subsection */}
              <section className="space-y-4" aria-labelledby="access-boundary-heading">
                <h3 id="access-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Access Boundary
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target GitHub integration defines conceptual access boundaries. The exact authentication and permission model remains undecided until the adapter is implemented.
                </p>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl">
                  <li>repository access must be server-side</li>
                  <li>access should be limited to configured repositories and operations</li>
                  <li>read and reporting capabilities should remain independently configurable</li>
                  <li>the adapter should request only the access needed by enabled capabilities</li>
                  <li>browser code must not receive repository credentials</li>
                  <li>model context must not contain repository credentials</li>
                  <li>exact GitHub App, token, or installation model remains undecided until implemented</li>
                </ul>

                <Callout type="warning">
                  Do not document or request broad repository-write access merely to support change inspection. The final permission model must be derived from the implemented integration operations.
                </Callout>

                {/* Conceptual Access Table */}
                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="conceptual-access-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target capabilities and their corresponding conceptual repository access permissions and constraints.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Target Capability</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Conceptual Access</th>
                        <th scope="col" className="px-4 py-3">Constraint</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CHANGE INSPECTION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Read configured repository and revision information.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">No unrelated repository access.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DIFF RETRIEVAL</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Read bounded changed-file and diff content.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Content filtering and redaction required.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REVIEW REPORTING</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Write permitted review status or annotation.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Only when reporting is enabled and result data is authorized.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONFIGURATION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Resolve configured repository scope.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">No credential exposure to browser or model context.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Target Adapter Responsibilities Subsection */}
              <section className="space-y-4" aria-labelledby="github-adapter-heading">
                <h3 id="github-adapter-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Adapter Responsibilities
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target GitHub client adapter is responsible for coordinating repository access and reporting within the RIFTLESS architecture:
                </p>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl">
                  <li>establish configured server-side repository access</li>
                  <li>resolve permitted repository and revision references</li>
                  <li>retrieve only required diff and file information</li>
                  <li>normalize repository changes into a Change Request</li>
                  <li>preserve source references without storing credentials</li>
                  <li>report unavailable, stale, or incomplete repository data</li>
                  <li>prepare permitted review annotations or status updates</li>
                  <li>record reporting success or failure</li>
                  <li>avoid exposing credentials to browser code or model context</li>
                </ul>

                <p className="text-xs text-stone-600 leading-relaxed max-w-2xl italic font-semibold">
                  The target GitHub adapter transports repository context and permitted review results. It does not evaluate deterministic risk, authorize validation, or approve its own reporting outcome.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Target Operation Shapes Subsection */}
              <section className="space-y-4" aria-labelledby="github-shapes-heading">
                <h3 id="github-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Operation Shapes
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Illustrative interface specifications for repository change intake and review reporting operations:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* Block 1 */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL CHANGE INTAKE <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive configured repository reference
resolve proposed revision boundary
retrieve permitted changed-file references
retrieve bounded diff content
apply exclusion and redaction rules
return normalized Change Request input`}
                    </pre>
                  </div>

                  {/* Block 2 */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL REVIEW REPORTING <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive recorded review result
receive permitted decision and evidence references
prepare configured GitHub review output
submit permitted annotation or status
record reporting success or failure`}
                    </pre>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] italic">
                  Exact GitHub events, API operations, authentication approach, request formats, and review surfaces will be documented after the integration adapter is implemented and versioned.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* GitHub Review Result Contract Subsection */}
              <section className="space-y-4" aria-labelledby="review-contract-heading">
                <h3 id="review-contract-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  GitHub Review Result Contract
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target review reporting contract permits publishing review outcomes to GitHub only when the following conditions are satisfied:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  <div className="space-y-3">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">Entry requirements:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 leading-relaxed">
                      <li>repository or pull request reference is available</li>
                      <li>deterministic Risk Decision is recorded</li>
                      <li>decision reasons are available</li>
                      <li>affected asset references are available when identified</li>
                      <li>validation outcome is available where required</li>
                      <li>reporting is enabled and configured</li>
                      <li>prohibited secret values are excluded</li>
                    </ul>

                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase pt-2">Target review output may include:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 leading-relaxed">
                      <li>RIFTLESS review status</li>
                      <li>ALLOW, WARN, or BLOCK result</li>
                      <li>concise decision reasons</li>
                      <li>affected asset summary or references</li>
                      <li>configured policy references</li>
                      <li>validation outcome and tested scope</li>
                      <li>remediation proposal reference when applicable</li>
                      <li>required owner or reviewer action</li>
                      <li>permitted artifact links or references</li>
                    </ul>
                  </div>

                  <div className="bg-red-50/20 border border-red-200/60 rounded p-5 space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-700 uppercase">Target review output must not:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 leading-relaxed">
                      <li>expose credentials</li>
                      <li>expose unrestricted Context Pack content</li>
                      <li>expose unrestricted validation logs</li>
                      <li>describe advisory model output as authorization</li>
                      <li>describe a failed validation as successful</li>
                      <li>describe an unrecorded writeback as complete</li>
                      <li>reveal prohibited repository content</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Review Status Table */}
              <section className="space-y-4" aria-labelledby="status-table-heading">
                <h3 id="status-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Review Status Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The relationship between internal review outcomes and their reported GitHub status values:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="review-status-reporting-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Conceptual RIFTLESS review results that may be reported to a configured GitHub review surface.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Review Result</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Meaning</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Required Information</th>
                        <th scope="col" className="px-4 py-3">Permitted Repository Message</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REVIEW IN PROGRESS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">The target review has not reached a recorded final decision.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Run reference and current target stage when available.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Review is in progress; no approval is implied.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top font-bold text-stone-900">ALLOW</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">No configured blocking rule was triggered within the evaluated scope.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Decision reasons, evaluated scope, and required validation status.</td>
                        <td className="px-4 py-3 text-stone-600 align-top font-bold text-stone-900">Run may advance according to configured policy.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-[#F2A93B] bg-[#F2A93B]/5 text-left align-top">WARN</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Acknowledgment or human review is required.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Decision reasons, affected assets, and required action.</td>
                        <td className="px-4 py-3 text-[#F2A93B] align-top font-semibold">Review required before protected later stages.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-red-600 bg-red-50/10 text-left align-top">BLOCK</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A configured policy or contract rule prevents advancement.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Blocking reasons, affected assets, and applicable policy references.</td>
                        <td className="px-4 py-3 text-red-600 align-top font-semibold">Change cannot advance until revised and reevaluated.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-red-700 bg-red-50/5 text-left align-top">VALIDATION FAILED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-bold text-red-700">A configured validation step failed.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Failure summary, tested scope, and permitted artifact references.</td>
                        <td className="px-4 py-3 text-red-700 align-top">Validation did not complete successfully; verified status is not available.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-[#A8CD16] bg-lime-50/10 text-left align-top">VALIDATED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-bold text-[#A8CD16]">Configured validators passed within the recorded scope.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Validation outcome, tested scope, and artifact references.</td>
                        <td className="px-4 py-3 text-[#A8CD16] align-top font-bold">Configured validation passed within the recorded scope; this is not a universal safety guarantee.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-600 bg-stone-50/20 text-left align-top">REPORTING FAILED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">The GitHub review result could not be published.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Reporting failure reason when available.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">No successful GitHub reporting state may be recorded.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Revision Consistency Subsection */}
              <section className="space-y-4" aria-labelledby="revision-consistency-heading">
                <h3 id="revision-consistency-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Revision Consistency
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target repository contract defines the following revision-consistency requirements:
                </p>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl">
                  <li>the reviewed base and head references should remain recorded</li>
                  <li>a review result applies only to its evaluated revision boundary</li>
                  <li>a newer commit should not inherit a previous validation result automatically</li>
                  <li>changed repository content may require a new review run</li>
                  <li>reporting should distinguish current and stale results</li>
                  <li>artifact references should remain associated with the revision that produced them</li>
                </ul>

                <Callout type="target">
                  A review result should never be presented as current when the repository revision no longer matches the evaluated revision boundary.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* GitHub Failure Behavior Subsection */}
              <section className="space-y-4" aria-labelledby="github-failure-heading-3">
                <h3 id="github-failure-heading-3" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  GitHub Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Explicit target behaviors are defined for various repository integration failures:
                </p>

                <div className="space-y-4 max-w-3xl font-mono text-xs">
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">REPOSITORY ACCESS UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>change intake cannot complete</li>
                      <li>the run should record an intake failure</li>
                      <li>no fabricated diff or repository state may be used</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">PARTIAL DIFF OR FILE RESPONSE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>incomplete references should be identified</li>
                      <li>configured policy determines whether review may continue</li>
                      <li>missing required content prevents normalization</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">STALE REVISION:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>the previous result must not be presented as current</li>
                      <li>a new review may be required for the updated revision</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">REPORTING UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>the review decision remains distinct from GitHub reporting success</li>
                      <li>no published status should be recorded</li>
                      <li>reporting failure reason should be preserved when available</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">REPORTING REJECTED:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>rejected operation or unavailable target should be identified when possible</li>
                      <li>no success status should be recorded</li>
                      <li>no automatic authority escalation is permitted</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Target Configuration Areas Subsection */}
              <section className="space-y-4" aria-labelledby="github-config-heading">
                <h3 id="github-config-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Configuration Areas
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Core properties configured under target repository execution boundaries:
                </p>

                <div className="space-y-2 max-w-xl">
                  <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                    ILLUSTRATIVE CONFIGURATION GROUPS <span className="text-stone-400 font-normal">(NON-EXECUTABLE)</span>
                  </span>
                  <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`# Illustrative configuration shape only.
# This is not yet the repository-backed schema.

github:
  connection: "<configured-server-side-connection>"
  repository_scope: "<configured-repository-scope>"
  intake:
    enabled: "<configured-boolean>"
    change_scope: "<configured-change-scope>"

  reporting:
    enabled: "<configured-boolean>"
    review_surface: "<configured-review-surface>"

filtering:
  repository_policy: "<configured-filter-policy>"
  redaction_policy: "<configured-redaction-policy>"`}
                  </pre>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* GitHub Invariants Subsection */}
              <section className="space-y-4" aria-labelledby="github-invariants-heading">
                <h3 id="github-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  GitHub Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target GitHub contract defines the following integration invariants:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">REPOSITORY SCOPE REMAINS CONFIGURED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">REVISION REFERENCES REMAIN TRACEABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">CREDENTIALS REMAIN SERVER-SIDE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS ADVISORY.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">RISK AUTHORITY REMAINS DETERMINISTIC.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION STATUS REMAINS SCOPE-BOUND.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">REPORTING SUCCESS REMAINS EXPLICIT.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe target integration requirements, not proof that repository intake or GitHub review reporting has already been implemented.
                </p>
              </section>
            </section>
          ) : activeSection === 'DeepSeek' ? (
            <section id="deepseek" aria-labelledby="deepseek-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="deepseek-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  DeepSeek Integration
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  DeepSeek provides advisory analysis and compatible remediation proposals using bounded, redacted context assembled by the RIFTLESS control plane.
                </p>
              </div>

              {/* TARGET callout */}
              <Callout type="target">
                This section describes the target model-integration contract. Request formats, model identifiers, response schemas, token limits, and runtime behavior remain illustrative until implemented and verified against a repository-backed client.
              </Callout>

              {/* Integration Role */}
              <section className="space-y-6" aria-labelledby="deepseek-role-heading">
                <h3 id="deepseek-role-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Integration Role
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target model integration supports RIFTLESS in three distinct advisory roles to analyze data changes and organize metadata:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl">
                  {/* CHANGE EXPLANATION */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase text-[var(--color-riftless-ink)]">Change Explanation</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      The target model request may ask DeepSeek to explain:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 font-mono">
                      <li>the proposed structural or semantic change</li>
                      <li>relevant downstream dependencies</li>
                      <li>identified compatibility risks</li>
                      <li>assumptions derived from the supplied context</li>
                      <li>policy constraints relevant to remediation planning</li>
                    </ul>
                  </div>

                  {/* REMEDIATION PLANNING */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase text-[var(--color-riftless-ink)]">Remediation Planning</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      The target model may propose:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 font-mono">
                      <li>compatibility views</li>
                      <li>coordinated rename plans</li>
                      <li>downstream query patches</li>
                      <li>staged deprecation plans</li>
                      <li>owner-action recommendations</li>
                      <li>alternative migration approaches</li>
                    </ul>
                  </div>

                  {/* REVIEW ASSISTANCE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold tracking-tight text-stone-900 uppercase text-[var(--color-riftless-ink)]">Review Assistance</h4>
                    <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      The target model may help produce:
                    </p>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 font-mono">
                      <li>concise technical explanations</li>
                      <li>proposal summaries</li>
                      <li>assumptions</li>
                      <li>affected-area hypotheses</li>
                      <li>validation recommendations</li>
                    </ul>
                  </div>
                </div>

                <div className="p-4 bg-stone-50 border border-stone-200 rounded max-w-4xl text-xs text-stone-700 leading-relaxed font-semibold">
                  DeepSeek may propose and explain. It does not assign ALLOW, WARN, or BLOCK, authorize validation, approve deployment, or authorize writeback.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Static Model Request Flow */}
              <section className="space-y-4" aria-labelledby="deepseek-flow-heading">
                <h3 id="deepseek-flow-heading" className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  TARGET MODEL REQUEST FLOW
                </h3>

                {/* Desktop Flow Diagram */}
                <div className="hidden md:block bg-stone-100/60 border border-stone-200 p-5 rounded font-mono text-[9px] max-w-4xl space-y-4">
                  <div className="flex flex-wrap items-stretch justify-between gap-2">
                    <div className="flex flex-col justify-between gap-1 w-1/3">
                      <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                        PROPOSED CHANGE
                      </div>
                      <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                        REDACTED CONTEXT PACK
                      </div>
                      <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                        CONFIGURED POLICY CONSTRAINTS
                      </div>
                    </div>
                    <div className="flex items-center text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center flex flex-col justify-center min-w-[120px]">
                      <span>REQUEST ASSEMBLY</span>
                    </div>
                    <div className="flex items-center text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-stone-800 text-stone-200 border border-stone-900 font-bold shadow-sm rounded text-center flex flex-col justify-center min-w-[120px]">
                      <span>DEEPSEEK</span>
                    </div>
                    <div className="flex items-center text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center flex flex-col justify-center min-w-[120px]">
                      <span>ADVISORY RESPONSE</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between mt-4 pt-3 border-t border-stone-200/60 text-[9px] text-stone-500 gap-4">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-stone-400 rounded-full" />
                      <span>GENERAL REQUEST PATH</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-[#A8CD16] rounded-full" />
                      <span className="font-bold text-[#A8CD16]">REQUIRES EXECUTABLE EVIDENCE</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-3 border-t border-stone-200/60">
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center flex-1">
                      ADVISORY RESPONSE
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-amber-200 text-stone-700 font-bold shadow-sm rounded text-center flex-1">
                      DETERMINISTIC REVIEW
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center flex-1">
                      VALIDATION PLANNING
                      <span className="block text-[8px] text-[#A8CD16] font-bold uppercase mt-0.5">REQUIRES EXECUTABLE EVIDENCE</span>
                    </div>
                  </div>

                  <div className="p-3 bg-red-50/20 border border-red-200 rounded flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-red-600 text-white font-bold rounded text-[8px]">BLOCKED PATH</span>
                      <span className="text-stone-700 font-bold">DEEPSEEK RESPONSE</span>
                      <span className="text-stone-400 font-bold">×</span>
                      <span className="text-stone-700 font-bold">DIRECT AUTHORIZATION</span>
                    </div>
                    <div className="font-bold text-red-600 uppercase font-mono text-[10px]">
                      BLOCKED
                    </div>
                  </div>
                </div>

                {/* Mobile Flow Sequence */}
                <div className="md:hidden space-y-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px]">
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    PROPOSED CHANGE
                  </div>
                  <div className="text-center text-stone-400 font-bold">+</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    REDACTED CONTEXT PACK
                  </div>
                  <div className="text-center text-stone-400 font-bold">+</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    CONFIGURED POLICY CONSTRAINTS
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-300 text-stone-700 font-bold shadow-sm text-center">
                    REQUEST ASSEMBLY
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-stone-800 text-stone-200 font-bold shadow-sm text-center">
                    DEEPSEEK
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    ADVISORY RESPONSE
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    DETERMINISTIC REVIEW
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    VALIDATION PLANNING
                    <span className="block text-[8px] text-[#A8CD16] font-bold uppercase mt-0.5">REQUIRES EXECUTABLE EVIDENCE</span>
                  </div>

                  <div className="p-3 bg-red-50/20 border border-red-200 rounded text-center space-y-1">
                    <span className="block text-red-600 font-bold uppercase text-[8px]">BLOCKED PATH</span>
                    <span className="text-stone-700 font-bold">DEEPSEEK RESPONSE × DIRECT AUTHORIZATION</span>
                    <span className="block text-xs font-bold text-red-600 uppercase font-mono mt-1">[BLOCKED]</span>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Model Request Boundary */}
              <section className="space-y-4" aria-labelledby="deepseek-boundary-heading">
                <h3 id="deepseek-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Model Request Boundary
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target model-request contract separates permitted request content from values that must remain server-side or be excluded.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* MAY ENTER THE TARGET REQUEST */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-[#A8CD16] tracking-wider uppercase">MAY ENTER THE TARGET REQUEST</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>redacted Context Pack</li>
                      <li>proposed change</li>
                      <li>configured policy constraints</li>
                      <li>bounded schema references</li>
                      <li>relevant lineage references</li>
                      <li>permitted ownership metadata</li>
                      <li>required governance context</li>
                      <li>relevant failure or validation context</li>
                      <li>explicit requested task</li>
                    </ul>
                  </div>

                  {/* MUST REMAIN SERVER-SIDE OR EXCLUDED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-600 tracking-wider uppercase">MUST REMAIN SERVER-SIDE OR EXCLUDED</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>DeepSeek API credentials</li>
                      <li>DataHub credentials</li>
                      <li>GitHub credentials</li>
                      <li>artifact-storage credentials</li>
                      <li>internal authorization records</li>
                      <li>secret environment values</li>
                      <li>raw authorization headers</li>
                      <li>unrestricted repository content</li>
                      <li>unrelated sensitive metadata</li>
                      <li>unrestricted validation logs</li>
                      <li>hidden application instructions</li>
                    </ul>
                  </div>
                </div>

                <Callout type="warning">
                  A value is not safe for model context merely because it originated from metadata, source code, or a previous model response. Configured allowlist and redaction rules must evaluate it before request assembly.
                </Callout>

                <Callout type="note">
                  Runtime tests should verify that prohibited values are rejected or removed before a request is sent.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Untrusted Content Handling */}
              <section className="space-y-4" aria-labelledby="deepseek-untrusted-heading">
                <h3 id="deepseek-untrusted-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Untrusted Content
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Repository content, metadata descriptions, comments, queries, and previous model output must be treated as untrusted data.
                </p>

                <div className="space-y-2 text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl pt-2">
                  <p>Target requirements for handling untrusted content:</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs text-stone-600">
                    <li>untrusted content must not override control-plane policy</li>
                    <li>repository comments must not become system instructions</li>
                    <li>metadata descriptions must not authorize additional tools or data access</li>
                    <li>previous model output must not authorize later stages</li>
                    <li>requested remediation must remain within the configured task</li>
                    <li>external content should remain clearly separated from control instructions</li>
                    <li>model output must be validated before executable use</li>
                  </ul>
                </div>

                <Callout type="warning">
                  Instructions found inside repository files, SQL comments, metadata descriptions, or retrieved content must not be treated as RIFTLESS authorization.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Request Assembly Sequence */}
              <section className="space-y-4" aria-labelledby="deepseek-assembly-heading">
                <h3 id="deepseek-assembly-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Request Assembly
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The assembly of a model request progresses through the following sequential stages:
                </p>

                <ol className="list-decimal pl-5 space-y-2 text-xs text-stone-700 font-mono leading-relaxed max-w-2xl">
                  <li><strong>REVIEW TASK IDENTIFIED:</strong> The specific advisory task is identified and restricted.</li>
                  <li><strong>REQUIRED CONTEXT SELECTED:</strong> Necessary schemas, lineage maps, and policy definitions are gathered.</li>
                  <li><strong>PROHIBITED VALUES EXCLUDED:</strong> Configured redaction and allowlist rules must remove or reject prohibited values.</li>
                  <li><strong>CONTEXT BOUNDED:</strong> Request content should remain within configured size limits. Oversized input must be reduced through explicit context selection or rejected.</li>
                  <li><strong>SOURCE REFERENCES ATTACHED:</strong> Available source references should remain associated with the supplied context.</li>
                  <li><strong>POLICY CONSTRAINTS INCLUDED:</strong> Explicit rules bounding remediation proposals are appended.</li>
                  <li><strong>REQUEST SIZE CHECKED:</strong> The fully constructed request size is measured against target constraints.</li>
                  <li><strong>MODEL REQUEST PREPARED:</strong> A permitted request structure is prepared for the configured model client.</li>
                </ol>

                <div className="space-y-2 text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl pt-2">
                  <p>Request assembly guidelines and invariants:</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs text-stone-600">
                    <li>the task should be explicit and narrow</li>
                    <li>unrelated context should not be added automatically</li>
                    <li>source references should remain associated with supplied claims</li>
                    <li>the request should state that model output is advisory</li>
                    <li>configured size limits should prevent unbounded requests</li>
                    <li>request failure must not alter deterministic risk results</li>
                  </ul>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Request Content Table */}
              <section className="space-y-4" aria-labelledby="deepseek-content-heading">
                <h3 id="deepseek-content-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Request Content Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The mapping of RIFTLESS run parameters into a target advisory request:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="deepseek-content-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target DeepSeek request content and its role in advisory remediation planning.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Request Element</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Source</th>
                        <th scope="col" className="px-4 py-3">Required or Conditional</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PROPOSED CHANGE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Describe the change being evaluated.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Normalized Change Request.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REDACTED CONTEXT PACK</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide relevant downstream and organizational context.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured metadata integrations after filtering.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Required when contextual review is enabled.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">POLICY CONSTRAINTS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Bound remediation proposals to configured requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">RIFTLESS policy configuration.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REQUESTED TASK</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Specify explanation, remediation, or comparison work.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Control-plane orchestration.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Required.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">SOURCE REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Associate supplied context with retrievable evidence references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Change Request and Context Pack.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional on available referenced context.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PREVIOUS VALIDATION CONTEXT</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Help explain or revise a failed proposal.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Permitted validation outcome and failure summary.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Conditional.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Target Client Responsibilities */}
              <section className="space-y-4" aria-labelledby="deepseek-client-heading">
                <h3 id="deepseek-client-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Client Responsibilities
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target DeepSeek client adapter is responsible for configured server-side access and permitted request assembly:
                </p>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl">
                  <li>establish configured server-side API access</li>
                  <li>assemble only permitted request content</li>
                  <li>exclude credentials and prohibited values</li>
                  <li>attach the explicit requested task</li>
                  <li>submit the configured model request</li>
                  <li>record request status without storing secrets</li>
                  <li>parse the returned advisory response</li>
                  <li>reject unreadable or invalid response shapes</li>
                  <li>preserve permitted proposal and source references</li>
                  <li>report unavailable or incomplete model responses</li>
                  <li>avoid granting model output authority over run state</li>
                </ul>

                <p className="text-xs text-stone-600 leading-relaxed max-w-2xl italic font-semibold pt-1">
                  The target DeepSeek client is an advisory integration adapter. It does not own deterministic policy, validation authorization, deployment authority, or writeback authority.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Non-Executable Operation Shapes */}
              <section className="space-y-4" aria-labelledby="deepseek-shapes-heading">
                <h3 id="deepseek-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Operation Shapes
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Illustrative interface specifications for advisory model request and parsing operations:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* Block 1 */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL MODEL REQUEST <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive explicit review task
receive redacted Context Pack
receive proposed change
receive configured policy constraints
exclude prohibited values
submit configured advisory request
return parsed advisory response`}
                    </pre>
                  </div>

                  {/* Block 2 */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL RESPONSE HANDOFF <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive advisory explanation or remediation proposal
record assumptions and source references
validate required response fields
forward proposal to deterministic review
prepare configured validation planning
preserve response status or failure reason`}
                    </pre>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] italic">
                  Exact API operations, model identifiers, headers, payload schemas, response formats, and retry behavior will be documented after the DeepSeek client is implemented and versioned.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Advisory Response Contract */}
              <section className="space-y-4" aria-labelledby="deepseek-contract-heading">
                <h3 id="deepseek-contract-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Advisory Response Contract
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target contract defines structural boundaries for parsing and utilizing model responses:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  <div className="space-y-3">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">Target response may include:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 leading-relaxed">
                      <li>concise change explanation</li>
                      <li>identified compatibility risks</li>
                      <li>remediation proposal</li>
                      <li>assumptions</li>
                      <li>referenced context</li>
                      <li>affected-area hypotheses</li>
                      <li>proposed validation steps</li>
                      <li>known limitations</li>
                      <li>unresolved questions</li>
                    </ul>
                  </div>

                  <div className="bg-red-50/20 border border-red-200/60 rounded p-5 space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-700 uppercase">Target response must not be treated as:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-700 leading-relaxed">
                      <li>Risk Decision</li>
                      <li>authorization record</li>
                      <li>validation evidence</li>
                      <li>deployment approval</li>
                      <li>writeback approval</li>
                      <li>proof that referenced assets actually exist</li>
                      <li>proof that proposed SQL executes correctly</li>
                    </ul>
                  </div>
                </div>

                <p className="text-xs text-stone-600 leading-relaxed max-w-2xl italic font-semibold pt-1">
                  A model response is useful only as an advisory artifact until deterministic policy evaluation and executable validation establish the permitted next state.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* Remediation Proposal Table */}
              <section className="space-y-4" aria-labelledby="deepseek-remediation-heading">
                <h3 id="deepseek-remediation-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Remediation Proposal Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The relationship between parsed proposal elements and downstream evaluation stages:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="deepseek-remediation-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target fields in an advisory DeepSeek remediation proposal.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Proposal Field</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Required</th>
                        <th scope="col" className="px-4 py-3">Downstream Use</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">SUMMARY</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Explain the proposed compatibility strategy.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-900 font-bold align-top">Yes.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Human review and deterministic proposal checks.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ASSUMPTIONS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Expose conditions relied upon by the proposal.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-900 font-bold align-top">Yes.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Review and validation planning.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PROPOSED CHANGES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Describe suggested SQL, schema, dbt, or coordination changes.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 align-top">Yes when remediation is requested.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Proposal review and isolated validation.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">AFFECTED AREAS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify potential downstream surfaces from supplied context.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 align-top">Conditional.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Risk comparison and validation scope.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">SOURCE REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Associate claims with supplied context references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 align-top">Conditional on available references.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Explainability and review.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION RECOMMENDATIONS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Suggest relevant executable checks.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 align-top">Conditional.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Validation planning only.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">LIMITATIONS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">State unresolved uncertainty or missing context.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-900 font-bold align-top">Yes.</td>
                        <td className="px-4 py-3 text-stone-600 align-top">Human review and policy handling.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="p-4 bg-stone-50 border border-stone-200 rounded max-w-4xl text-xs text-stone-700 leading-relaxed">
                  <p className="font-bold uppercase text-[10px] text-stone-500 tracking-wider mb-1">PROPOSAL INTEGRITY REQUIREMENT</p>
                  No hidden chain of thought, private reasoning transcript, unsupported certainty score, or fabricated evidence may enter the reported remediation proposal. Use concise rationale, assumptions, and source references instead.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Deterministic Handoff */}
              <section className="space-y-4" aria-labelledby="deepseek-handoff-heading">
                <h3 id="deepseek-handoff-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Deterministic Handoff
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  After an advisory response is returned, the RIFTLESS control plane coordinates execution handoff:
                </p>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl">
                  <li>required response fields should be checked</li>
                  <li>unsupported or malformed output should be rejected</li>
                  <li>assumptions should remain explicit</li>
                  <li>source references should remain attached where available</li>
                  <li>the proposal must not clear an existing BLOCK</li>
                  <li>configured deterministic rules may evaluate the proposal</li>
                  <li>protected state transitions require control-plane authorization</li>
                  <li>executable validation is required where configured</li>
                  <li>only validation output can become executable evidence</li>
                </ul>

                {/* Inline flow chart */}
                <div className="bg-stone-50 border border-stone-200 rounded p-4 max-w-3xl font-mono text-[10px] text-stone-600 flex flex-wrap items-center justify-center gap-2">
                  <div className="p-1.5 bg-white border border-stone-200 rounded font-bold">ADVISORY RESPONSE</div>
                  <div>→</div>
                  <div className="p-1.5 bg-white border border-stone-200 rounded font-bold">RESPONSE CHECKS</div>
                  <div>→</div>
                  <div className="p-1.5 bg-white border border-stone-200 rounded font-bold">DETERMINISTIC POLICY</div>
                  <div>→</div>
                  <div className="p-1.5 bg-white border border-stone-200 rounded font-bold">VALIDATION PLAN</div>
                  <div>→</div>
                  <div className="p-1.5 bg-white border border-stone-200 rounded font-bold">ISOLATED EXECUTION</div>
                  <div>→</div>
                  <div className="p-1.5 bg-lime-50/20 border border-lime-200 text-[#A8CD16] rounded font-bold">EVIDENCE</div>
                </div>

                <Callout type="warning">
                  Syntactically plausible SQL or a confident explanation is not evidence that a remediation is correct.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Model Availability and Failure */}
              <section className="space-y-4" aria-labelledby="deepseek-failure-heading">
                <h3 id="deepseek-failure-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  DeepSeek Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Explicit target behaviors are defined for various model integration failures:
                </p>

                <div className="space-y-4 max-w-3xl font-mono text-xs">
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">MODEL ACCESS UNAVAILABLE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>no new explanation or remediation proposal is produced</li>
                      <li>deterministic Risk Decision remains independent</li>
                      <li>the run may continue only when model assistance is not required by policy</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">REQUEST REJECTED:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>rejection reason should be recorded when available</li>
                      <li>no fabricated response may be substituted</li>
                      <li>the run must not treat the request as completed</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">RESPONSE UNREADABLE OR MALFORMED:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>response should be rejected</li>
                      <li>proposal status must remain unavailable</li>
                      <li>failure reason should be recorded</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">RESPONSE INCOMPLETE:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>missing required proposal fields should be identified</li>
                      <li>configured policy determines whether human review or a new request is permitted</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">RESPONSE CONFLICTS WITH POLICY:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>deterministic policy remains authoritative</li>
                      <li>the conflicting proposal must not advance the run</li>
                    </ul>
                  </div>
                  <div className="p-4 border border-stone-200 bg-stone-50/20 rounded">
                    <span className="font-bold text-stone-900 block mb-1">RESPONSE REFERENCES UNSUPPLIED FACTS:</span>
                    <ul className="list-disc pl-4 space-y-1 text-stone-600">
                      <li>unsupported claims must not become evidence</li>
                      <li>the proposal should be rejected, revised, or sent to human review according to configured policy</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* Data Retention Boundary */}
              <section className="space-y-4" aria-labelledby="deepseek-retention-heading">
                <h3 id="deepseek-retention-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Request and Response Records
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Target principles applied to historical execution logs and model interactions:
                </p>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl">
                  <li>do not store API credentials in artifacts</li>
                  <li>do not store prohibited request values</li>
                  <li>preserve the request status</li>
                  <li>preserve the explicit requested task</li>
                  <li>preserve permitted source references</li>
                  <li>preserve the advisory proposal when allowed</li>
                  <li>preserve assumptions and limitations</li>
                  <li>preserve failure reason when a request fails</li>
                  <li>distinguish model output from validation evidence</li>
                  <li>apply configured retention rules to request and response records</li>
                </ul>

                <Callout type="note">
                  The exact persistence and retention implementation remains undefined until the repository-backed artifact model is implemented.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* Target Configuration Areas */}
              <section className="space-y-4" aria-labelledby="deepseek-config-heading">
                <h3 id="deepseek-config-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Configuration Areas
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Core properties configured under target model execution boundaries:
                </p>

                <div className="space-y-2 max-w-xl">
                  <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                    ILLUSTRATIVE CONFIGURATION GROUPS <span className="text-stone-400 font-normal">(NON-EXECUTABLE)</span>
                  </span>
                  <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`# Illustrative configuration shape only.
# This is not yet the repository-backed schema.

deepseek:
  connection: "<configured-server-side-connection>"
  model: "<configured-model-identifier>"
  request:
    task_scope: "<configured-task-scope>"
    size_limit: "<configured-request-limit>"

  response:
    required_fields: "<configured-response-contract>"

redaction:
  policy: "<configured-redaction-policy>"

retention:
  request_records: "<configured-retention-policy>"
  response_records: "<configured-retention-policy>"`}
                  </pre>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* DeepSeek Invariants */}
              <section className="space-y-4" aria-labelledby="deepseek-invariants-heading">
                <h3 id="deepseek-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  DeepSeek Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target DeepSeek contract defines the following integration invariants:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">REQUEST CONTEXT REMAINS BOUNDED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN SERVER-SIDE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">UNTRUSTED CONTENT REMAINS DATA.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS ADVISORY.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">ASSUMPTIONS REMAIN EXPLICIT.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">POLICY AUTHORITY REMAINS DETERMINISTIC.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION EVIDENCE REMAINS EXECUTABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">FAILURE REMAINS NON-AUTHORIZING.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe target integration requirements, not proof that the DeepSeek client or response contract has already been implemented.
                </p>
              </section>
            </section>
          ) : activeSection === 'Configuration' ? (
            <section id="configuration" aria-labelledby="configuration-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="configuration-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Configuration
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  RIFTLESS configuration defines integration boundaries, deterministic policy selection, validation behavior, redaction requirements, artifact handling, and permitted writeback capabilities.
                </p>
              </div>

              {/* TARGET callout */}
              <Callout type="target">
                This section describes the target configuration contract. File names, field names, defaults, precedence rules, and validation behavior remain illustrative until a repository-backed configuration schema is implemented and versioned.
              </Callout>

              <hr className="border-stone-200/50" />

              {/* CONFIGURATION PRINCIPLES */}
              <section className="space-y-4" aria-labelledby="config-principles-heading">
                <h3 id="config-principles-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Configuration Principles
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target configuration model is designed around six foundational principles to ensure reliable evaluation and control:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-950 uppercase">EXPLICIT</h4>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      Enabled integrations and capabilities should be declared rather than inferred.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-950 uppercase">BOUNDED</h4>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      Repository scope, metadata scope, model context, validation commands, and writeback destinations should remain limited to configured boundaries.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-950 uppercase">SERVER-SIDE</h4>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      Credentials, connection details, authorization records, and restricted configuration must not be exposed to browser code or model context.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-950 uppercase">VALIDATED BEFORE USE</h4>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      Unknown, missing, conflicting, or malformed configuration should produce an explicit configuration result before a review run begins.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-950 uppercase">NON-AUTHORIZING</h4>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      Configuration may define policy and capability boundaries, but configuration values do not replace a recorded runtime decision or validation outcome.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-950 uppercase">TRACEABLE</h4>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      The target run record should retain a reference to the effective configuration version or identifier used during evaluation.
                    </p>
                  </div>
                </div>

                <Callout type="note">
                  A configuration file is an input to the control plane. It is not evidence that an integration, validator, or writeback operation is functioning correctly.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* CONFIGURATION DOMAINS */}
              <section className="space-y-6" aria-labelledby="config-domains-heading">
                <h3 id="config-domains-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Configuration Domains
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Each domain defines target concerns and intended authority boundaries that repository-backed runtime controls must enforce.
                </p>

                <div className="space-y-6 max-w-4xl">
                  {/* DATAHUB */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">A. DataHub Integration</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="space-y-1.5">
                        <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONCERNS</span>
                        <ul className="list-disc pl-4 space-y-1 text-stone-600">
                          <li>configured server-side connection reference</li>
                          <li>metadata read scope</li>
                          <li>enabled metadata categories</li>
                          <li>writeback enabled state</li>
                          <li>conceptual writeback mappings</li>
                        </ul>
                      </div>
                      <div className="space-y-1.5">
                        <span className="font-mono text-[10px] text-red-600 font-bold block uppercase">MUST NOT CONTAIN</span>
                        <ul className="list-disc pl-4 space-y-1 text-stone-600">
                          <li>browser-visible credentials</li>
                          <li>unrestricted metadata export instructions</li>
                          <li>model-context secrets</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* GITHUB */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">B. GitHub Integration</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="space-y-1.5">
                        <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONCERNS</span>
                        <ul className="list-disc pl-4 space-y-1 text-stone-600">
                          <li>configured repository scope</li>
                          <li>intake enabled state</li>
                          <li>bounded change scope</li>
                          <li>reporting enabled state</li>
                          <li>configured review surface</li>
                        </ul>
                      </div>
                      <div className="space-y-1.5">
                        <span className="font-mono text-[10px] text-amber-600 font-bold block uppercase">MUST NOT IMPLY</span>
                        <ul className="list-disc pl-4 space-y-1 text-stone-600">
                          <li>exact GitHub permission names</li>
                          <li>finalized authentication method</li>
                          <li>active webhook implementation</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* DEEPSEEK */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">C. DeepSeek Integration</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="space-y-1.5">
                        <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONCERNS</span>
                        <ul className="list-disc pl-4 space-y-1 text-stone-600">
                          <li>configured server-side connection reference</li>
                          <li>model identifier selected by implementation</li>
                          <li>allowed task scope</li>
                          <li>request-size policy</li>
                          <li>expected advisory response contract</li>
                        </ul>
                      </div>
                      <div className="space-y-1.5">
                        <span className="font-mono text-[10px] text-red-600 font-bold block uppercase">MUST NOT GRANT</span>
                        <ul className="list-disc pl-4 space-y-1 text-stone-600">
                          <li>risk authority</li>
                          <li>state-transition authority</li>
                          <li>validation authority</li>
                          <li>writeback authority</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* POLICIES */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">D. Policies</h4>
                    <div className="space-y-2 text-xs">
                      <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONCERNS</span>
                      <ul className="list-disc pl-4 space-y-1 text-stone-600">
                        <li>deterministic risk-policy selection</li>
                        <li>contract rules</li>
                        <li>acknowledgment requirements</li>
                        <li>required validation gates</li>
                        <li>writeback authorization conditions</li>
                      </ul>
                      <div className="p-3 bg-stone-50 rounded border border-stone-100 font-mono text-[11px] text-stone-700 mt-2 leading-relaxed">
                        <span className="font-bold text-stone-900">CLARIFICATION:</span> Policy configuration defines deterministic evaluation requirements. DeepSeek does not modify policy authority.
                      </div>
                    </div>
                  </div>

                  {/* VALIDATORS */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">E. Validators</h4>
                    <div className="space-y-2 text-xs">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                          <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONCERNS</span>
                          <ul className="list-disc pl-4 space-y-1 text-stone-600">
                            <li>enabled validator categories</li>
                            <li>validator-specific bounded options</li>
                            <li>required versus optional validation steps</li>
                            <li>isolated execution requirements</li>
                            <li>failure handling policy</li>
                          </ul>
                        </div>
                        <div className="space-y-1.5">
                          <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET VALIDATORS MAY INCLUDE</span>
                          <ul className="list-disc pl-4 space-y-1 text-stone-600">
                            <li>SQLGlot</li>
                            <li>DuckDB</li>
                            <li>dbt compilation or tests</li>
                            <li>deterministic policy checks</li>
                          </ul>
                        </div>
                      </div>
                      <div className="p-3 bg-stone-50 rounded border border-stone-100 font-mono text-[11px] text-stone-700 mt-2 leading-relaxed">
                        <span className="font-bold text-stone-950">NOTE:</span> Executable command syntax is not yet defined in this contract.
                      </div>
                    </div>
                  </div>

                  {/* REDACTION */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">F. Redaction</h4>
                    <div className="space-y-1.5 text-xs">
                      <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONCERNS</span>
                      <ul className="list-disc pl-4 space-y-1 text-stone-600">
                        <li>prohibited value categories</li>
                        <li>permitted context categories</li>
                        <li>repository-content filtering</li>
                        <li>metadata allowlist behavior</li>
                        <li>model-request exclusion requirements</li>
                        <li>validation-log filtering requirements</li>
                      </ul>
                    </div>
                  </div>

                  {/* ARTIFACTS AND RETENTION */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">G. Artifacts and Retention</h4>
                    <div className="space-y-2 text-xs">
                      <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONCERNS</span>
                      <ul className="list-disc pl-4 space-y-1 text-stone-600">
                        <li>configured artifact destination reference</li>
                        <li>permitted artifact categories</li>
                        <li>retention-policy reference</li>
                        <li>prohibited artifact content</li>
                        <li>failure-record requirements</li>
                      </ul>
                      <div className="p-3 bg-stone-50 rounded border border-stone-100 font-mono text-[11px] text-stone-700 mt-2 leading-relaxed">
                        <span className="font-bold text-stone-950">NOTE:</span> Storage provider choice remains open; no specific provider is marked as mandatory.
                      </div>
                    </div>
                  </div>

                  {/* WRITEBACK */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">H. Writeback</h4>
                    <div className="space-y-2 text-xs">
                      <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONCERNS</span>
                      <ul className="list-disc pl-4 space-y-1 text-stone-600">
                        <li>enabled state</li>
                        <li>permitted record categories</li>
                        <li>required authorization state</li>
                        <li>configured destination mappings</li>
                        <li>failure reporting behavior</li>
                      </ul>
                      <div className="p-3 bg-stone-50 rounded border border-stone-100 font-mono text-[11px] text-stone-700 mt-2 leading-relaxed">
                        <span className="font-bold text-stone-900">CLARIFICATION:</span> Enabling writeback does not authorize an individual writeback operation.
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET CONFIGURATION FLOW */}
              <section className="space-y-4" aria-labelledby="config-flow-heading">
                <h3 id="config-flow-heading" className="text-[10px] font-mono tracking-widest text-stone-500 uppercase font-bold">
                  Target Configuration Flow
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target control plane is expected to resolve configuration through explicit validation stages before a review run begins:
                </p>

                {/* Desktop Flow Diagram */}
                <div className="hidden md:block bg-stone-100/60 border border-stone-200 p-5 rounded font-mono text-[9px] max-w-4xl space-y-4">
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      CONFIGURATION INPUT
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      STRUCTURE CHECK
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      REQUIRED FIELD CHECK
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      PROHIBITED VALUE CHECK
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm rounded text-center">
                      CAPABILITY RESOLUTION
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-stone-800 text-stone-100 font-bold shadow-sm rounded text-center">
                      EFFECTIVE CONFIGURATION
                    </div>
                    <div className="text-stone-400 font-bold">→</div>
                    <div className="p-2 bg-white border border-lime-200 text-[#A8CD16] font-bold shadow-sm rounded text-center">
                      REVIEW RUN
                    </div>
                  </div>

                  <div className="p-3 bg-red-50/20 border border-red-200 rounded flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-red-600 text-white font-bold rounded text-[8px]">BLOCKED PATH</span>
                      <span className="text-stone-700 font-bold">INVALID CONFIGURATION</span>
                      <span className="text-stone-400 font-bold">×</span>
                      <span className="text-stone-700 font-bold">REVIEW EXECUTION</span>
                    </div>
                    <div className="font-bold text-red-600 uppercase font-mono text-[10px]">
                      BLOCKED
                    </div>
                  </div>
                </div>

                {/* Mobile Flow Sequence */}
                <div className="md:hidden space-y-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px]">
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    CONFIGURATION INPUT
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    STRUCTURE CHECK
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    REQUIRED FIELD CHECK
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    PROHIBITED VALUE CHECK
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center">
                    CAPABILITY RESOLUTION
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-stone-800 text-stone-100 font-bold shadow-sm text-center">
                    EFFECTIVE CONFIGURATION
                  </div>
                  <div className="text-center text-stone-400 font-bold">↓</div>
                  <div className="p-2 bg-white border border-lime-200 text-[#A8CD16] font-bold shadow-sm text-center">
                    REVIEW RUN
                  </div>

                  <div className="p-3 bg-red-50/20 border border-red-200 rounded text-center space-y-1">
                    <span className="block text-red-600 font-bold uppercase text-[8px]">BLOCKED PATH</span>
                    <span className="text-stone-700 font-bold">INVALID CONFIGURATION × REVIEW EXECUTION</span>
                    <span className="block text-xs font-bold text-red-600 uppercase font-mono mt-1">[BLOCKED]</span>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* CONFIGURATION DOMAIN TABLE */}
              <section className="space-y-4" aria-labelledby="config-table-heading">
                <h3 id="config-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Configuration Domains Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The logical separation of concerns across target domains defines specific responsibilities and clear authority boundaries:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="configuration-domains-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target RIFTLESS configuration domains and their conceptual responsibilities.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Domain</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Primary Responsibility</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Example Configuration Concern</th>
                        <th scope="col" className="px-4 py-3">Authority Boundary</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DATAHUB</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define target metadata read and writeback boundaries.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Metadata categories and conceptual writeback mappings.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Does not authorize risk decisions.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">GITHUB</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define target repository intake and reporting boundaries.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Repository scope and reporting enabled state.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Does not approve a change.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DEEPSEEK</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define target advisory model-client boundaries.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Task scope and response contract.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Advisory only.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">POLICIES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define deterministic evaluation and protected transition requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Risk rules and required validation gates.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">May determine whether a run can advance within configured policy.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATORS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define executable validation categories and requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required or optional validator selection.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Produces evidence, not deployment approval.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REDACTION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define prohibited and permitted context boundaries.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Model-request and log filtering rules.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Prevents prohibited input; does not authorize a run.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACTS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define target evidence destination and retention requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Artifact categories and destination reference.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Storage does not determine correctness.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITEBACK</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define permitted metadata-record destinations.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-bold">Enabled state and conceptual mappings.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Individual writeback still requires recorded authorization.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET CONFIGURATION SHAPE */}
              <section className="space-y-4" aria-labelledby="config-shape-heading">
                <h3 id="config-shape-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Configuration Shape
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The layout structure representing the conceptual RIFTLESS YAML format:
                </p>

                <div className="space-y-2 max-w-xl">
                  <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                    ILLUSTRATIVE CONFIGURATION SHAPE <span className="text-stone-400 font-normal">(NON-EXECUTABLE)</span>
                  </span>
                  <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`# Illustrative configuration shape only.
# This is not yet the repository-backed schema.

datahub:
  connection: "<configured-server-side-connection>"
  read_scope: "<configured-metadata-scope>"
  metadata_categories:
    - "<configured-category>"
  writeback:
    enabled: "<configured-boolean>"
    mappings: "<configured-writeback-mappings>"

github:
  connection: "<configured-server-side-connection>"
  repository_scope: "<configured-repository-scope>"
  intake:
    enabled: "<configured-boolean>"
    change_scope: "<configured-change-scope>"
  reporting:
    enabled: "<configured-boolean>"
    review_surface: "<configured-review-surface>"

deepseek:
  connection: "<configured-server-side-connection>"
  model: "<configured-model-identifier>"
  request:
    task_scope: "<configured-task-scope>"
    size_limit: "<configured-request-limit>"
  response:
    required_fields: "<configured-response-contract>"

policies:
  risk: "<configured-risk-policy>"
  acknowledgment: "<configured-review-policy>"
  required_validation: "<configured-validation-policy>"

validators:
  enabled:
    - "<configured-validator>"
  requirements: "<configured-validator-requirements>"

redaction:
  policy: "<configured-redaction-policy>"
  allowlist: "<configured-context-allowlist>"

artifacts:
  destination: "<configured-artifact-destination>"
  retention: "<configured-retention-policy>"

writeback:
  authorization: "<configured-authorization-policy>"`}
                  </pre>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* VALUE CATEGORIES */}
              <section className="space-y-4" aria-labelledby="value-categories-heading">
                <h3 id="value-categories-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Value Categories
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Configuration values must be strictly partitioned to prevent accidental exposure of sensitive runtime credentials or tokens:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* MAY APPEAR IN PROJECT CONFIGURATION */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-[#A8CD16] tracking-wider uppercase">MAY APPEAR IN PROJECT CONFIGURATION</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>enabled capability flags</li>
                      <li>repository scope references</li>
                      <li>metadata category selection</li>
                      <li>validator selection</li>
                      <li>policy references</li>
                      <li>redaction-policy references</li>
                      <li>artifact-destination references</li>
                      <li>retention-policy references</li>
                      <li>writeback mapping references</li>
                    </ul>
                  </div>

                  {/* MUST REMAIN IN SERVER-SIDE SECRET MANAGEMENT */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-600 tracking-wider uppercase">MUST REMAIN IN SERVER-SIDE SECRET MANAGEMENT</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>API credentials</li>
                      <li>access tokens</li>
                      <li>private keys</li>
                      <li>raw authorization headers</li>
                      <li>credential-bearing connection strings</li>
                      <li>webhook secrets</li>
                      <li>secret environment values</li>
                    </ul>
                  </div>
                </div>

                <Callout type="warning">
                  A placeholder field for a connection does not mean credentials should be stored directly in the project configuration file.
                </Callout>

                <Callout type="note">
                  The final implementation should resolve secrets through a server-side mechanism without rendering them into browser-visible configuration, logs, artifacts, or model context.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET PRECEDENCE MODEL */}
              <section className="space-y-4" aria-labelledby="precedence-model-heading">
                <h3 id="precedence-model-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Precedence Model
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  When establishing the final configuration, settings are resolved using a specific, conceptual precedence order:
                </p>

                {/* Path display */}
                <div className="bg-stone-50 border border-stone-200 rounded p-4 font-mono text-[10px] text-stone-700 space-y-2 max-w-xl">
                  <span className="text-[9px] font-bold text-stone-500 uppercase block">CONCEPTUAL ORDER OF PRECEDENCE</span>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="p-1.5 bg-white border border-stone-200 rounded font-bold">IMPLEMENTATION DEFAULTS</span>
                    <span className="font-bold text-stone-400">→</span>
                    <span className="p-1.5 bg-white border border-stone-200 rounded font-bold">PROJECT CONFIGURATION</span>
                    <span className="font-bold text-stone-400">→</span>
                    <span className="p-1.5 bg-white border border-stone-200 rounded font-bold">PERMITTED RUN-SPECIFIC OVERRIDES</span>
                    <span className="font-bold text-stone-400">→</span>
                    <span className="p-1.5 bg-stone-800 text-stone-100 rounded font-bold">EFFECTIVE CONFIGURATION</span>
                  </div>
                </div>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl pt-2">
                  <li>implementation defaults should remain explicit and versioned</li>
                  <li>project configuration may define repository-level behavior</li>
                  <li>only explicitly permitted fields may accept run-specific overrides</li>
                  <li>credentials must not be passed as ordinary run overrides</li>
                  <li>overrides must not weaken mandatory policy, redaction, or validation requirements unless the implemented policy model explicitly permits it</li>
                  <li>effective configuration should be recorded by reference for explainability</li>
                </ul>

                <Callout type="target">
                  The final precedence and override model must be derived from the implemented schema. This conceptual ordering is not yet executable behavior.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET CONFIGURATION VALIDATION */}
              <section className="space-y-4" aria-labelledby="config-validation-heading">
                <h3 id="config-validation-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Configuration Validation
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target configuration contract defines five validation-result categories so configuration problems can be reported explicitly before a run begins:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
                  {/* STRUCTURE ERROR */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="text-[10px] font-mono bg-red-100 text-red-800 font-bold px-2 py-0.5 rounded uppercase">Structure Error</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li><strong>Examples:</strong> Malformed document, unsupported top-level structure, invalid field shape.</li>
                      <li><strong>Target result:</strong> Configuration unavailable, review run must not begin.</li>
                    </ul>
                  </div>

                  {/* MISSING REQUIRED VALUE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="text-[10px] font-mono bg-red-100 text-red-800 font-bold px-2 py-0.5 rounded uppercase">Missing Required Value</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li><strong>Examples:</strong> Required enabled integration lacks a connection reference, enabled validator lacks required options, writeback enabled without required mapping.</li>
                      <li><strong>Target result:</strong> Affected capability remains unavailable, run must not silently assume a value.</li>
                    </ul>
                  </div>

                  {/* UNKNOWN FIELD */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="text-[10px] font-mono bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded uppercase">Unknown Field</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li>Should be rejected or reported according to the implemented schema policy.</li>
                      <li>Must not silently alter authority behavior.</li>
                    </ul>
                  </div>

                  {/* CONFLICTING CONFIGURATION */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="text-[10px] font-mono bg-red-100 text-red-800 font-bold px-2 py-0.5 rounded uppercase">Conflicting Configuration</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li><strong>Examples:</strong> Writeback enabled while authorization policy is absent, required validation disabled, model assistance required while model integration is disabled.</li>
                      <li><strong>Target result:</strong> Explicit configuration conflict; run does not begin until resolved.</li>
                    </ul>
                  </div>

                  {/* PROHIBITED VALUE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2">
                    <span className="text-[10px] font-mono bg-red-100 text-red-800 font-bold px-2 py-0.5 rounded uppercase">Prohibited Value</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li><strong>Examples:</strong> Secret embedded in browser-visible config, credential placed in model-context configuration, unrestricted production-write configuration for validation worker.</li>
                      <li><strong>Target result:</strong> Configuration rejected, prohibited value not propagated.</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* CAPABILITY ENABLEMENT */}
              <section className="space-y-4" aria-labelledby="capability-enablement-heading">
                <h3 id="capability-enablement-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Capability Enablement
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Declaring a capability as enabled does not mean it is immediately functional, authorized, or correct. The state progress must be evaluated across multiple verification boundaries:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-xl space-y-3 font-mono text-xs">
                  <div className="font-bold text-center text-stone-900 text-sm tracking-wider">
                    CONFIGURED &ne; AVAILABLE &ne; AUTHORIZED &ne; SUCCESSFUL
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="text-xs text-stone-600 font-sans leading-relaxed space-y-2">
                    <p>
                      <strong>CONFIGURED:</strong> Defined structurally inside the configuration file, but connection health or schema versions remain unverified.
                    </p>
                    <p>
                      <strong>AVAILABLE:</strong> Initialized with valid credentials and reachable endpoints, but the specific task or scope remains unauthorized for the current run.
                    </p>
                    <p>
                      <strong>AUTHORIZED:</strong> The required authorization state has been recorded for the specific capability operation, but that operation has not yet completed.
                    </p>
                    <p>
                      <strong>SUCCESSFUL:</strong> The specific capability operation completed and its resulting status was recorded. Success for one capability does not imply that the entire review run succeeded.
                    </p>
                  </div>
                </div>

                <div className="space-y-2 text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl pt-2">
                  <p>Invariants of capability enablement:</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs text-stone-600">
                    <li>enabled does not mean healthy</li>
                    <li>configured does not mean verified</li>
                    <li>available does not mean authorized</li>
                    <li>validation enabled does not mean validation passed</li>
                    <li>writeback enabled does not mean writeback permitted</li>
                  </ul>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* EFFECTIVE CONFIGURATION RECORD */}
              <section className="space-y-4" aria-labelledby="effective-record-heading">
                <h3 id="effective-record-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Effective Configuration Record
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  For explainability and reproducibility, target run references should identify the effective configuration used during evaluation:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* TARGET RUN REFERENCES SHOULD IDENTIFY */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-[#A8CD16] tracking-wider uppercase">TARGET RUN REFERENCES SHOULD IDENTIFY</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>configuration schema or implementation version when available</li>
                      <li>project configuration reference</li>
                      <li>permitted override reference</li>
                      <li>enabled capability set</li>
                      <li>selected policy references</li>
                      <li>selected validator categories</li>
                      <li>redaction-policy reference</li>
                      <li>writeback enabled state</li>
                      <li>artifact and retention-policy references</li>
                    </ul>
                  </div>

                  {/* MUST NOT PRESERVE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-600 tracking-wider uppercase">MUST NOT PRESERVE</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>API credentials</li>
                      <li>access tokens</li>
                      <li>secret environment values</li>
                      <li>raw authorization headers</li>
                      <li>private keys</li>
                    </ul>
                  </div>
                </div>

                <Callout type="note">
                  The exact storage and versioning model for effective configuration remains undefined until the backend artifact contract is implemented.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* CONFIGURATION FAILURE BEHAVIOR */}
              <section className="space-y-4" aria-labelledby="failure-behavior-heading">
                <h3 id="failure-behavior-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Configuration Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target configuration contract defines the following non-success behavior when configuration parsing, resolution, or capability initialization cannot complete:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl">
                  {/* CONFIGURATION UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">CONFIGURATION UNAVAILABLE</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Review run must not begin.</li>
                      <li>Failure reason should be reported.</li>
                    </ul>
                  </div>

                  {/* CONFIGURATION MALFORMED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">CONFIGURATION MALFORMED</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>No inferred fallback should silently replace required values.</li>
                      <li>Parsing or structure failure should be recorded.</li>
                    </ul>
                  </div>

                  {/* REQUIRED CAPABILITY DISABLED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">REQUIRED CAPABILITY DISABLED</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Stage requiring that capability cannot begin.</li>
                      <li>Configured policy determines whether the run closes or requires review.</li>
                    </ul>
                  </div>

                  {/* SECRET RESOLUTION FAILURE */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">SECRET RESOLUTION FAILURE</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Affected integration must remain unavailable.</li>
                      <li>Secret value must not be written to logs.</li>
                    </ul>
                  </div>

                  {/* EFFECTIVE CONFIGURATION CONFLICT */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">EFFECTIVE CONFIGURATION CONFLICT</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Protected stage must not run.</li>
                      <li>Conflict should remain explainable.</li>
                    </ul>
                  </div>

                  {/* CONFIGURATION CHANGED DURING RUN */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">CONFIGURATION CHANGED DURING RUN</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>An existing run should continue to reference the effective configuration under which it began.</li>
                      <li>A later run may use the newer configuration.</li>
                      <li>Do not silently reinterpret an existing result under changed configuration.</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* CONFIGURATION INVARIANTS */}
              <section className="space-y-4" aria-labelledby="config-invariants-heading">
                <h3 id="config-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Configuration Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target configuration contract defines the following configuration invariants:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">CONFIGURATION REMAINS EXPLICIT.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN SERVER-SIDE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">POLICY REMAINS DETERMINISTIC.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">MODEL AUTHORITY REMAINS ADVISORY.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION REQUIREMENTS REMAIN ENFORCED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK REMAINS AUTHORIZED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">EFFECTIVE CONFIGURATION REMAINS REFERENCED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">CONFIGURATION SUCCESS REMAINS DISTINCT FROM RUNTIME SUCCESS.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe target configuration requirements, not proof that a configuration loader, schema validator, or precedence engine has already been implemented.
                </p>
              </section>
            </section>
          ) : activeSection === 'Artifact Contracts' ? (
            <section id="artifact-contracts" aria-labelledby="artifact-contracts-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="artifact-contracts-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Artifact Contracts
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  RIFTLESS represents each review stage through explicit artifacts that preserve inputs, context, decisions, proposals, executable evidence, and permitted writeback outcomes.
                </p>
              </div>

              {/* TARGET callout */}
              <Callout type="target">
                This section describes the target artifact contract model. Field names, serialization formats, schema versions, persistence behavior, and validation rules remain illustrative until repository-backed contracts are implemented and versioned.
              </Callout>

              <hr className="border-stone-200/50" />

              {/* PRIMARY ARTIFACT CHAIN */}
              <section className="space-y-4" aria-labelledby="artifact-chain-heading">
                <h3 id="artifact-chain-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Primary Artifact Chain
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target artifact chain describes the primary records that may be produced across a review run. Artifact presence alone does not authorize the next stage, and not every run produces every artifact.
                </p>

                {/* Desktop horizontal flow */}
                <div className="hidden md:flex flex-wrap items-center justify-between gap-1 border border-stone-200 rounded p-4 bg-stone-50/50 font-mono text-[9px] font-bold text-stone-700">
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2.5 bg-white text-center shadow-sm uppercase tracking-tight">Change Request</div>
                  <div className="text-stone-400 text-sm px-1">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2.5 bg-white text-center shadow-sm uppercase tracking-tight">Context Pack</div>
                  <div className="text-stone-400 text-sm px-1">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2.5 bg-white text-center shadow-sm uppercase tracking-tight">Risk Decision</div>
                  <div className="text-stone-400 text-sm px-1">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2.5 bg-white text-center shadow-sm uppercase tracking-tight">Remediation Plan</div>
                  <div className="text-stone-400 text-sm px-1">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2.5 bg-white text-center shadow-sm uppercase tracking-tight">Validation Bundle</div>
                  <div className="text-stone-400 text-sm px-1">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2.5 bg-white text-center shadow-sm uppercase tracking-tight">Writeback Record</div>
                </div>

                {/* Mobile vertical flow */}
                <div className="md:hidden flex flex-col items-stretch gap-2 border border-stone-200 rounded p-4 bg-stone-50/50 font-mono text-[10px] font-bold text-stone-700">
                  <div className="border border-stone-200 rounded p-3 bg-white text-center shadow-sm uppercase">Change Request</div>
                  <div className="text-stone-400 text-center">&darr;</div>
                  <div className="border border-stone-200 rounded p-3 bg-white text-center shadow-sm uppercase">Context Pack</div>
                  <div className="text-stone-400 text-center">&darr;</div>
                  <div className="border border-stone-200 rounded p-3 bg-white text-center shadow-sm uppercase">Risk Decision</div>
                  <div className="text-stone-400 text-center">&darr;</div>
                  <div className="border border-stone-200 rounded p-3 bg-white text-center shadow-sm uppercase">Remediation Plan</div>
                  <div className="text-stone-400 text-center">&darr;</div>
                  <div className="border border-stone-200 rounded p-3 bg-white text-center shadow-sm uppercase">Validation Bundle</div>
                  <div className="text-stone-400 text-center">&darr;</div>
                  <div className="border border-stone-200 rounded p-3 bg-white text-center shadow-sm uppercase">Writeback Record</div>
                </div>

                {/* Supporting references */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-[10px] uppercase font-bold text-stone-700 mt-4">
                  <div className="border border-dashed border-stone-300 rounded p-3 bg-stone-50/20 text-center">
                    <span className="text-stone-500 block text-[8px] tracking-wider mb-1">Supporting Reference</span>
                    Effective Configuration Reference
                  </div>
                  <div className="border border-dashed border-stone-300 rounded p-3 bg-stone-50/20 text-center">
                    <span className="text-stone-500 block text-[8px] tracking-wider mb-1">Supporting Reference</span>
                    Authorization Record
                  </div>
                  <div className="border border-dashed border-stone-300 rounded p-3 bg-stone-50/20 text-center">
                    <span className="text-stone-500 block text-[8px] tracking-wider mb-1">Supporting Reference</span>
                    Failure Record
                  </div>
                </div>

                <div className="space-y-2 text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl pt-2">
                  <p>Invariants of the primary artifact chain:</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs text-stone-600">
                    <li>Not every run produces every primary artifact.</li>
                    <li>A remediation-free ALLOW path may not produce a Remediation Plan.</li>
                    <li>Failed validation does not produce a successful Validation Bundle.</li>
                    <li>Disabled or failed writeback does not produce a successful Writeback Record.</li>
                    <li>Supporting records may be associated with multiple stages.</li>
                  </ul>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* SHARED ARTIFACT ENVELOPE */}
              <section className="space-y-4" aria-labelledby="shared-envelope-heading">
                <h3 id="shared-envelope-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Shared Artifact Envelope
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The shared envelope is intended to record provenance, contract interpretation, predecessor relationships, and relevant filtering references without duplicating unrestricted source content.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">ARTIFACT TYPE</span>
                    <p className="text-stone-600 leading-relaxed">Identifies the contract category.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">ARTIFACT REFERENCE</span>
                    <p className="text-stone-600 leading-relaxed">Stable reference used to associate the artifact with a run and other artifacts.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">CONTRACT VERSION REFERENCE</span>
                    <p className="text-stone-600 leading-relaxed">Identifies the artifact-contract version or implementation version when available.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">RUN REFERENCE</span>
                    <p className="text-stone-600 leading-relaxed">Associates the artifact with the review run.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">CREATED STAGE</span>
                    <p className="text-stone-600 leading-relaxed">Identifies the lifecycle stage that produced the artifact.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">PRODUCER COMPONENT</span>
                    <p className="text-stone-600 leading-relaxed">Identifies the target component responsible for producing it.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">SOURCE REFERENCES</span>
                    <p className="text-stone-600 leading-relaxed">Links the artifact to predecessor inputs or external references.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">RELATED ARTIFACT REFERENCES</span>
                    <p className="text-stone-600 leading-relaxed">Links derived artifacts without embedding unrestricted predecessor content.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">STATUS</span>
                    <p className="text-stone-600 leading-relaxed">Records whether the artifact is complete, partial, failed, unavailable, or superseded when those states are implemented.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">REDACTION RECORD REFERENCE</span>
                    <p className="text-stone-600 leading-relaxed">Identifies relevant filtering or exclusion results when applicable.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">CONTENT</span>
                    <p className="text-stone-600 leading-relaxed">Contains the contract-specific permitted fields.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">LIMITATIONS OR FAILURE REASON</span>
                    <p className="text-stone-600 leading-relaxed">Records missing context, skipped processing, malformed output, or stage failure where applicable.</p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1 md:col-span-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">RECORDED TIME</span>
                    <p className="text-stone-600 leading-relaxed">May record when the artifact status was created or updated after a backend implementation defines timestamp behavior.</p>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic pt-2">
                  The shared envelope records provenance and relationships. It does not grant authorization by itself.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* SHARED ENVELOPE TABLE */}
              <section className="space-y-4" aria-labelledby="envelope-table-heading">
                <h3 id="envelope-table-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Shared Envelope Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The validation, dependency, and metadata categories shared across all artifact definitions:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="shared-envelope-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Conceptual fields shared by target RIFTLESS artifact contracts.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Field</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Required or Conditional</th>
                        <th scope="col" className="px-4 py-3">Security Constraint</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACT TYPE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify the artifact contract.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Must not be inferred solely from presentation styling.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACT REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Associate records and downstream references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Must not contain credentials.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTRACT VERSION REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify the interpreting contract version.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required when versioning exists.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Must not silently reinterpret older artifacts.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RUN REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Associate the artifact with a review run.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Must not expose authorization secrets.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">SOURCE REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify predecessor or external sources.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional by artifact type.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">References must not embed prohibited source content.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RELATED ARTIFACT REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Connect derived artifacts.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Must not imply approval or validation automatically.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">STATUS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record contract completion or failure state.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required once status modeling exists.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">UI styling must not be the source of truth.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REDACTION RECORD REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Associate relevant filtering results.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Must not contain removed secret values.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">LIMITATIONS OR FAILURE REASON</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-bold">Preserve incomplete or non-success context.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top font-bold">Must not expose prohibited logs or credentials.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* CHANGE REQUEST */}
              <section className="space-y-4" aria-labelledby="change-request-heading">
                <h3 id="change-request-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Change Request
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Normalize the proposed repository, SQL, schema, dbt, ownership, or policy change into a bounded review input:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONTENT</span>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>source type</li>
                      <li>original submitted-input reference</li>
                      <li>normalized change representation</li>
                      <li>repository reference when applicable</li>
                      <li>base and head revision references when applicable</li>
                      <li>changed-file references</li>
                      <li>SQL or schema source references</li>
                      <li>evaluated change scope</li>
                      <li>intake warnings</li>
                      <li>unsupported-input reason</li>
                      <li>effective configuration reference</li>
                    </ul>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">AUTHORITY BOUNDARY</span>
                    <p className="italic">
                      A Change Request starts a review. It does not authorize execution, validation, deployment, or writeback.
                    </p>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">PRESERVATION RULE</span>
                    <p>
                      The original submitted input should not be silently rewritten. Corrections or normalization changes should create an explicit new artifact or version reference once artifact versioning exists.
                    </p>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* CONTEXT PACK */}
              <section className="space-y-4" aria-labelledby="context-pack-heading">
                <h3 id="context-pack-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Context Pack
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Assemble bounded and redacted organizational context relevant to the proposed change:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONTENT</span>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>relevant asset references</li>
                      <li>schema references</li>
                      <li>column-lineage references</li>
                      <li>observed query-usage references</li>
                      <li>ownership references</li>
                      <li>governance-policy references</li>
                      <li>quality-signal references</li>
                      <li>declared ML-dependency references</li>
                      <li>source references</li>
                      <li>missing-context warnings</li>
                      <li>redaction record reference</li>
                      <li>evaluated context scope</li>
                    </ul>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">AUTHORITY BOUNDARY</span>
                    <p className="italic">
                      A Context Pack provides review context. It does not determine ALLOW, WARN, or BLOCK.
                    </p>
                  </div>
                </div>

                <Callout type="note">
                  More context does not automatically produce a more accurate decision. The Context Pack should remain relevant, bounded, referenced, and filtered.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* RISK DECISION */}
              <section className="space-y-4" aria-labelledby="risk-decision-heading">
                <h3 id="risk-decision-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Risk Decision
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Record the result of configured deterministic policy and contract evaluation:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">REQUIRED TARGET CONTENT</span>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>decision status: ALLOW, WARN, or BLOCK</li>
                      <li>evaluated scope</li>
                      <li>decision reasons</li>
                      <li>affected asset references</li>
                      <li>referenced policy results</li>
                      <li>missing-context effects</li>
                      <li>required acknowledgment or human action</li>
                      <li>required validation gates</li>
                      <li>predecessor Change Request reference</li>
                      <li>predecessor Context Pack reference</li>
                      <li>effective configuration reference</li>
                    </ul>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">AUTHORITY BOUNDARY</span>
                    <p className="italic">
                      The Risk Decision records deterministic policy output. A model response cannot create, replace, or clear this artifact.
                    </p>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">DETERMINISTIC EVALUATION INVARIANTS</span>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>ALLOW does not universally guarantee safety.</li>
                      <li>WARN does not automatically become approval.</li>
                      <li>BLOCK cannot be cleared by a remediation proposal.</li>
                      <li>A different result requires a new deterministic evaluation.</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* REMEDIATION PLAN */}
              <section className="space-y-4" aria-labelledby="remediation-plan-heading">
                <h3 id="remediation-plan-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Remediation Plan
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Preserve an advisory compatibility or repair proposal:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONTENT</span>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>summary</li>
                      <li>assumptions</li>
                      <li>proposed changes</li>
                      <li>affected-area hypotheses</li>
                      <li>referenced context</li>
                      <li>source references</li>
                      <li>validation recommendations</li>
                      <li>known limitations</li>
                      <li>unresolved questions</li>
                      <li>originating model-request status when applicable</li>
                      <li>predecessor Risk Decision reference</li>
                      <li>predecessor Context Pack reference</li>
                    </ul>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">AUTHORITY BOUNDARY</span>
                    <p className="italic">
                      A Remediation Plan is advisory. It is not authorization, executable evidence, deployment approval, or proof that the proposal is correct.
                    </p>
                  </div>
                </div>

                <Callout type="warning">
                  A syntactically plausible proposal remains unverified until configured executable validation produces evidence within a recorded scope.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* VALIDATION BUNDLE */}
              <section className="space-y-4" aria-labelledby="validation-bundle-heading">
                <h3 id="validation-bundle-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validation Bundle
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Record executable validation evidence produced within a bounded test scope:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONTENT</span>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>proposed change or remediation reference</li>
                      <li>configured validators</li>
                      <li>executed-command references</li>
                      <li>execution-environment details</li>
                      <li>test inputs or fixture references</li>
                      <li>logs or log references</li>
                      <li>individual validator outcomes</li>
                      <li>overall validation outcome</li>
                      <li>tested-scope statement</li>
                      <li>skipped-validator list and reasons</li>
                      <li>failure reason when applicable</li>
                      <li>artifact references</li>
                      <li>effective configuration reference</li>
                    </ul>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">AUTHORITY BOUNDARY</span>
                    <p className="italic">
                      A Validation Bundle provides evidence. It does not independently authorize production deployment or metadata writeback.
                    </p>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">VALIDATION RESULTS RULE</span>
                    <p>
                      A failed validation result must not be represented as a successful Validation Bundle.
                    </p>
                  </div>
                </div>

                <Callout type="warning">
                  A successful Validation Bundle means the configured validators passed within the recorded scope. It is not a universal guarantee that no downstream failure can occur.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* WRITEBACK RECORD */}
              <section className="space-y-4" aria-labelledby="writeback-record-heading">
                <h3 id="writeback-record-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Writeback Record
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Record the result of a permitted metadata-writeback attempt after required authorization is available:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">TARGET CONTENT</span>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>authorization-record reference</li>
                      <li>Risk Decision reference</li>
                      <li>Validation Bundle or failure-result reference</li>
                      <li>configured destination reference</li>
                      <li>conceptual mapping reference</li>
                      <li>requested record categories</li>
                      <li>accepted record categories</li>
                      <li>rejected record categories</li>
                      <li>target asset references</li>
                      <li>writeback outcome</li>
                      <li>failure reason</li>
                      <li>resulting metadata references when available</li>
                      <li>artifact references</li>
                    </ul>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">AUTHORITY BOUNDARY</span>
                    <p className="italic">
                      The Writeback Record reports writeback outcome. Its presence does not create authorization retroactively.
                    </p>
                  </div>

                  <div className="h-px bg-stone-100" />

                  <div className="text-xs text-stone-700 leading-relaxed space-y-2">
                    <span className="font-mono text-[10px] text-stone-500 font-bold block uppercase">WRITEBACK OUTCOME RULES</span>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>Authorization success is distinct from writeback success.</li>
                      <li>An attempted writeback is distinct from a completed writeback.</li>
                      <li>Failed writeback must not be reported as successful.</li>
                      <li>Advisory model output must not be stored as verified evidence.</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* SUPPORTING RECORDS */}
              <section className="space-y-4" aria-labelledby="supporting-records-heading">
                <h3 id="supporting-records-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Supporting Records
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target artifact model includes three supporting record types for effective configuration, protected-transition authorization, and stage or integration failure.
                </p>

                <div className="space-y-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">A. EFFECTIVE CONFIGURATION REFERENCE</h4>
                    <p className="text-stone-500 font-bold uppercase text-[9px]">PURPOSE: Identify the effective configuration used by a run without storing credentials.</p>
                    <div className="text-stone-600 leading-relaxed space-y-1.5">
                      <span>May reference:</span>
                      <ul className="list-disc pl-4">
                        <li>configuration implementation or contract version</li>
                        <li>project configuration reference</li>
                        <li>permitted override reference</li>
                        <li>enabled capability set</li>
                        <li>policy references</li>
                        <li>validator categories</li>
                        <li>redaction-policy reference</li>
                        <li>writeback enabled state</li>
                      </ul>
                    </div>
                  </div>

                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">B. AUTHORIZATION RECORD</h4>
                    <p className="text-stone-500 font-bold uppercase text-[9px]">PURPOSE: Record that the control plane permitted a protected transition or operation after required predecessor states were available.</p>
                    <div className="text-stone-600 leading-relaxed space-y-1.5">
                      <span>May include:</span>
                      <ul className="list-disc pl-4">
                        <li>authorized operation</li>
                        <li>predecessor artifact references</li>
                        <li>policy-result references</li>
                        <li>required validation outcome reference</li>
                        <li>recorded authorization state</li>
                        <li>limitations or expiration behavior only after implementation defines them</li>
                      </ul>
                      <p className="italic text-amber-800 font-mono text-[10px] bg-amber-50/50 p-2 border border-amber-100 rounded">
                        MUST NOT IMPLY: cryptographic signature, authorization token format, identity-provider integration, blockchain, or ledger.
                      </p>
                    </div>
                  </div>

                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-sm font-mono font-bold text-stone-900 uppercase">C. FAILURE RECORD</h4>
                    <p className="text-stone-500 font-bold uppercase text-[9px]">PURPOSE: Record why a stage or integration could not complete.</p>
                    <div className="text-stone-600 leading-relaxed space-y-1.5">
                      <span>May include:</span>
                      <ul className="list-disc pl-4">
                        <li>failed stage</li>
                        <li>failure category</li>
                        <li>failure reason</li>
                        <li>available predecessor references</li>
                        <li>partial artifact references</li>
                        <li>permitted diagnostic references</li>
                        <li>target retry eligibility when defined</li>
                      </ul>
                      <p className="font-semibold text-stone-900">
                        A Failure Record should not erase or overwrite previously captured artifacts.
                      </p>
                    </div>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* CONTRACT RESPONSIBILITY TABLE */}
              <section className="space-y-4" aria-labelledby="contract-responsibility-heading">
                <h3 id="contract-responsibility-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Contract Responsibility Table
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The following matrix outlines target responsibilities and evidence scopes assigned to each artifact:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-6">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="contract-responsibility-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target RIFTLESS artifact contracts, producers, evidence roles, and authority boundaries.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Artifact</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Target Producer</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Primary Responsibility</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Evidence Role</th>
                        <th scope="col" className="px-4 py-3">Authority Boundary</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CHANGE REQUEST</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Change intake.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Normalize the proposed change.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Preserves input and source references.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">No execution authority.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTEXT PACK</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Context Pack Builder.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Assemble bounded organizational context.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Supplies referenced review context.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">No decision authority.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK DECISION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Deterministic Risk Engine.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record ALLOW, WARN, or BLOCK with reasons.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Preserves deterministic policy results.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Controls protected advancement within configured policy.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">REMEDIATION PLAN</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Advisory remediation planner.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Propose compatible changes and assumptions.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Advisory artifact only.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">No authorization role.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION BUNDLE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Isolated Validation Worker.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record executable validation results.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Executable evidence within tested scope.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Does not authorize deployment independently.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">WRITEBACK RECORD</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured Writeback Adapter.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top font-bold">Record metadata-writeback outcome.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Records writeback result and target references.</td>
                        <td className="px-4 py-3 text-stone-900 font-bold align-top">Writes only after recorded authorization.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              {/* TARGET CONTRACT SHAPE */}
              <section className="space-y-4" aria-labelledby="target-contract-shape-heading">
                <h3 id="target-contract-shape-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Contract Shape
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The structured layout representing the conceptual RIFTLESS YAML format:
                </p>

                <div className="space-y-2 max-w-xl">
                  <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                    ILLUSTRATIVE ARTIFACT SHAPE <span className="text-stone-400 font-normal">(NON-EXECUTABLE)</span>
                  </span>
                  <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`# Illustrative artifact shape only.
# Field names are not yet repository-backed.

artifact:
  type: "<artifact-type>"
  reference: "<artifact-reference>"
  contract_version: "<contract-version-reference>"
  run_reference: "<run-reference>"
  created_stage: "<lifecycle-stage>"
  producer: "<target-producer-component>"
  status: "<artifact-status>"

  source_references:
    - "<source-reference>"

  related_artifact_references:
    - "<artifact-reference>"

  redaction_record_reference: "<optional-reference>"

  content:
    "<contract-specific-field>": "<permitted-value>"

  limitations:
    - "<limitation-or-failure-reason>"`}
                  </pre>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* REFERENCE AND VERSIONING RULES */}
              <section className="space-y-4" aria-labelledby="reference-versioning-heading">
                <h3 id="reference-versioning-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Reference and Versioning Rules
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  All recorded references and schema versioning strategies are designed to support audit and reproducibility requirements across a run lifecycle.
                </p>

                <ul className="list-disc pl-5 space-y-1.5 text-xs text-stone-700 leading-relaxed max-w-2xl pt-2">
                  <li>Derived artifacts should reference relevant predecessors.</li>
                  <li>References should remain stable after being recorded.</li>
                  <li>Corrections should not silently rewrite historical meaning.</li>
                  <li>Superseded artifacts should remain distinguishable from current artifacts.</li>
                  <li>Contract version should determine how an artifact is interpreted.</li>
                  <li>Older artifacts should not be silently interpreted using incompatible newer semantics.</li>
                  <li>Missing required predecessor references should produce an explicit contract result.</li>
                  <li>External references should retain enough source context for explanation.</li>
                  <li>References must not embed credentials or prohibited content.</li>
                </ul>

                <Callout type="target">
                  The final identifier, versioning, migration, and compatibility strategy must be derived from the implemented artifact schema. No identifier or migration behavior in this section is executable yet.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET ARTIFACT VALIDATION */}
              <section className="space-y-4" aria-labelledby="artifact-validation-heading">
                <h3 id="artifact-validation-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Artifact Validation
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The structural guardian validates generated artifact properties against rules grouped into five target areas:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="text-[10px] font-mono bg-stone-100 text-stone-800 font-bold px-2 py-0.5 rounded uppercase">Structure Validation</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li>Checks expected contract type.</li>
                      <li>Checks required shared-envelope fields.</li>
                      <li>Checks expected field shapes.</li>
                      <li>Checks permitted status values once schema exists.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="text-[10px] font-mono bg-stone-100 text-stone-800 font-bold px-2 py-0.5 rounded uppercase">Reference Validation</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li>Checks required predecessor references exist.</li>
                      <li>Checks related artifact types are permitted.</li>
                      <li>Checks run references are consistent.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="text-[10px] font-mono bg-stone-100 text-stone-800 font-bold px-2 py-0.5 rounded uppercase">Authority Validation</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li>Checks Remediation Plan is not treated as authorization.</li>
                      <li>Checks Validation Bundle is not treated as writeback authorization.</li>
                      <li>Checks Writeback Record has recorded authorization reference.</li>
                      <li>Checks model output does not create Risk Decision.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="text-[10px] font-mono bg-stone-100 text-stone-800 font-bold px-2 py-0.5 rounded uppercase">Redaction Validation</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li>Checks prohibited credentials are absent.</li>
                      <li>Checks unrestricted logs are not embedded.</li>
                      <li>Checks secret values are not copied into failure reasons.</li>
                      <li>Checks model-context artifacts contain only permitted data.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2">
                    <span className="text-[10px] font-mono bg-stone-100 text-stone-800 font-bold px-2 py-0.5 rounded uppercase">State Consistency</span>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600">
                      <li>Checks failed validation does not claim VALIDATED.</li>
                      <li>Checks BLOCK does not claim permitted writeback.</li>
                      <li>Checks failed writeback does not claim completion.</li>
                      <li>Checks stale or superseded artifacts are distinguishable.</li>
                    </ul>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic pt-2">
                  These are target validation categories. No automated schema validator or verification service is running in this workspace.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* ARTIFACT CONTENT BOUNDARY */}
              <section className="space-y-4" aria-labelledby="content-boundary-heading">
                <h3 id="content-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Artifact Content Boundary
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Artifact values must be strictly partitioned to ensure sensitive or prohibited context does not leak into recorded outputs:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                  {/* MAY BE PRESERVED WHEN PERMITTED */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-[#A8CD16] tracking-wider uppercase">MAY BE PRESERVED WHEN PERMITTED</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>normalized change content</li>
                      <li>bounded context references</li>
                      <li>deterministic decision reasons</li>
                      <li>remediation assumptions</li>
                      <li>executable-test results</li>
                      <li>tested-scope statement</li>
                      <li>failure reasons</li>
                      <li>permitted artifact and target references</li>
                    </ul>
                  </div>

                  {/* MUST NOT BE PRESERVED IN ORDINARY ARTIFACT CONTENT */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <h4 className="text-xs font-mono font-bold text-red-600 tracking-wider uppercase">MUST NOT BE PRESERVED IN ORDINARY ARTIFACT CONTENT</h4>
                    <ul className="list-disc pl-4 space-y-1.5 text-xs text-stone-700 leading-relaxed">
                      <li>API credentials</li>
                      <li>access tokens</li>
                      <li>private keys</li>
                      <li>raw authorization headers</li>
                      <li>secret environment values</li>
                      <li>unrestricted repository exports</li>
                      <li>unrestricted metadata exports</li>
                      <li>unrelated sensitive data</li>
                      <li>provider credentials</li>
                      <li>browser session secrets</li>
                    </ul>
                  </div>
                </div>

                <Callout type="warning">
                  A diagnostic value is not safe merely because it appears in a log or error message. Artifact filtering must evaluate content before persistence.
                </Callout>

                <Callout type="note">
                  Runtime tests should verify that prohibited values are rejected or removed before artifacts are stored or exposed.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* ARTIFACT CONTRACT FAILURE BEHAVIOR */}
              <section className="space-y-4" aria-labelledby="artifact-failure-heading">
                <h3 id="artifact-failure-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Artifact Contract Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target artifact contract defines non-success outcomes and handling categories for core artifact operations:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl">
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">MALFORMED ARTIFACT</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Artifact should be rejected or marked invalid.</li>
                      <li>Protected next stage must not infer success.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">MISSING REQUIRED REFERENCE</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Relationship remains unresolved.</li>
                      <li>Dependent protected transition must not proceed.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">UNSUPPORTED CONTRACT VERSION</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Artifact must not be silently reinterpreted.</li>
                      <li>Explicit compatibility result should be recorded.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">AUTHORITY CONFLICT</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Remediation Plan presented as authorization.</li>
                      <li>Failed Validation Bundle presented as validated.</li>
                      <li>Writeback Record lacks authorization reference.</li>
                      <li>Contract is rejected and protected transition does not proceed.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">REDACTION FAILURE</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Artifact must not be persisted or exposed with prohibited values.</li>
                      <li>Failure reason should be recorded without reproducing the secret.</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-5 bg-white space-y-2">
                    <h4 className="text-xs font-mono font-bold text-stone-900 uppercase">ARTIFACT STORAGE UNAVAILABLE</h4>
                    <ul className="list-disc pl-4 space-y-1 text-xs text-stone-600 leading-relaxed">
                      <li>Artifact must not be reported as successfully preserved.</li>
                      <li>Stage result and storage success remain distinct.</li>
                      <li>Retry handling remains undefined until implementation.</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* ARTIFACT INVARIANTS */}
              <section className="space-y-4" aria-labelledby="artifact-invariants-heading">
                <h3 id="artifact-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Artifact Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  All target artifact properties must adhere strictly to these conceptual invariants:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">INPUT REFERENCES REMAIN TRACEABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">CONTEXT REMAINS BOUNDED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">DECISIONS REMAIN EXPLAINABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS ADVISORY.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION EVIDENCE REMAINS SCOPE-BOUND.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">AUTHORIZATION REMAINS EXPLICIT.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK OUTCOME REMAINS DISTINCT FROM AUTHORIZATION.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">FAILURE REMAINS REPRESENTABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">SECRETS REMAIN EXCLUDED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">CONTRACT VERSION REMAINS IDENTIFIABLE.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe planned target capabilities. No artifact persistence, schema validation, version migration, or cloud storage adapter is active in this workspace.
                </p>
              </section>
            </section>
          ) : activeSection === 'Risk Decisions' ? (
            <section id="risk-decisions" aria-labelledby="risk-decisions-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <h2 id="risk-decisions-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Risk Decisions
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  A target RIFTLESS Risk Decision records the result of configured deterministic policy evaluation for a bounded proposed change and its available Context Pack.
                </p>
              </div>

              {/* TARGET callout */}
              <Callout type="target">
                This section describes the target deterministic decision contract. Rule identifiers, evaluation order, policy syntax, severity mapping, and runtime behavior remain illustrative until a repository-backed risk engine is implemented and versioned.
              </Callout>

              <hr className="border-stone-200/50" />

              {/* STATIC FLOW DIAGRAM */}
              <section className="space-y-4" aria-labelledby="risk-flow-heading">
                <h3 id="risk-flow-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Risk Decision Flow
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target decision flow evaluates permitted inputs through configured deterministic policy before producing a Risk Decision.
                </p>

                {/* Desktop horizontal flow */}
                <div className="hidden md:flex flex-wrap items-center justify-between gap-1 border border-stone-200 rounded p-4 bg-stone-50/50 font-mono text-[9px] font-bold text-stone-700 max-w-4xl">
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">CHANGE REQUEST</div>
                  <div className="text-stone-400 text-xs font-bold px-0.5" aria-hidden="true">+</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">REDACTED CONTEXT PACK</div>
                  <div className="text-stone-400 text-xs font-bold px-0.5" aria-hidden="true">+</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">EFFECTIVE CONFIGURATION REF</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-stone-800 text-stone-100 text-center shadow-sm uppercase tracking-tight">DETERMINISTIC POLICY EVALUATION</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">DECISION REASONS</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">AFFECTED ASSET REFS</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">ALLOW / WARN / BLOCK</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-stone-900 text-white text-center shadow-sm uppercase tracking-tight">REQUIRED NEXT ACTION</div>
                </div>

                {/* Mobile Flow Sequence */}
                <div className="md:hidden space-y-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px]">
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">CHANGE REQUEST</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">+</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">REDACTED CONTEXT PACK</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">+</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">EFFECTIVE CONFIGURATION REF</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-stone-800 text-stone-100 font-bold shadow-sm text-center uppercase">DETERMINISTIC POLICY EVALUATION</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">DECISION REASONS</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">AFFECTED ASSET REFS</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">ALLOW / WARN / BLOCK</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-stone-900 text-white font-bold shadow-sm text-center uppercase">REQUIRED NEXT ACTION</div>
                </div>

                {/* Blocked Path Callout / Box */}
                <div className="border border-red-200 bg-red-50/50 rounded p-4 max-w-xl space-y-2">
                  <div className="font-mono text-[10px] font-bold text-red-700 tracking-wider uppercase flex items-center gap-1.5">
                    <span>Blocked Path: Model Response &times; Risk Authorization</span>
                  </div>
                  <div className="text-xs text-red-800 leading-relaxed font-mono">
                    MODEL RESPONSE <span className="font-sans font-normal text-stone-600 mx-1">cannot fulfill or replace</span> RISK AUTHORIZATION <span className="mx-1">&rarr;</span> <span className="bg-red-200 text-red-900 font-bold px-1.5 py-0.5 rounded text-[10px]">BLOCKED</span>
                  </div>
                  <p className="text-xs text-stone-600 leading-relaxed">
                    Model outputs cannot serve as policy authority or authorize state progression. Risk evaluation remains strictly deterministic.
                  </p>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* AUTHORITY MODEL */}
              <section className="space-y-4" aria-labelledby="authority-model-heading">
                <h3 id="authority-model-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Authority Model
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The deterministic Risk Decision represents the configured policy result. Model confidence, persuasive language, or syntactically valid SQL cannot replace it.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      DETERMINISTIC RISK ENGINE
                    </span>
                    <hr className="border-stone-100" />
                    <ul className="list-disc pl-4 text-stone-600 space-y-1.5">
                      <li>Evaluate configured policy and contract rules</li>
                      <li>Record conceptual rule results</li>
                      <li>Identify affected assets from available context</li>
                      <li>Produce decision reasons</li>
                      <li>Assign ALLOW, WARN, or BLOCK</li>
                      <li>Identify required acknowledgment or validation gates</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      DEEPSEEK
                    </span>
                    <hr className="border-stone-100" />
                    <ul className="list-disc pl-4 text-stone-600 space-y-1.5">
                      <li>Explain proposed changes</li>
                      <li>Propose remediation</li>
                      <li>Expose assumptions</li>
                      <li>Suggest validation ideas</li>
                      <li className="font-bold text-stone-800">Advisory only</li>
                      <li className="font-bold text-stone-800">Cannot create or clear a Risk Decision</li>
                      <li className="font-bold text-stone-800">Cannot convert WARN or BLOCK into ALLOW</li>
                      <li className="font-bold text-stone-800">Cannot authorize validation or writeback</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      CONTROL PLANE
                    </span>
                    <hr className="border-stone-100" />
                    <ul className="list-disc pl-4 text-stone-600 space-y-1.5">
                      <li>Provide permitted evaluation inputs</li>
                      <li>Invoke configured deterministic evaluation</li>
                      <li>Record the target decision result when implementation exists</li>
                      <li>Enforce protected transition requirements</li>
                      <li>Request reevaluation after relevant input changes</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* DECISION INPUTS */}
              <section className="space-y-4" aria-labelledby="inputs-heading">
                <h3 id="inputs-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Evaluation Inputs
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target deterministic evaluation may use four input groups, depending on the configured policy and available context.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CHANGE REQUEST</span>
                    <p className="text-stone-500 italic">May provide:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Normalized proposed change</li>
                      <li>Source references</li>
                      <li>Evaluated change scope</li>
                      <li>Repository or revision references when applicable</li>
                      <li>Intake warnings</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CONTEXT PACK</span>
                    <p className="text-stone-500 italic">May provide:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Schema references</li>
                      <li>Lineage references</li>
                      <li>Usage references</li>
                      <li>Ownership references</li>
                      <li>Governance references</li>
                      <li>Quality signals</li>
                      <li>Declared dependencies</li>
                      <li>Missing-context warnings</li>
                      <li>Redaction record reference</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">EFFECTIVE CONFIGURATION REFERENCE</span>
                    <p className="text-stone-500 italic">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Selected risk-policy reference</li>
                      <li>Contract-rule references</li>
                      <li>Acknowledgment requirements</li>
                      <li>Required validation gates</li>
                      <li>Enabled capability boundaries</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PREVIOUS DECISION OR VALIDATION REFERENCES</span>
                    <p className="text-stone-500 italic">Conditional only when:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>The change is being reevaluated</li>
                      <li>Remediation was revised</li>
                      <li>Previous validation failed</li>
                      <li>Configured policy permits historical references</li>
                    </ul>
                  </div>
                </div>

                <div className="border-l-4 border-amber-300 bg-amber-50/50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed">
                  <strong>Clarification:</strong> Previous model output is not an authorization input. It may be referenced only as advisory proposal context.
                </div>

                <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="evaluation-inputs-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target inputs used by deterministic RIFTLESS risk evaluation.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Input</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Review Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Required or Conditional</th>
                        <th scope="col" className="px-4 py-3 w-1/4">Authority Constraint</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CHANGE REQUEST</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Describe the bounded proposed change.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Does not authorize advancement by itself.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">CONTEXT PACK</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide relevant referenced organizational context.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required when configured policy depends on contextual evaluation.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Context does not determine the decision independently.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">EFFECTIVE CONFIGURATION REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify selected deterministic policy and protected-transition requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configuration defines requirements but is not a completed decision.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PREVIOUS RISK DECISION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Support explicit comparison or reevaluation.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">A previous result must not automatically apply to changed input.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION OUTCOME REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide permitted evidence context during reevaluation.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Validation evidence does not create policy authorization independently.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* STATUS CONTRACT */}
              <section className="space-y-4" aria-labelledby="status-contract-heading">
                <h3 id="status-contract-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Status Contract
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target decision contract defines three deterministic statuses that may be assigned after configured policy evaluation.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl text-xs">
                  {/* ALLOW */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded uppercase">ALLOW</span>
                    </div>
                    <div className="space-y-1">
                      <span className="font-semibold text-stone-900 block">Meaning:</span>
                      <p className="text-stone-700 leading-relaxed italic">
                        &ldquo;No configured blocking rule was triggered within the evaluated scope.&rdquo;
                      </p>
                    </div>
                    <div className="space-y-1 pt-1">
                      <span className="font-semibold text-stone-900 block">Target Behavior:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>Run may advance according to configured policy</li>
                        <li>Required validation must still occur where configured</li>
                        <li>Writeback still requires recorded authorization</li>
                        <li>Evaluated scope and decision reasons remain recorded</li>
                        <li>ALLOW is not a universal safety guarantee</li>
                      </ul>
                    </div>
                  </div>

                  {/* WARN */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded uppercase">WARN</span>
                    </div>
                    <div className="space-y-1">
                      <span className="font-semibold text-stone-900 block">Meaning:</span>
                      <p className="text-stone-700 leading-relaxed italic">
                        &ldquo;Identified impact requires acknowledgment, policy-defined review, or additional action before protected later stages.&rdquo;
                      </p>
                    </div>
                    <div className="space-y-1 pt-1">
                      <span className="font-semibold text-stone-900 block">Target Behavior:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>The specific triggers and actions required under a WARN state are determined by active configured policy</li>
                        <li>Does not represent an automatic human approval or arbitrary low severity categorization</li>
                        <li>A recorded acknowledgment or human-review result may be required before a protected later stage when configured policy requires it.</li>
                      </ul>
                    </div>
                  </div>

                  {/* BLOCK */}
                  <div className="border border-stone-200 rounded p-5 bg-white space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono bg-red-100 text-red-800 font-bold px-2 py-0.5 rounded uppercase">BLOCK</span>
                    </div>
                    <div className="space-y-1">
                      <span className="font-semibold text-stone-900 block">Meaning:</span>
                      <p className="text-stone-700 leading-relaxed italic">
                        &ldquo;A configured policy or contract rule prevents the run from advancing.&rdquo;
                      </p>
                    </div>
                    <div className="space-y-1 pt-1">
                      <span className="font-semibold text-stone-900 block">Target Behavior:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>Protected validation or writeback must not advance</li>
                        <li>Remediation may be proposed when configured</li>
                        <li>Change must be revised or reevaluated</li>
                        <li>Model output cannot clear BLOCK</li>
                        <li>Only a new deterministic evaluation may produce a different decision</li>
                        <li>Applies to any blocking condition, regardless of original severity classifications</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* RULE RESULT MODEL */}
              <section className="space-y-4" aria-labelledby="rule-result-model-heading">
                <h3 id="rule-result-model-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Rule Result Model
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Rather than hardcoded pass/fail schemas, individual rules evaluate to one of five conceptual states:
                </p>

                <div className="overflow-x-auto border border-stone-200 rounded my-4 max-w-4xl">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="rule-result-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Conceptual Rule Result States
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Rule Result</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Meaning</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200">Decision Effect</th>
                        <th scope="col" className="px-4 py-3">Required Record</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-emerald-700 bg-emerald-50/10 text-left align-top">MATCHED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A configured rule condition matched the evaluated inputs.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured policy determines whether the matched condition contributes to ALLOW, WARN, or BLOCK.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Rule reference, matched condition, effect, and reason when available.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-700 bg-stone-50/10 text-left align-top">NOT MATCHED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">The condition was evaluated and did not match.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured policy determines the effect. A rule may represent a prohibited condition or a required condition.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Rule reference and evaluation reason when required for explainability.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-700 bg-stone-50/10 text-left align-top">NOT EVALUATED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">The rule was outside the configured scope or a prerequisite was unavailable.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured policy determines whether evaluation may continue. Missing prerequisites must remain visible.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Rule reference and reason the rule was not evaluated.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-amber-700 bg-amber-50/10 text-left align-top">INDETERMINATE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Available inputs were insufficient to determine the result.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured policy determines how indeterminate state affects overall decision.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Missing input, unresolved condition, or evaluation limitation.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-red-700 bg-red-50/10 text-left align-top">ERROR</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">The rule could not complete because of configuration, parsing, or runtime failure.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Must not silently become ALLOW. Protected advancement must not infer successful evaluation.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Failure category and permitted diagnostic reference.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="border border-stone-200 rounded p-4 bg-stone-50/50 max-w-3xl space-y-1.5 text-xs font-mono text-stone-700">
                  <div className="font-bold text-stone-900 mb-1 uppercase tracking-wider text-[10px]">Rule Logic Clarifications:</div>
                  <ul className="list-disc pl-5 space-y-1 font-sans">
                    <li><span className="font-mono text-[11px] font-bold">NOT MATCHED</span> is not the same as <span className="font-mono text-[11px] font-bold">NOT EVALUATED</span>.</li>
                    <li>Missing context must not silently become a passing result.</li>
                    <li>An <span className="font-mono text-[11px] font-bold">ERROR</span> must not silently become <span className="font-mono text-[11px] font-bold">ALLOW</span>.</li>
                    <li>Configured policy determines how <span className="font-mono text-[11px] font-bold">INDETERMINATE</span> affects the decision.</li>
                  </ul>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* POLICY CATEGORIES */}
              <section className="space-y-4" aria-labelledby="policy-categories-heading">
                <h3 id="policy-categories-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Policy Categories
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Rules are classified into logical conceptual policy domains:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl text-xs">
                  {/* STRUCTURAL COMPATIBILITY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">STRUCTURAL COMPATIBILITY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Field removal</li>
                      <li>Type compatibility</li>
                      <li>Schema shape changes</li>
                      <li>Rename behavior</li>
                      <li>Contract-required fields</li>
                    </ul>
                  </div>

                  {/* LINEAGE IMPACT */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">LINEAGE IMPACT</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Downstream asset references</li>
                      <li>Dependency paths</li>
                      <li>Transformation relationships</li>
                    </ul>
                  </div>

                  {/* OBSERVED USAGE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">OBSERVED USAGE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Relevant query references</li>
                      <li>Configured usage signals</li>
                    </ul>
                  </div>

                  {/* GOVERNANCE AND CLASSIFICATION */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">GOVERNANCE &amp; CLASSIFICATION</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Handling policies</li>
                      <li>Governance tags</li>
                      <li>Restricted conditions</li>
                      <li>Acknowledgment requirements</li>
                    </ul>
                  </div>

                  {/* OWNERSHIP AND REVIEW */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">OWNERSHIP AND REVIEW</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Owner presence</li>
                      <li>Review requirements</li>
                      <li>Owner-action routing</li>
                    </ul>
                  </div>

                  {/* VALIDATION REQUIREMENTS */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION REQUIREMENTS</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Required validators</li>
                      <li>Required test scope</li>
                      <li>Validation bypass prevention</li>
                    </ul>
                  </div>

                  {/* WRITEBACK CONDITIONS */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2 lg:col-span-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">WRITEBACK CONDITIONS</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Required authorization</li>
                      <li>Evidence references</li>
                      <li>Prohibited writeback conditions</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* MISSING CONTEXT BEHAVIOR */}
              <section className="space-y-4" aria-labelledby="missing-context-heading">
                <h3 id="missing-context-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Missing Context Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Missing context remains an evaluation limitation. Its final effect must be determined by configured deterministic policy:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">OPTIONAL CONTEXT MISSING</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Available context may remain usable</li>
                      <li>Missing category should remain visible</li>
                      <li>Configured policy determines whether evaluation may continue</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REQUIRED CONTEXT MISSING</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Affected rules must not silently pass</li>
                      <li>Evaluation may become INDETERMINATE or fail</li>
                      <li>Protected advancement must not infer ALLOW</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">CONTEXT REFERENCE STALE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Stale status should be recorded when detectable</li>
                      <li>A current decision must not silently rely on an invalid reference</li>
                      <li>Configured policy determines whether refresh or closure is required</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* ACKNOWLEDGMENT AND HUMAN REVIEW */}
              <section className="space-y-4" aria-labelledby="human-review-heading">
                <h3 id="human-review-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Acknowledgment and Human Review
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A WARN path may require a recorded acknowledgment or human-review result when configured policy requires it.
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-5 max-w-2xl text-xs space-y-3">
                  <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                    Target Acknowledgment References:
                  </span>
                  <ul className="list-disc pl-4 text-stone-600 space-y-1">
                    <li>Risk Decision</li>
                    <li>Warning reasons</li>
                    <li>Affected assets</li>
                    <li>Configured reviewer or owner reference when available</li>
                    <li>Acknowledgment result</li>
                    <li>Required follow-up</li>
                    <li>Limitations</li>
                  </ul>

                  <hr className="border-stone-200" />

                  <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                    Rule Clarifications:
                  </span>
                  <ul className="list-disc pl-4 text-stone-600 space-y-1">
                    <li>Acknowledgment does not rewrite the Risk Decision</li>
                    <li>Acknowledgment does not convert WARN into ALLOW</li>
                    <li>Acknowledgment may permit a later stage only when configured policy allows</li>
                    <li>Model output cannot provide acknowledgment</li>
                    <li>UI interaction alone is not the source of truth</li>
                  </ul>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* REEVALUATION AND SUPERSESSION */}
              <section className="space-y-4" aria-labelledby="reevaluation-heading">
                <h3 id="reevaluation-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Reevaluation and Supersession
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A recorded Risk Decision should not be silently overwritten. A revised input requires a new deterministic evaluation and a distinguishable successor decision once artifact versioning exists.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                      New Evaluation Required When:
                    </span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Proposed change changes</li>
                      <li>Revision boundary changes</li>
                      <li>Relevant Context Pack scope changes</li>
                      <li>Selected policy changes</li>
                      <li>Remediation is revised</li>
                      <li>Required missing context becomes available</li>
                      <li>Evidence becomes stale</li>
                      <li>Failed validation leads to a revised proposal</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                      Reevaluation Clarifications:
                    </span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Previous decision remains referenced</li>
                      <li>Successor identifies evaluated inputs</li>
                      <li>Current and superseded decisions remain distinguishable</li>
                      <li>Old ALLOW does not automatically apply to changed input</li>
                      <li>Model proposal alone is not reevaluation</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET RISK DECISION SHAPE */}
              <section className="space-y-4" aria-labelledby="risk-contract-shape-heading">
                <h3 id="risk-contract-shape-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Risk Decision Shape
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The structured layout representing the conceptual Risk Decision interface:
                </p>

                <div className="space-y-2 max-w-xl">
                  <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                    CONCEPTUAL RISK EVALUATION <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                  </span>
                  <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive normalized Change Request
receive permitted Context Pack
receive effective policy references
evaluate configured deterministic rules
record conceptual rule results
identify affected assets
assemble decision reasons
assign ALLOW, WARN, or BLOCK
record required next actions
return target Risk Decision artifact`}
                  </pre>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
                  Exact rule-engine APIs, policy formats, field names, evaluation order, and decision payloads will be documented after the deterministic risk engine is implemented and versioned.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* DECISION VALIDATION */}
              <section className="space-y-4" aria-labelledby="decision-validation-heading">
                <h3 id="decision-validation-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Decision Validation
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target decision contract defines conceptual validation requirements. This does not imply that a decision-schema validator already exists.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">INPUT CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Change Request reference exists</li>
                      <li>Required Context Pack reference exists</li>
                      <li>Effective configuration reference exists</li>
                      <li>Evaluated scope remains identifiable</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RULE CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Configured rules have explicit results</li>
                      <li>NOT EVALUATED and INDETERMINATE remain visible</li>
                      <li>Rule errors do not silently pass</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">STATUS CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>BLOCK is not shown as allowed to advance</li>
                      <li>WARN does not appear as final approval</li>
                      <li>ALLOW includes evaluated-scope limitations</li>
                      <li>Missing required context does not silently produce ALLOW</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHORITY CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Model output does not create or clear the decision</li>
                      <li>Acknowledgment does not rewrite deterministic status</li>
                      <li>Validation evidence does not replace Risk Decision</li>
                      <li>Writeback status does not create risk authorization</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* FAILURE BEHAVIOR */}
              <section className="space-y-4" aria-labelledby="decision-failure-heading">
                <h3 id="decision-failure-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target decision contract defines non-success behavior when deterministic evaluation or decision recording cannot complete.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">POLICY CONFIGURATION UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Deterministic evaluation cannot begin</li>
                      <li>No decision status is fabricated</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REQUIRED INPUT MISSING</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Affected evaluation remains incomplete</li>
                      <li>Protected advancement must not infer ALLOW</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RULE EVALUATION ERROR</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Error should be recorded</li>
                      <li>Configured policy determines whether evaluation fails or becomes indeterminate</li>
                      <li>Error must not silently become success</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AFFECTED ASSET RESOLUTION INCOMPLETE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Limitation should remain visible</li>
                      <li>Configured policy determines whether evaluation may continue</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DECISION RECORD INVALID</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Protected next stage must not proceed</li>
                      <li>UI must not infer status from styling</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DECISION PERSISTENCE UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Decision must not be reported as successfully recorded</li>
                      <li>Evaluated result and persistence success remain distinct</li>
                      <li>Later authorization must not rely on an unavailable record</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* INVARIANTS */}
              <section className="space-y-4" aria-labelledby="decision-invariants-heading">
                <h3 id="decision-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Risk Decision Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target Risk Decision contract defines the following decision invariants:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">INPUT SCOPE REMAINS IDENTIFIABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">CONTEXT LIMITATIONS REMAIN VISIBLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">POLICY RESULTS REMAIN EXPLAINABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS ADVISORY.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">ALLOW REMAINS SCOPE-BOUND.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WARN REMAINS NON-AUTHORIZING.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">BLOCK REMAINS NON-BYPASSABLE BY PROPOSAL.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">REEVALUATION REMAINS DETERMINISTIC.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK REMAINS SEPARATELY AUTHORIZED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">DECISION RECORDING SUCCESS REMAINS EXPLICIT.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe target decision requirements, not proof that a policy engine, decision validator, artifact persistence layer, or immutable history system has already been implemented.
                </p>
              </section>
            </section>
          ) : activeSection === 'Validation' ? (
            <section id="validation" aria-labelledby="validation-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
                  REFERENCE
                </span>
                <h2 id="validation-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Validation
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  A target RIFTLESS validation stage executes configured checks inside a bounded execution environment and records a Validation Bundle containing executable evidence, outcomes, and limitations within a documented test scope.
                </p>
              </div>

              {/* TARGET Callout */}
              <Callout type="target">
                This section describes the target validation contract. Validator commands, result schemas, execution environments, resource limits, and runtime orchestration remain illustrative until repository-backed validation workers are implemented and verified.
              </Callout>

              <hr className="border-stone-200/50" />

              {/* TARGET VALIDATION FLOW */}
              <section className="space-y-4" aria-labelledby="validation-flow-heading">
                <h3 id="validation-flow-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Validation Flow
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation flow processes an authorized candidate through configured validators and records the resulting evidence, limitations, or failure outcomes.
                </p>

                {/* Desktop horizontal flow */}
                <div className="hidden md:flex flex-wrap items-center justify-between gap-1 border border-stone-200 rounded p-4 bg-stone-50/50 font-mono text-[9px] font-bold text-stone-700 max-w-4xl">
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">AUTHORIZED VALIDATION INPUT</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">VALIDATION PLAN</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-stone-800 text-stone-100 text-center shadow-sm uppercase tracking-tight">ISOLATED EXECUTION</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight">VALIDATOR RESULTS</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-[#A8CD16] rounded p-2 bg-[#A8CD16]/10 text-[#556b03] text-center shadow-sm uppercase tracking-tight">VALIDATION BUNDLE</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-900 rounded p-2 bg-stone-900 text-white text-center shadow-sm uppercase tracking-tight">CONTROL-PLANE REVIEW</div>
                </div>

                {/* Mobile Flow Sequence */}
                <div className="md:hidden space-y-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px]">
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">AUTHORIZED VALIDATION INPUT</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">VALIDATION PLAN</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-stone-800 text-stone-100 font-bold shadow-sm text-center uppercase">ISOLATED EXECUTION</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-600 font-bold shadow-sm text-center uppercase">VALIDATOR RESULTS</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-[#A8CD16]/10 border border-[#A8CD16] text-[#556b03] font-bold shadow-sm text-center uppercase">VALIDATION BUNDLE</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-stone-900 text-white font-bold shadow-sm text-center uppercase">CONTROL-PLANE REVIEW</div>
                </div>

                {/* Supporting Inputs */}
                <div className="border border-stone-200 rounded p-4 bg-white max-w-xl space-y-2 text-xs">
                  <div className="font-mono text-[10px] font-bold text-stone-500 uppercase tracking-wider">
                    Target Flow Supporting Inputs:
                  </div>
                  <ul className="list-disc pl-4 space-y-1 text-stone-600 font-mono">
                    <li>PROPOSED CHANGE OR REMEDIATION REFERENCE</li>
                    <li>RISK DECISION REFERENCE</li>
                    <li>EFFECTIVE CONFIGURATION REFERENCE</li>
                  </ul>
                </div>

                {/* Blocked Path Callout / Box */}
                <div className="border border-red-200 bg-red-50/50 rounded p-4 max-w-xl space-y-3">
                  <div className="font-mono text-[10px] font-bold text-red-700 tracking-wider uppercase flex items-center gap-1.5">
                    <span>Blocked Paths:</span>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="text-xs text-red-800 leading-relaxed font-mono">
                      MODEL PROPOSAL <span className="text-stone-500 font-sans mx-1">&times;</span> VERIFIED EVIDENCE <span className="mx-1">&rarr;</span> <span className="bg-red-200 text-red-900 font-bold px-1.5 py-0.5 rounded text-[10px]">BLOCKED</span>
                    </div>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      A model proposal cannot construct or substitute for verified execution evidence.
                    </p>
                  </div>

                  <hr className="border-red-100" />

                  <div className="space-y-2">
                    <div className="text-xs text-red-800 leading-relaxed font-mono">
                      FAILED REQUIRED VALIDATOR <span className="text-stone-500 font-sans mx-1">&times;</span> VALIDATED STATUS <span className="mx-1">&rarr;</span> <span className="bg-red-200 text-red-900 font-bold px-1.5 py-0.5 rounded text-[10px]">BLOCKED</span>
                    </div>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      If any required validator fails, overall validation status must remain blocked from successful completion.
                    </p>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* AUTHORITY MODEL */}
              <section className="space-y-4" aria-labelledby="validation-authority-heading">
                <h3 id="validation-authority-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Authority Model
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation contract separates coordination, execution, evidence production, and later-stage authorization responsibilities.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  {/* CONTROL PLANE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      CONTROL PLANE
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>Verify that validation is permitted</li>
                        <li>Identify the proposed change or remediation to evaluate</li>
                        <li>Resolve required validation policy</li>
                        <li>Select configured validator categories</li>
                        <li>Record the validation-plan reference</li>
                        <li>Receive result references</li>
                        <li>Determine whether protected next stages may be considered</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed">
                        The control plane coordinates validation authorization. It must not reinterpret a failed required validator as successful evidence.
                      </p>
                    </div>
                  </div>

                  {/* ISOLATED VALIDATION WORKER */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      ISOLATED VALIDATION WORKER
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>Receive bounded validation inputs</li>
                        <li>Execute configured validation steps</li>
                        <li>Capture permitted outputs and failure reasons</li>
                        <li>Produce individual validator results</li>
                        <li>Assemble or contribute to the Validation Bundle</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed">
                        The worker produces evidence. It cannot authorize deployment, writeback, or its own result.
                      </p>
                    </div>
                  </div>

                  {/* VALIDATORS */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      VALIDATORS
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>Perform configured static analysis, bounded execution, compilation, tests, or deterministic contract checks</li>
                        <li>Return explicit outcomes and limitations</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed">
                        A validator reports its result. It does not determine overall run authorization independently.
                      </p>
                    </div>
                  </div>

                  {/* DEEPSEEK */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      DEEPSEEK
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>Suggest validation ideas</li>
                        <li>Explain failures</li>
                        <li>Propose revised remediation</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed font-bold">
                        DeepSeek cannot execute validators, create executable evidence, mark a run VALIDATED, or authorize the next state.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed">
                  <strong>Authority Rule:</strong> Executable validation results and advisory model output must remain separate artifacts.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* ENTRY REQUIREMENTS */}
              <section className="space-y-4" aria-labelledby="validation-entry-heading">
                <h3 id="validation-entry-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Entry Requirements
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A target validation stage may begin only when specific prerequisites are satisfied:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white text-xs max-w-2xl space-y-3">
                  <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                    Target Validation Stage Pre-conditions:
                  </span>
                  <ul className="list-disc pl-4 text-stone-600 space-y-1">
                    <li>Validation authorization has been recorded</li>
                    <li>Proposed change or remediation reference is available</li>
                    <li>Relevant Risk Decision reference is available</li>
                    <li>Effective configuration reference is available</li>
                    <li>Required validator categories are selected</li>
                    <li>Bounded validation inputs are available</li>
                    <li>Prohibited secret values are excluded</li>
                    <li>Required execution environment is available when implementation exists</li>
                  </ul>

                  <hr className="border-stone-200" />

                  <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                    Entry Clarifications:
                  </span>
                  <ul className="list-disc pl-4 text-stone-600 space-y-1">
                    <li>The presence of a remediation proposal does not authorize validation</li>
                    <li>An ALLOW risk status does not remove required validation</li>
                    <li>A WARN status may require a recorded acknowledgment before validation begins when configured</li>
                    <li>A BLOCK status must not advance to protected validation</li>
                    <li>Validator availability does not mean execution is authorized</li>
                  </ul>
                </div>

                <div className="border border-red-200 bg-red-50/50 rounded p-5 max-w-xl space-y-3">
                  <span className="text-[10px] font-mono tracking-wider text-red-700 font-bold block uppercase">
                    Validation State Non-Equivalence Contract
                  </span>
                  <div className="text-xs text-red-800 leading-relaxed font-mono">
                    AVAILABLE VALIDATOR &ne; AUTHORIZED VALIDATION &ne; EXECUTED VALIDATION &ne; PASSED VALIDATION
                  </div>
                  <p className="text-xs text-stone-600 leading-relaxed">
                    This logical contract dictates that:
                  </p>
                  <ul className="list-disc pl-4 text-xs text-stone-600 space-y-1">
                    <li>The mere availability of a validator does not equal authorized validation.</li>
                    <li>An authorized plan does not constitute executed validation evidence.</li>
                    <li>Executing a validator does not automatically imply the checks passed successfully.</li>
                  </ul>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* VALIDATION INPUTS */}
              <section className="space-y-4" aria-labelledby="validation-inputs-heading">
                <h3 id="validation-inputs-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validation Inputs
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation stage uses configured bounded properties grouped into logical categories to establish explicit test boundaries.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PROPOSED CHANGE OR REMEDIATION REFERENCE</span>
                    <p className="text-stone-500 italic">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Normalized SQL or schema change</li>
                      <li>Revised compatibility proposal</li>
                      <li>Relevant changed-file references</li>
                      <li>Evaluated revision boundary</li>
                      <li>Source references</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RISK DECISION REFERENCE</span>
                    <p className="text-stone-500 italic">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Current deterministic status</li>
                      <li>Evaluated scope</li>
                      <li>Required validation gates</li>
                      <li>Prohibited stages</li>
                      <li>Acknowledgment requirements</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION PLAN</span>
                    <p className="text-stone-500 italic">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Selected validators</li>
                      <li>Required and optional checks</li>
                      <li>Bounded test scope</li>
                      <li>Expected result conditions</li>
                      <li>Fixtures or test-input references</li>
                      <li>Environment requirements</li>
                      <li>Skipped checks and reasons when permitted</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">EFFECTIVE CONFIGURATION REFERENCE</span>
                    <p className="text-stone-500 italic">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Enabled validator categories</li>
                      <li>Validation-policy reference</li>
                      <li>Validator requirement references</li>
                      <li>Artifact destination reference</li>
                      <li>Redaction-policy reference</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">BOUNDED TEST INPUTS</span>
                    <p className="text-stone-500 italic">May include:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>SQL statements, schema fixtures, and bounded table fixtures</li>
                      <li>dbt project references when configured</li>
                      <li>Expected output references and contract assertions</li>
                    </ul>
                    <p className="text-red-700 italic font-semibold mt-2">Must not include:</p>
                    <ul className="list-disc pl-4 text-red-800 space-y-1">
                      <li>Unrestricted production exports</li>
                      <li>Unrestricted production-write credentials</li>
                      <li>Unrelated repository content</li>
                      <li>Prohibited secrets</li>
                    </ul>
                  </div>
                </div>

                <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="validation-inputs-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target inputs used to plan and execute a RIFTLESS validation stage.
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
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PROPOSED CHANGE OR REMEDIATION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify the exact candidate being tested.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Candidate content does not prove correctness.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK DECISION REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify current policy status and required validation gates.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Validation does not replace deterministic policy.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION PLAN</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Define selected validators, scope, expected conditions, and execution requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">A plan is not executable evidence.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">EFFECTIVE CONFIGURATION REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify configured validators and validation requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configuration does not indicate that execution succeeded.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">BOUNDED TEST INPUTS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide fixtures, project references, or assertions needed by configured validators.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional by validator.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Fixtures do not represent universal production behavior.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PREVIOUS VALIDATION OUTCOME</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Support explicit revalidation after revision or failure.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">An older result must not automatically apply to changed input.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* VALIDATION PLAN */}
              <section className="space-y-4" aria-labelledby="validation-plan-heading">
                <h3 id="validation-plan-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validation Plan
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A target Validation Plan records the selection and intent of configured validators for a specific proposal.
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-5 max-w-2xl text-xs space-y-3">
                  <div className="space-y-1">
                    <span className="font-semibold text-stone-900 font-mono block text-[10px]">TARGET CONTENT:</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>candidate artifact reference</li>
                      <li>Risk Decision reference</li>
                      <li>effective configuration reference</li>
                      <li>selected validator categories</li>
                      <li>required validator indicators</li>
                      <li>optional validator indicators</li>
                      <li>bounded test scope</li>
                      <li>fixture or project references</li>
                      <li>expected result conditions</li>
                      <li>environment requirements</li>
                      <li>permitted artifact destinations</li>
                      <li>redaction requirements</li>
                      <li>skipped validator reasons</li>
                      <li>known limitations</li>
                    </ul>
                  </div>

                  <hr className="border-stone-200" />

                  <div className="space-y-1">
                    <span className="font-semibold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                    <p className="text-stone-600 leading-relaxed">
                      A Validation Plan authorizes nothing by itself. The required control-plane validation authorization must remain separately recorded.
                    </p>
                  </div>
                </div>

                <div className="border-l-4 border-[#F2A93B] bg-amber-50/20 p-4 rounded-r text-xs text-amber-900 max-w-2xl leading-relaxed font-mono">
                  <strong>WARNING:</strong> A model-generated list of suggested tests is not a Validation Plan until the control plane applies configured policy and validator requirements.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* VALIDATOR CATEGORIES */}
              <section className="space-y-4" aria-labelledby="validator-categories-heading">
                <h3 id="validator-categories-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validator Categories
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation contract describes four conceptual validator categories.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  {/* SQLGLOT ANALYSIS */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">SQLGLOT ANALYSIS</span>
                    <p className="text-stone-600 leading-relaxed">
                      Parse supported SQL when configured, identify referenced tables or columns, inspect syntax structure, and detect configured structural patterns.
                    </p>
                    <p className="text-stone-500 italic">Produces:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Static-analysis result</li>
                      <li>Parsed-reference information when available</li>
                      <li>Warning, failure, or limitation reason</li>
                    </ul>
                    <p className="text-stone-500 font-bold">Limitation:</p>
                    <p className="text-stone-600 leading-relaxed">
                      SQLGlot analysis is static analysis. Successful parsing does not prove that SQL executes correctly against the target environment.
                    </p>
                  </div>

                  {/* DUCKDB FIXTURE EXECUTION */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DUCKDB FIXTURE EXECUTION</span>
                    <p className="text-stone-600 leading-relaxed">
                      Execute bounded SQL against configured local fixtures, evaluate schema compatibility inside the fixture scope, observe query outcomes, and compare permitted expected results.
                    </p>
                    <p className="text-stone-500 italic">Produces:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Execution outcome</li>
                      <li>Query-result reference</li>
                      <li>Fixture reference</li>
                      <li>Failure reason</li>
                      <li>Tested-scope statement</li>
                    </ul>
                    <p className="text-stone-500 font-bold">Limitation:</p>
                    <p className="text-stone-600 leading-relaxed">
                      DuckDB fixture execution does not reproduce every production engine, dataset, workload, permission, or operational condition.
                    </p>
                  </div>

                  {/* DBT COMPILATION OR TESTS */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DBT COMPILATION OR TESTS</span>
                    <p className="text-stone-600 leading-relaxed">
                      Compile configured dbt project references, execute configured dbt tests when the required project context is available, and identify compilation or test failures.
                    </p>
                    <p className="text-stone-500 italic">Produces:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Compilation result</li>
                      <li>Test result</li>
                      <li>Selected-node references when available</li>
                      <li>Failure reason</li>
                      <li>Tested-scope statement</li>
                    </ul>
                    <p className="text-stone-500 font-bold">Limitation:</p>
                    <p className="text-stone-600 leading-relaxed">
                      dbt compilation or tests do not authorize deployment and must not be described as production execution.
                    </p>
                  </div>

                  {/* DETERMINISTIC CONTRACT CHECKS */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DETERMINISTIC CONTRACT CHECKS</span>
                    <p className="text-stone-600 leading-relaxed">
                      Evaluate configured structural expectations, verify required references or fields, compare expected compatibility requirements, and confirm required gates were represented.
                    </p>
                    <p className="text-stone-500 italic">Produces:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Matched, not-matched, indeterminate, or error results</li>
                      <li>Decision-relevant validation references</li>
                    </ul>
                    <p className="text-stone-500 font-bold">Limitation:</p>
                    <p className="text-stone-600 leading-relaxed">
                      Validation contract checks do not replace the original Risk Decision.
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="validator-responsibility-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Conceptual validator categories, evidence roles, and recorded limitations.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Validator Category</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Target Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Produces</th>
                        <th scope="col" className="px-4 py-3 w-1/4">Scope Limitation</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">SQLGLOT ANALYSIS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Static SQL parsing and structural inspection.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Parse outcome, references, and limitations.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Does not prove runtime execution.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DUCKDB FIXTURE EXECUTION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Execute bounded SQL against configured fixtures.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Execution result and tested-scope references.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Does not reproduce universal production behavior.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DBT COMPILATION OR TESTS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Compile or test configured dbt project scope.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Compilation or test outcomes.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Does not authorize deployment.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DETERMINISTIC CONTRACT CHECKS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Evaluate configured validation expectations.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Contract-check results and reasons.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Does not replace the Risk Decision.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* VALIDATOR RESULT STATES */}
              <section className="space-y-4" aria-labelledby="validator-results-heading">
                <h3 id="validator-results-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validator Result States
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation contract defines six conceptual result states. These are not yet repository-backed enums.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PASSED</span>
                    <p className="text-stone-600 leading-relaxed">
                      The validator completed and the configured expected condition was satisfied within the recorded scope.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">FAILED</span>
                    <p className="text-stone-600 leading-relaxed">
                      The validator completed but one or more required expected conditions were not satisfied.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ERROR</span>
                    <p className="text-stone-600 leading-relaxed">
                      The validator could not complete because of configuration, parsing, environment, or runtime failure.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">SKIPPED</span>
                    <p className="text-stone-600 leading-relaxed">
                      The validator was intentionally not executed under a permitted configuration or plan condition.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">NOT AVAILABLE</span>
                    <p className="text-stone-600 leading-relaxed">
                      The configured validator or required execution input was unavailable.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">INDETERMINATE</span>
                    <p className="text-stone-600 leading-relaxed">
                      The available result was insufficient to determine whether the expected condition was satisfied.
                    </p>
                  </div>
                </div>

                <div className="border border-stone-200 rounded p-4 bg-stone-50/50 max-w-3xl space-y-1.5 text-xs font-mono text-stone-700">
                  <div className="font-bold text-stone-900 mb-1 uppercase tracking-wider text-[10px]">Result Logic Clarifications:</div>
                  <ul className="list-disc pl-5 space-y-1 font-sans">
                    <li>SKIPPED is not PASSED.</li>
                    <li>NOT AVAILABLE is not PASSED.</li>
                    <li>ERROR is not FAILED execution evidence.</li>
                    <li>INDETERMINATE must remain visible.</li>
                    <li>A required validator in FAILED, ERROR, NOT AVAILABLE, or INDETERMINATE state must not silently contribute to a successful overall outcome.</li>
                    <li>Configured policy determines whether optional non-success results permit further review.</li>
                  </ul>
                </div>

                <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="validator-result-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Conceptual validator result states and their effect on overall validation.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Result</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Meaning</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Overall Validation Effect</th>
                        <th scope="col" className="px-4 py-3 w-1/4">Required Record</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-emerald-700 bg-emerald-50/10 text-left align-top">PASSED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured condition satisfied within tested scope.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">May contribute to a successful overall outcome.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Validator reference, tested scope, and permitted result references.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-red-700 bg-red-50/10 text-left align-top">FAILED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Execution completed but expected condition failed.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A required failed validator prevents successful validation.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Failure reason and permitted evidence references.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-red-700 bg-red-50/10 text-left align-top">ERROR</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Execution could not complete.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Must not silently become PASSED.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Failure category and permitted diagnostic reference.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-700 bg-stone-50/10 text-left align-top">SKIPPED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Validator intentionally not run.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Configured policy determines whether overall validation may continue.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Skip reason and policy reference when applicable.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-700 bg-stone-50/10 text-left align-top">NOT AVAILABLE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Validator or required input unavailable.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required validation must not infer success.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Unavailable capability or input reason.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-amber-700 bg-amber-50/10 text-left align-top">INDETERMINATE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Result insufficient to determine success.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Must remain visible and must not silently contribute to PASSED.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Unresolved condition or missing evidence reason.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* OVERALL VALIDATION OUTCOME */}
              <section className="space-y-4" aria-labelledby="overall-outcome-heading">
                <h3 id="overall-outcome-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Overall Validation Outcome
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation contract defines the following overall-outcome requirements based on configured validator requirements and recorded results.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl text-xs">
                  {/* SUCCESSFUL WITHIN RECORDED SCOPE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">SUCCESSFUL WITHIN RECORDED SCOPE</span>
                    <p className="text-stone-500 italic">May be recorded only when:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>All required configured validators completed successfully</li>
                      <li>No required validator remains failed, errored, unavailable, or indeterminate</li>
                      <li>Skipped required validation is not silently accepted</li>
                      <li>Tested scope is recorded</li>
                      <li>Limitations are recorded</li>
                      <li>Result references are available</li>
                    </ul>
                  </div>

                  {/* NON-SUCCESSFUL */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">NON-SUCCESSFUL</span>
                    <p className="text-stone-500 italic">Must be recorded when:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>A required validator fails</li>
                      <li>A required validator cannot execute</li>
                      <li>Required test input is unavailable</li>
                      <li>Result consistency cannot be established</li>
                      <li>The Validation Bundle is malformed</li>
                      <li>Required evidence references are unavailable</li>
                    </ul>
                  </div>

                  {/* PARTIAL RESULT */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PARTIAL RESULT</span>
                    <p className="text-stone-500 italic">May be recorded when:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Some optional validators completed</li>
                      <li>One or more optional validators were skipped or unavailable</li>
                      <li>Configured policy permits a partial evidence record</li>
                    </ul>
                  </div>
                </div>

                <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed">
                  <strong>Clarification:</strong> A partial result must not be presented as a successful complete validation.
                </div>

                <div className="border-l-4 border-[#F2A93B] bg-amber-50/20 p-4 rounded-r text-xs text-amber-900 max-w-2xl leading-relaxed font-mono">
                  <strong>WARNING:</strong> A successful validation outcome means configured validators passed within the recorded scope. It does not guarantee universal compatibility, production safety, or absence of downstream failure.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* VALIDATION BUNDLE CONTRACT */}
              <section className="space-y-4" aria-labelledby="validation-bundle-heading">
                <h3 id="validation-bundle-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validation Bundle
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A target Validation Bundle records permitted validator outcomes, tested scope, limitations, and relevant evidence references for the evaluated candidate.
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-5 max-w-2xl text-xs space-y-3">
                  <div className="space-y-1">
                    <span className="font-semibold text-stone-900 font-mono block text-[10px]">TARGET CONTENT:</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>candidate artifact reference</li>
                      <li>Risk Decision reference</li>
                      <li>Validation Plan reference</li>
                      <li>effective configuration reference</li>
                      <li>selected validators</li>
                      <li>individual validator results</li>
                      <li>overall validation outcome</li>
                      <li>executed-command references</li>
                      <li>fixture or project references</li>
                      <li>execution-environment details</li>
                      <li>tested-scope statement</li>
                      <li>skipped-validator list and reasons</li>
                      <li>logs or permitted log references</li>
                      <li>failure reasons</li>
                      <li>limitations</li>
                      <li>produced artifact references</li>
                      <li>evaluated revision reference when applicable</li>
                    </ul>
                  </div>

                  <hr className="border-stone-200" />

                  <div className="space-y-1">
                    <span className="font-semibold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                    <p className="text-stone-600 leading-relaxed">
                      A Validation Bundle provides scope-bound evidence. It does not independently authorize deployment, GitHub reporting, or DataHub writeback.
                    </p>
                  </div>

                  <hr className="border-stone-200" />

                  <div className="space-y-1 text-red-900">
                    <span className="font-bold font-mono block text-[10px] text-red-800">MUST NOT CONTAIN:</span>
                    <ul className="list-disc pl-4 space-y-1 text-red-800">
                      <li>API credentials</li>
                      <li>access tokens</li>
                      <li>unrestricted raw logs</li>
                      <li>secret environment values</li>
                      <li>unrestricted production data</li>
                      <li>private keys</li>
                      <li>raw authorization headers</li>
                      <li>model output presented as executed evidence</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* ISOLATED EXECUTION BOUNDARY */}
              <section className="space-y-4" aria-labelledby="isolated-execution-heading">
                <h3 id="isolated-execution-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Isolated Execution Boundary
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target execution boundary must restrict validation inputs, credentials, and permitted operations so validators cannot directly mutate production systems.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">MAY RECEIVE WHEN PERMITTED:</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>candidate change or remediation reference</li>
                      <li>selected validator configuration</li>
                      <li>bounded SQL or schema fixtures</li>
                      <li>required dbt project references</li>
                      <li>expected-result references</li>
                      <li>artifact-destination references</li>
                      <li>redaction-policy reference</li>
                      <li>execution-scope requirements</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-red-700 block uppercase">MUST NOT RECEIVE OR PERFORM:</span>
                    <ul className="list-disc pl-4 text-red-800 space-y-1">
                      <li>unrestricted production-write credentials</li>
                      <li>direct production mutation</li>
                      <li>browser session credentials</li>
                      <li>model-provider credentials unless explicitly required by a separate permitted operation</li>
                      <li>unrelated repository content</li>
                      <li>unrestricted metadata exports</li>
                      <li>self-authorization</li>
                      <li>deployment approval</li>
                      <li>writeback authorization</li>
                    </ul>
                  </div>
                </div>

                <div className="border-l-4 border-[#F2A93B] bg-amber-50/20 p-4 rounded-r text-xs text-amber-900 max-w-2xl leading-relaxed font-mono">
                  <strong>WARNING:</strong> The validation worker must not receive unrestricted production-write credentials merely because a validator needs database-compatible input.
                </div>

                <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed">
                  <strong>NOTE:</strong> The final isolation mechanism remains undefined until the validation worker is implemented.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* LOG AND SECRET BOUNDARY */}
              <section className="space-y-4" aria-labelledby="validation-log-heading">
                <h3 id="validation-log-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validation Log Boundary
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation-log contract separates permitted diagnostic content from values that must be removed, rejected, or kept server-side.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">MAY BE PRESERVED WHEN PERMITTED:</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>validator name or category reference</li>
                      <li>execution status</li>
                      <li>bounded command reference</li>
                      <li>sanitized output</li>
                      <li>failure category</li>
                      <li>tested-scope information</li>
                      <li>fixture references</li>
                      <li>permitted diagnostic references</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-red-700 block uppercase">MUST BE REMOVED, REJECTED, OR KEPT SERVER-SIDE:</span>
                    <ul className="list-disc pl-4 text-red-800 space-y-1">
                      <li>credentials</li>
                      <li>access tokens</li>
                      <li>connection strings containing secrets</li>
                      <li>private keys</li>
                      <li>raw authorization headers</li>
                      <li>secret environment values</li>
                      <li>unrestricted row-level production data</li>
                      <li>unrelated sensitive values</li>
                    </ul>
                  </div>
                </div>

                <div className="border-l-4 border-[#F2A93B] bg-amber-50/20 p-4 rounded-r text-xs text-amber-900 max-w-2xl leading-relaxed font-mono">
                  <strong>WARNING:</strong> A value is not safe for artifact storage or model context merely because it was emitted by a validator.
                </div>

                <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed">
                  <strong>NOTE:</strong> Runtime tests should verify that prohibited values are removed or rejected before logs are persisted, exposed, or supplied to a model.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET OPERATION SHAPES */}
              <section className="space-y-4" aria-labelledby="target-operation-shapes-heading">
                <h3 id="target-operation-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Operation Shapes
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  These conceptual interfaces describe the target operations for planning and executing validation stages:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  {/* Planning Shape */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL VALIDATION PLANNING <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive candidate artifact reference
receive current Risk Decision
receive effective validation requirements
select configured validator categories
define bounded test scope
identify required fixtures or project references
record limitations
return target Validation Plan`}
                    </pre>
                  </div>

                  {/* Execution Shape */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL VALIDATION EXECUTION <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive recorded validation authorization
receive target Validation Plan
resolve permitted bounded inputs
execute configured validators
record individual results
assemble tested-scope statement
record overall outcome and limitations
return target Validation Bundle`}
                    </pre>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
                  Exact commands, worker APIs, validator options, environment setup, result payloads, and execution limits will be documented after repository-backed validation workers are implemented and versioned.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* REVALIDATION */}
              <section className="space-y-4" aria-labelledby="revalidation-heading">
                <h3 id="revalidation-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Revalidation
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A new validation should be required when the evaluated candidate, relevant validation inputs, required policy, validator selection, or tested scope changes materially.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                      Revalidation Required When:
                    </span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>proposed change content changes</li>
                      <li>remediation proposal changes</li>
                      <li>evaluated repository revision changes</li>
                      <li>relevant fixture or project input changes</li>
                      <li>selected validator configuration changes</li>
                      <li>required validation policy changes</li>
                      <li>previous result becomes stale</li>
                      <li>failed validation leads to a revised candidate</li>
                      <li>tested scope materially changes</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">
                      Target Revalidation Rules:
                    </span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>previous Validation Bundle remains referenced</li>
                      <li>successor result identifies the newly evaluated candidate</li>
                      <li>old successful validation does not automatically apply to changed input</li>
                      <li>changed validation scope must remain visible</li>
                      <li>skipped validators from the previous run must not be silently treated as executed</li>
                      <li>model explanation alone does not constitute revalidation</li>
                    </ul>
                  </div>
                </div>

                <Callout type="target">
                  The final result identifier, supersession, and validation-history model must be derived from the implemented artifact contracts. This section does not define executable versioning behavior.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET VALIDATION CONSISTENCY */}
              <section className="space-y-4" aria-labelledby="validation-consistency-heading">
                <h3 id="validation-consistency-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Validation Consistency
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation contract defines conceptual consistency requirements for validation inputs, plans, results, authority, and references.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  {/* INPUT CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">INPUT CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>candidate reference exists</li>
                      <li>current Risk Decision reference exists</li>
                      <li>Validation Plan reference exists</li>
                      <li>effective configuration reference exists</li>
                      <li>evaluated revision remains identifiable when applicable</li>
                    </ul>
                  </div>

                  {/* PLAN CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PLAN CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>required validators are represented</li>
                      <li>selected scope is explicit</li>
                      <li>skipped checks include reasons</li>
                      <li>prohibited validators or commands are absent</li>
                    </ul>
                  </div>

                  {/* RESULT CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RESULT CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>individual results correspond to selected validators</li>
                      <li>required FAILED result prevents successful outcome</li>
                      <li>ERROR does not appear as PASSED</li>
                      <li>SKIPPED does not appear as executed</li>
                      <li>tested scope and limitations are available</li>
                    </ul>
                  </div>

                  {/* AUTHORITY CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHORITY CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>model proposal is not executable evidence</li>
                      <li>Validation Bundle does not authorize deployment</li>
                      <li>worker does not authorize its own outcome</li>
                      <li>writeback remains separately authorized</li>
                    </ul>
                  </div>

                  {/* REFERENCE CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REFERENCE CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>predecessor references remain associated</li>
                      <li>superseded results remain distinguishable</li>
                      <li>artifact references do not embed secrets</li>
                    </ul>
                  </div>
                </div>

                <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed">
                  <strong>Clarification:</strong> These are target validation requirements. Do not claim a Validation Bundle schema validator already exists.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* FAILURE BEHAVIOR */}
              <section className="space-y-4" aria-labelledby="validation-failure-heading">
                <h3 id="validation-failure-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validation Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation contract defines non-success behavior when planning, execution, result assembly, redaction, or artifact storage cannot complete.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl text-xs">
                  {/* VALIDATION PLAN INVALID */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION PLAN INVALID</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>execution must not begin</li>
                      <li>missing or conflicting requirements should remain visible</li>
                    </ul>
                  </div>

                  {/* REQUIRED VALIDATOR UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REQUIRED VALIDATOR UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>successful overall validation must not be inferred</li>
                      <li>unavailable capability should be recorded</li>
                    </ul>
                  </div>

                  {/* BOUNDED INPUT UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">BOUNDED INPUT UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>affected validator cannot complete</li>
                      <li>missing input should remain explicit</li>
                    </ul>
                  </div>

                  {/* VALIDATOR FAILED */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATOR FAILED</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>required failure prevents successful validation</li>
                      <li>failure reason and permitted evidence references should be recorded</li>
                    </ul>
                  </div>

                  {/* VALIDATOR ERROR */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATOR ERROR</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>result must not silently become PASSED</li>
                      <li>configured policy determines whether other optional checks may continue</li>
                    </ul>
                  </div>

                  {/* EXECUTION ENVIRONMENT UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">EXECUTION ENVIRONMENT UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>validation must not be reported as completed</li>
                      <li>available pre-execution references may remain recorded</li>
                    </ul>
                  </div>

                  {/* LOG REDACTION FAILURE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">LOG REDACTION FAILURE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>prohibited log content must not be persisted or exposed</li>
                      <li>failure reason should be recorded without reproducing the secret</li>
                    </ul>
                  </div>

                  {/* VALIDATION BUNDLE INVALID */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION BUNDLE INVALID</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>protected next stage must not infer successful validation</li>
                      <li>UI must not infer state from styling</li>
                    </ul>
                  </div>

                  {/* ARTIFACT STORAGE UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ARTIFACT STORAGE UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Validation Bundle must not be reported as successfully preserved</li>
                      <li>execution result and storage success remain distinct</li>
                      <li>retry handling remains undefined</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* INVARIANTS */}
              <section className="space-y-4" aria-labelledby="validation-invariants-heading">
                <h3 id="validation-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Validation Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target validation contract defines the following validation invariants:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION INPUT REMAINS IDENTIFIABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION AUTHORIZATION REMAINS RECORDED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS NON-EVIDENCE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">EXECUTION REMAINS BOUNDED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">REQUIRED VALIDATORS REMAIN VISIBLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">SKIPPED WORK REMAINS EXPLICIT.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">RESULTS REMAIN SCOPE-BOUND.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">FAILURE DOES NOT BECOME SUCCESS.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WORKER AUTHORITY REMAINS LIMITED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK REMAINS SEPARATELY AUTHORIZED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION STORAGE SUCCESS REMAINS EXPLICIT.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe target validation requirements, not proof that isolated workers, validator adapters, schema validation, artifact storage, or execution orchestration have already been implemented.
                </p>
              </section>
            </section>
          ) : activeSection === 'Writeback' ? (
            <section id="writeback" aria-labelledby="writeback-heading" className="space-y-8 animate-none scroll-mt-24">
              {/* Title & Lead */}
              <div className="space-y-4">
                <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
                  REFERENCE
                </span>
                <h2 id="writeback-heading" className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  Writeback
                </h2>
                <p className="text-lg text-[var(--color-riftless-ink)] leading-relaxed font-semibold">
                  RIFTLESS writeback records permitted review outcomes in configured organizational metadata destinations only after the required decision, evidence, and authorization conditions are recorded.
                </p>

                <div className="border border-stone-200 rounded p-4 bg-stone-50/50 space-y-4 text-xs max-w-4xl">
                  <div className="font-mono text-[10px] font-bold text-stone-900 uppercase tracking-wider">
                    Core Writeback Principles
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <span className="font-bold text-stone-900 block font-mono text-[10px] uppercase">1. Writeback of Review Memory (May Preserve)</span>
                      <p className="text-stone-500 leading-relaxed">
                        May preserve an authorized record of:
                      </p>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1 font-mono">
                        <li>ALLOW, WARN, or BLOCK Risk Decision</li>
                        <li>decision reasons</li>
                        <li>affected assets</li>
                        <li>acknowledgment requirements</li>
                        <li>validation success or failure</li>
                        <li>incident or blocked status</li>
                        <li>owner actions</li>
                        <li>permitted artifact references</li>
                      </ul>
                    </div>
                    <div className="space-y-2">
                      <span className="font-bold text-red-700 block font-mono text-[10px] uppercase">2. Writeback as Approval or Verified Success (Must Not)</span>
                      <p className="text-stone-500 leading-relaxed">
                        Must not:
                      </p>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1 font-mono">
                        <li>present BLOCK as approved</li>
                        <li>present WARN as ALLOW</li>
                        <li>present failed validation as successful</li>
                        <li>present partial validation as complete</li>
                        <li>imply deployment authorization</li>
                        <li>imply remediation was deployed</li>
                        <li>imply universal safety</li>
                      </ul>
                    </div>
                  </div>
                  <div className="border-t border-stone-200 pt-3 text-stone-700 leading-relaxed font-mono font-semibold">
                    “An authorized writeback may preserve a BLOCK, WARN, validation failure, or other non-success outcome as organizational memory. Recording the outcome does not permit deployment or convert it into approval.”
                  </div>
                </div>
              </div>

              {/* TARGET Callout */}
              <Callout type="target">
                This section describes the target writeback contract. Destination mappings, operation formats, record schemas, retry behavior, and runtime persistence remain illustrative until repository-backed writeback adapters are implemented and verified.
              </Callout>

              <hr className="border-stone-200/50" />

              {/* TARGET WRITEBACK FLOW */}
              <section className="space-y-4" aria-labelledby="writeback-flow-heading">
                <h3 id="writeback-flow-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Writeback Flow
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback flow prepares and submits permitted organizational metadata records after the required source references and authorization state are available.
                </p>

                {/* Desktop horizontal flow */}
                <div className="hidden md:flex flex-wrap items-center justify-between gap-1 border border-stone-200 rounded p-4 bg-stone-50/50 font-mono text-[9px] font-bold text-stone-700 max-w-4xl">
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight text-stone-500">Writeback Prep</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight text-stone-500">Destination Check</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-200 rounded p-2 bg-white text-center shadow-sm uppercase tracking-tight text-stone-500">Metadata Op</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-[#A8CD16] rounded p-2 bg-[#A8CD16]/10 text-[#556b03] text-center shadow-sm uppercase tracking-tight">Writeback Outcome</div>
                  <div className="text-stone-400 text-xs px-0.5" aria-hidden="true">&rarr;</div>
                  <div className="flex-1 min-w-[100px] border border-stone-900 rounded p-2 bg-stone-900 text-white text-center shadow-sm uppercase tracking-tight">Writeback Record</div>
                </div>

                {/* Mobile Flow Sequence */}
                <div className="md:hidden space-y-2 bg-stone-100/60 border border-stone-200 p-4 rounded font-mono text-[9px]">
                  <div className="p-2 bg-white border border-stone-200 text-stone-500 font-bold shadow-sm text-center uppercase">Writeback Prep</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-500 font-bold shadow-sm text-center uppercase">Destination Check</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-white border border-stone-200 text-stone-500 font-bold shadow-sm text-center uppercase">Metadata Op</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-[#A8CD16]/10 border border-[#A8CD16] text-[#556b03] font-bold shadow-sm text-center uppercase">Writeback Outcome</div>
                  <div className="text-center text-stone-400 font-bold" aria-hidden="true">&darr;</div>
                  <div className="p-2 bg-stone-900 text-white font-bold shadow-sm text-center uppercase">Writeback Record</div>
                </div>

                {/* Supporting references */}
                <div className="border border-stone-200 rounded p-4 bg-white max-w-xl space-y-2 text-xs">
                  <div className="font-mono text-[10px] font-bold text-stone-500 uppercase tracking-wider">
                    Required Inputs to Prepare &amp; Authorize:
                  </div>
                  <ul className="list-disc pl-4 space-y-1 text-stone-600 font-mono">
                    <li>RISK DECISION</li>
                    <li>VALIDATION OUTCOME WHEN REQUIRED</li>
                    <li>AUTHORIZATION RECORD</li>
                    <li>CONFIGURED DESTINATION MAPPING</li>
                  </ul>
                  <div className="h-px bg-stone-100 my-1" />
                  <div className="font-mono text-[10px] font-bold text-stone-500 uppercase tracking-wider">
                    Supporting References:
                  </div>
                  <ul className="list-disc pl-4 space-y-1 text-stone-600 font-mono">
                    <li>TARGET ASSET REFERENCES</li>
                    <li>EFFECTIVE CONFIGURATION REFERENCE</li>
                    <li>PERMITTED ARTIFACT REFERENCES</li>
                  </ul>
                </div>

                {/* Blocked Path Callout / Box */}
                <div className="border border-red-200 bg-red-50/50 rounded p-4 max-w-xl space-y-3">
                  <div className="font-mono text-[10px] font-bold text-red-700 tracking-wider uppercase flex items-center gap-1.5">
                    <span>Blocked Paths:</span>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="text-xs text-red-800 leading-relaxed font-mono">
                      MODEL OUTPUT <span className="text-stone-500 font-sans mx-1">&times;</span> WRITEBACK AUTHORIZATION <span className="mx-1">&rarr;</span> <span className="bg-red-200 text-red-900 font-bold px-1.5 py-0.5 rounded text-[10px]">BLOCKED</span>
                    </div>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      A model proposal or output cannot authorize writeback.
                    </p>
                  </div>

                  <hr className="border-red-100" />

                  <div className="space-y-2">
                    <div className="text-xs text-red-800 leading-relaxed font-mono">
                      MISSING AUTHORIZATION <span className="text-stone-500 font-sans mx-1">&times;</span> WRITEBACK OPERATION <span className="mx-1">&rarr;</span> <span className="bg-red-200 text-red-900 font-bold px-1.5 py-0.5 rounded text-[10px]">BLOCKED</span>
                    </div>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      Writeback operations cannot execute without a recorded authorization.
                    </p>
                  </div>

                  <hr className="border-red-100" />

                  <div className="space-y-2">
                    <div className="text-xs text-red-800 leading-relaxed font-mono">
                      FAILED REQUIRED VALIDATION <span className="text-stone-500 font-sans mx-1">&times;</span> SUCCESSFUL VALIDATION STATUS <span className="mx-1">&rarr;</span> <span className="bg-red-200 text-red-900 font-bold px-1.5 py-0.5 rounded text-[10px]">BLOCKED</span>
                    </div>
                    <p className="text-xs text-stone-600 leading-relaxed font-mono">
                      A failed required validator must not be written or reported as successful validation evidence. The failure outcome itself may still be preserved through an authorized failure, incident, or decision record.
                    </p>
                  </div>

                  <hr className="border-red-100" />

                  <div className="space-y-2">
                    <div className="text-xs text-red-800 leading-relaxed font-mono">
                      STALE EVALUATED REVISION <span className="text-stone-500 font-sans mx-1">&times;</span> CURRENT WRITEBACK STATUS <span className="mx-1">&rarr;</span> <span className="bg-red-200 text-red-900 font-bold px-1.5 py-0.5 rounded text-[10px]">BLOCKED</span>
                    </div>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      A newer revision requires re-evaluation; an old writeback state does not carry forward.
                    </p>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* AUTHORITY MODEL */}
              <section className="space-y-4" aria-labelledby="writeback-authority-heading">
                <h3 id="writeback-authority-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Authority Model
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract separates coordination, execution, evidence production, and later-stage authorization responsibilities:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  {/* CONTROL PLANE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      CONTROL PLANE
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>verify required predecessor artifacts</li>
                        <li>verify recorded authorization state</li>
                        <li>resolve configured destination mappings</li>
                        <li>permit or reject the writeback operation</li>
                        <li>receive writeback outcome references</li>
                        <li>record whether the operation completed, failed, or was rejected</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed">
                        The control plane may authorize a configured writeback operation only after required policy and validation conditions are satisfied.
                      </p>
                    </div>
                  </div>

                  {/* WRITEBACK ADAPTER */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      WRITEBACK ADAPTER
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>receive a permitted writeback request</li>
                        <li>prepare configured destination operations</li>
                        <li>submit only permitted metadata fields</li>
                        <li>capture accepted, rejected, and unavailable results</li>
                        <li>return destination references when available</li>
                        <li>contribute to the Writeback Record</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed">
                        The adapter performs the permitted operation. It does not create authorization or reinterpret the Risk Decision.
                      </p>
                    </div>
                  </div>

                  {/* DETERMINISTIC RISK ENGINE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      DETERMINISTIC RISK ENGINE
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>produce the current Risk Decision</li>
                        <li>identify required validation or acknowledgment gates</li>
                        <li>identify conditions prohibiting writeback</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed">
                        The engine determines policy requirements but does not execute destination writes.
                      </p>
                    </div>
                  </div>

                  {/* ISOLATED VALIDATION WORKER */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      ISOLATED VALIDATION WORKER
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>provide the required Validation Bundle or non-success outcome</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed">
                        Validation evidence does not independently authorize writeback.
                      </p>
                    </div>
                  </div>

                  {/* DEEPSEEK */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-3 md:col-span-2">
                    <span className="font-mono text-[10px] font-bold text-stone-950 block uppercase tracking-wider">
                      DEEPSEEK
                    </span>
                    <hr className="border-stone-100" />
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">TARGET ROLE:</span>
                      <ul className="list-disc pl-4 text-stone-600 space-y-1">
                        <li>explain the intended writeback</li>
                        <li>propose record wording or owner actions when permitted</li>
                        <li>explain a rejected or failed operation</li>
                      </ul>
                    </div>
                    <div className="space-y-1">
                      <span className="font-bold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                      <p className="text-stone-600 leading-relaxed">
                        DeepSeek cannot authorize, execute, or report successful writeback.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border-l-4 border-stone-400 bg-stone-50 p-4 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed">
                  <strong>Authority Rule:</strong> Authorization success, destination execution, and writeback-record persistence are three distinct results.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* ENTRY REQUIREMENTS */}
              <section className="space-y-4" aria-labelledby="writeback-entry-heading">
                <h3 id="writeback-entry-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Entry Requirements
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A target writeback operation may begin only when specific prerequisites are satisfied:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white text-xs max-w-2xl space-y-3">
                  <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                    Target Writeback Entry Conditions:
                  </span>
                  <ul className="list-disc pl-4 text-stone-600 space-y-1">
                    <li>current Risk Decision reference is available</li>
                    <li>required authorization state is recorded</li>
                    <li>required validation outcome is available when the selected record category and configured policy require validation.</li>
                    <li>required acknowledgment or human-review result is available when configured</li>
                    <li>configured destination mapping is available</li>
                    <li>target asset references are available</li>
                    <li>permitted record categories are identified</li>
                    <li>prohibited values are excluded</li>
                    <li>writeback capability is enabled and available</li>
                    <li>evaluated revision or change scope remains current</li>
                  </ul>

                  <hr className="border-stone-200" />

                  <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                    Entry Clarifications:
                  </span>
                  <ul className="list-disc pl-4 text-stone-600 space-y-1 font-mono">
                    <li>writeback enabled does not mean writeback authorized</li>
                    <li>ALLOW does not automatically perform writeback</li>
                    <li>WARN acknowledgment does not rewrite the Risk Decision</li>
                    <li>BLOCK must not advance to deployment, successful-validation reporting, or any operation represented as approval. An authorized writeback may preserve the BLOCK decision and its required actions.</li>
                    <li>Decision-status, decision-document, owner-action, incident-status, or failure records may not require a successful Validation Bundle when configured policy permits preserving the non-success outcome.</li>
                    <li>a successful Validation Bundle does not authorize writeback independently</li>
                    <li>model output is not an authorization input</li>
                    <li>destination availability does not imply operation permission</li>
                  </ul>
                </div>

                <div className="border border-red-200 bg-red-50/50 rounded p-5 max-w-xl space-y-3">
                  <span className="text-[10px] font-mono tracking-wider text-red-700 font-bold block uppercase">
                    Writeback State Non-Equivalence Contract
                  </span>
                  <div className="text-xs text-red-800 leading-relaxed font-mono">
                    ENABLED &ne; AVAILABLE &ne; AUTHORIZED &ne; ATTEMPTED &ne; COMPLETED
                  </div>
                  <p className="text-xs text-stone-600 leading-relaxed">
                    This logical contract dictates that enabling writeback in configuration is not equal to its availability or authorization, nor does attempting an operation guarantee its completed status at the organizational destination.
                  </p>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* WRITEBACK INPUTS */}
              <section className="space-y-4" aria-labelledby="writeback-inputs-heading">
                <h3 id="writeback-inputs-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Writeback Inputs
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract uses configured inputs to prepare bounded and permitted metadata operations.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">RISK DECISION REFERENCE</span>
                    <p className="text-stone-500 italic text-[10px] font-bold">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>current ALLOW, WARN, or BLOCK result</li>
                      <li>evaluated scope</li>
                      <li>decision reasons</li>
                      <li>affected assets</li>
                      <li>required validation gates</li>
                      <li>prohibited next stages</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION OUTCOME REFERENCE</span>
                    <p className="text-stone-500 italic text-[10px] font-bold">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>overall validation outcome</li>
                      <li>tested scope</li>
                      <li>limitations</li>
                      <li>required validator results</li>
                      <li>failure outcome when applicable</li>
                      <li>artifact references</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHORIZATION RECORD</span>
                    <p className="text-stone-500 italic text-[10px] font-bold">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>permitted operation</li>
                      <li>predecessor references</li>
                      <li>required decision and validation state</li>
                      <li>recorded authorization status</li>
                      <li>relevant limitations</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">EFFECTIVE CONFIGURATION REFERENCE</span>
                    <p className="text-stone-500 italic text-[10px] font-bold">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>writeback enabled state</li>
                      <li>permitted record categories</li>
                      <li>configured destination mappings</li>
                      <li>redaction-policy reference</li>
                      <li>artifact-reference policy</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">TARGET ASSET REFERENCES</span>
                    <p className="text-stone-500 italic text-[10px] font-bold">May identify:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>configured metadata asset</li>
                      <li>repository or catalog reference</li>
                      <li>evaluated revision or schema scope</li>
                      <li>owner reference when required</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PERMITTED WRITEBACK CONTENT</span>
                    <p className="text-stone-500 italic text-[10px] font-bold">May include:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 font-mono text-[10px]">
                      <li>recorded risk status</li>
                      <li>concise decision reasons</li>
                      <li>evaluated-scope statement</li>
                      <li>validation outcome</li>
                      <li>tested-scope statement</li>
                      <li>deprecation or remediation references</li>
                      <li>owner actions</li>
                      <li>incident status</li>
                      <li>permitted artifact references</li>
                    </ul>
                  </div>
                </div>

                <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="writeback-inputs-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Target inputs required to prepare and authorize a RIFTLESS metadata writeback operation.
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
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK DECISION REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide current deterministic status, reasons, and protected-transition requirements.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Risk result does not execute writeback.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION OUTCOME REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Provide a required Validation Bundle or non-success outcome reference.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required when configured policy or the selected writeback record category requires validation.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Validation evidence or non-success status does not authorize writeback independently.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">AUTHORIZATION RECORD</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record permission for the specific protected operation.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Must be distinct from model output and destination success.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">EFFECTIVE CONFIGURATION REFERENCE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify enabled capability, permitted categories, and destination mappings.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configuration does not prove authorization or execution success.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">TARGET ASSET REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Identify the organizational metadata destination associated with the reviewed change.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Required.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Destination existence does not permit mutation.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">PERMITTED ARTIFACT REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Associate the metadata record with review evidence.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Conditional by configured writeback category.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">References must not expose secrets or unrestricted content.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* RECORD CATEGORIES */}
              <section className="space-y-4" aria-labelledby="writeback-categories-heading">
                <h3 id="writeback-categories-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Record Categories
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract describes seven conceptual record categories depending on organizational tracking requirements:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  {/* RISK STATUS RECORD */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">A. RISK STATUS RECORD</span>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">Target purpose:</p>
                    <p className="text-stone-600 leading-relaxed">Expose the recorded ALLOW, WARN, or BLOCK result for the evaluated asset and scope.</p>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">May include:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Risk Decision reference</li>
                      <li>status</li>
                      <li>concise reasons</li>
                      <li>evaluated scope</li>
                      <li>required next action</li>
                    </ul>
                    <p className="text-red-700 italic font-semibold text-[10px] font-mono">Must not:</p>
                    <ul className="list-disc pl-4 text-red-800 space-y-1 font-mono">
                      <li>imply universal safety</li>
                      <li>hide missing-context limitations</li>
                      <li>convert WARN into ALLOW</li>
                      <li>present BLOCK as approved</li>
                    </ul>
                  </div>

                  {/* DECISION DOCUMENT */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">B. DECISION DOCUMENT</span>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">Target purpose:</p>
                    <p className="text-stone-600 leading-relaxed">Preserve permitted decision explanation and referenced policy outcomes.</p>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">May include:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>decision reasons</li>
                      <li>policy-result references</li>
                      <li>affected assets</li>
                      <li>context limitations</li>
                      <li>required validation or review actions</li>
                    </ul>
                    <p className="text-red-700 italic font-semibold text-[10px] font-mono">Must not:</p>
                    <ul className="list-disc pl-4 text-red-800 space-y-1 font-mono">
                      <li>expose unrestricted Context Pack content</li>
                      <li>expose secret policy values</li>
                      <li>include private model reasoning</li>
                    </ul>
                  </div>

                  {/* VALIDATION RESULT */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">C. VALIDATION RESULT</span>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">Target purpose:</p>
                    <p className="text-stone-600 leading-relaxed">Associate the reviewed asset with the recorded scope-bound validation outcome.</p>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">May include:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>Validation Bundle reference</li>
                      <li>overall outcome</li>
                      <li>tested scope</li>
                      <li>limitations</li>
                      <li>failed or skipped checks when permitted</li>
                    </ul>
                    <p className="text-red-700 italic font-semibold text-[10px] font-mono">Must not:</p>
                    <ul className="list-disc pl-4 text-red-800 space-y-1 font-mono">
                      <li>represent failed or partial validation as fully successful</li>
                      <li>describe model output as executed evidence</li>
                      <li>represent a validation failure as a validation success</li>
                    </ul>
                  </div>

                  {/* DEPRECATION NOTE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">D. DEPRECATION NOTE</span>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">Target purpose:</p>
                    <p className="text-stone-600 leading-relaxed">Record a configured staged compatibility or removal plan.</p>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">May include:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>affected field or asset references</li>
                      <li>approved transition description</li>
                      <li>required owner actions</li>
                      <li>target review dates only when implementation defines them</li>
                      <li>remediation references</li>
                    </ul>
                    <p className="text-red-700 italic font-semibold text-[10px] font-mono">Must not:</p>
                    <ul className="list-disc pl-4 text-red-800 space-y-1 font-mono">
                      <li>imply remediation was deployed</li>
                      <li>silently clear a Risk Decision</li>
                    </ul>
                  </div>

                  {/* OWNER ACTION */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">E. OWNER ACTION</span>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">Target purpose:</p>
                    <p className="text-stone-600 leading-relaxed">Record a required human follow-up associated with the decision.</p>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">May include:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>owner reference</li>
                      <li>action description</li>
                      <li>warning or block reason</li>
                      <li>relevant artifact references</li>
                      <li>action status when implementation defines it</li>
                    </ul>
                    <p className="text-red-700 italic font-semibold text-[10px] font-mono">Must not:</p>
                    <ul className="list-disc pl-4 text-red-800 space-y-1 font-mono">
                      <li>fabricate owner identity</li>
                      <li>act as model-generated approval</li>
                    </ul>
                  </div>

                  {/* INCIDENT STATUS */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">F. INCIDENT STATUS</span>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">Target purpose:</p>
                    <p className="text-stone-600 leading-relaxed">Record a relevant blocked or failed review condition as a failure outcome.</p>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">May include:</p>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1">
                      <li>failure category</li>
                      <li>affected asset</li>
                      <li>decision reference</li>
                      <li>validation failure reference</li>
                      <li>permitted diagnostic reference</li>
                    </ul>
                    <p className="text-red-700 italic font-semibold text-[10px] font-mono">Must not:</p>
                    <ul className="list-disc pl-4 text-red-800 space-y-1 font-mono">
                      <li>expose secret logs</li>
                      <li>imply an operational incident system already exists</li>
                    </ul>
                  </div>

                  {/* ARTIFACT REFERENCES */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">G. ARTIFACT REFERENCES</span>
                    <p className="text-stone-500 italic text-[10px] font-bold font-mono">Target purpose:</p>
                    <p className="text-stone-600 leading-relaxed">Associate permitted evidence references with the organizational metadata record.</p>
                    <p className="text-red-700 italic font-semibold text-[10px] font-mono">Must not:</p>
                    <ul className="list-disc pl-4 text-red-800 space-y-1 font-mono">
                      <li>embed unrestricted logs</li>
                      <li>embed credentials</li>
                      <li>replace source artifacts with untraceable summaries</li>
                    </ul>
                  </div>
                </div>

                <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="writeback-categories-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Conceptual RIFTLESS review records and their target organizational metadata purpose.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Record Category</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Purpose</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Required Source</th>
                        <th scope="col" className="px-4 py-3 w-1/4">Write Condition</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">RISK STATUS RECORD</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Expose recorded deterministic review status.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Risk Decision and target asset reference.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Recorded authorization and configured mapping. The recorded status may be ALLOW, WARN, or BLOCK.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DECISION DOCUMENT</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Preserve permitted decision reasons and evaluated scope.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Risk Decision and permitted policy-result references.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Recorded authorization. Successful validation is required only when configured policy or the written content depends on it.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">VALIDATION RESULT</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Preserve scope-bound validation outcome and evidence references.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">A required Validation Bundle or non-success outcome reference.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configured validation-result mapping and recorded authorization. The written result may represent success or non-success.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">DEPRECATION NOTE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record a staged compatibility or removal plan.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Approved decision path and permitted remediation references.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configured mapping, recorded authorization, and required review state.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">OWNER ACTION</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record required human follow-up.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Owner reference, required action, and decision reason.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configured owner-action mapping and recorded authorization.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">INCIDENT STATUS</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Record a relevant blocked or failed review condition as a failure outcome.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Failure reason and affected asset reference.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Configured incident-status mapping and recorded authorization.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-900 bg-stone-50/20 text-left align-top">ARTIFACT REFERENCES</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Link organizational metadata to permitted review evidence.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Permitted artifact references.</td>
                        <td className="px-4 py-3 text-stone-600 leading-relaxed align-top">Recorded authorization and references that pass configured content and redaction rules.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* DESTINATION MAPPING */}
              <section className="space-y-4" aria-labelledby="writeback-mapping-heading">
                <h3 id="writeback-mapping-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Destination Mapping
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  Target mapping may identify specific metadata structures to synchronize with destinations:
                </p>

                <div className="border border-stone-200 rounded p-5 bg-white text-xs max-w-2xl space-y-3">
                  <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                    Target Destination Mappings May Define:
                  </span>
                  <ul className="list-disc pl-4 text-stone-600 space-y-1 font-mono text-[11px]">
                    <li>record category</li>
                    <li>configured destination type</li>
                    <li>target asset-reference strategy</li>
                    <li>permitted target fields</li>
                    <li>required source artifacts</li>
                    <li>required authorization state</li>
                    <li>field-level exclusion rules</li>
                    <li>mapping version or implementation reference when available</li>
                    <li>rejection behavior</li>
                    <li>required result references</li>
                  </ul>

                  <hr className="border-stone-200" />

                  <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase tracking-wider">
                    Mapping Clarifications:
                  </span>
                  <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                    <li>mapping availability is not authorization</li>
                    <li>a mapping does not prove the destination exists</li>
                    <li>mapping success is distinct from operation success</li>
                    <li>missing required mapping prevents that record category from being written</li>
                    <li>unknown target fields must not be silently accepted</li>
                    <li>mappings must not include credentials</li>
                  </ul>
                </div>

                <div className="border-l-4 border-[#F2A93B] bg-amber-50/20 p-4 rounded-r text-xs text-amber-900 max-w-2xl leading-relaxed font-mono">
                  <strong>NOTE:</strong> Exact DataHub entity types, aspects, fields, GraphQL operations, REST operations, and destination schemas remain undefined until the writeback adapter is implemented.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* WRITEBACK OUTCOME STATES */}
              <section className="space-y-4" aria-labelledby="writeback-outcomes-heading">
                <h3 id="writeback-outcomes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Writeback Outcome States
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract defines six conceptual result states. These are conceptual states, not official enums:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">COMPLETED</span>
                    <p className="text-stone-600 leading-relaxed font-mono">
                      All requested and permitted record categories in the operation were accepted by the configured destination. This means only that the metadata write completed for the recorded scope. It does not imply: Risk Decision is ALLOW, validation passed, deployment is authorized, or the change is safe.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PARTIAL</span>
                    <p className="text-stone-600 leading-relaxed">
                      Some permitted record categories completed while others were rejected or unavailable.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REJECTED</span>
                    <p className="text-stone-600 leading-relaxed">
                      The destination or adapter declined the requested operation or one of its required fields.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">FAILED</span>
                    <p className="text-stone-600 leading-relaxed">
                      The operation could not complete because of configuration, access, destination, or runtime failure.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">NOT ATTEMPTED</span>
                    <p className="text-stone-600 leading-relaxed">
                      Entry requirements were not satisfied or the operation was intentionally not started.
                    </p>
                  </div>
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">OUTCOME UNAVAILABLE</span>
                    <p className="text-stone-600 leading-relaxed">
                      The adapter could not determine or record the final destination result.
                    </p>
                  </div>
                </div>

                <div className="border border-stone-200 rounded p-4 bg-stone-50/50 max-w-3xl space-y-1.5 text-xs font-mono text-stone-700">
                  <div className="font-bold text-stone-900 mb-1 uppercase tracking-wider text-[10px]">Outcome Logic Clarifications:</div>
                  <ul className="list-disc pl-5 space-y-1 font-sans text-[11px]">
                    <li>PARTIAL is not COMPLETED.</li>
                    <li>REJECTED and FAILED are distinct non-success outcomes. Neither may be presented as COMPLETED.</li>
                    <li>NOT ATTEMPTED must not appear as a destination failure.</li>
                    <li>OUTCOME UNAVAILABLE must not silently become COMPLETED.</li>
                    <li>authorization does not imply COMPLETED.</li>
                    <li>an attempted operation does not imply COMPLETED.</li>
                  </ul>
                </div>

                <div className="overflow-x-auto border border-stone-200 rounded my-6 max-w-4xl">
                  <table className="min-w-full divide-y divide-stone-200 text-left text-xs font-mono" id="writeback-outcome-table">
                    <caption className="px-4 py-3 bg-stone-50 border-b border-stone-200 text-left text-xs font-mono font-bold text-stone-500 uppercase">
                      Conceptual writeback outcome states and their recording requirements.
                    </caption>
                    <thead className="bg-stone-50 text-stone-700 font-mono text-[10px] uppercase font-bold tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Outcome</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Meaning</th>
                        <th scope="col" className="px-4 py-3 border-r border-stone-200 w-1/4">Success Interpretation</th>
                        <th scope="col" className="px-4 py-3 w-1/4">Required Record</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-emerald-700 bg-emerald-50/10 text-left align-top">COMPLETED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">All requested permitted categories were accepted. This means only that the metadata write completed for the recorded scope. It does not imply approval or safety.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Operation may be reported as completed for the recorded scope.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Accepted categories, destination references, and recorded scope.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-amber-700 bg-amber-50/10 text-left align-top">PARTIAL</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Only part of the operation completed.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Must not be reported as fully completed.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Accepted and rejected categories with reasons when available.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-red-700 bg-red-50/10 text-left align-top">REJECTED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Destination declined the operation or required content.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">No completed result may be inferred.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Rejection category and permitted response reference.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-red-700 bg-red-50/10 text-left align-top">FAILED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Operation could not complete.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">No success status may be recorded.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Failure category and permitted diagnostic reference.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-700 bg-stone-50/10 text-left align-top">NOT ATTEMPTED</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Operation did not begin.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">No destination outcome exists.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Reason entry requirements were not satisfied.</td>
                      </tr>
                      <tr>
                        <th scope="row" className="px-4 py-3 border-r border-stone-200 font-mono font-bold text-stone-700 bg-stone-50/10 text-left align-top">OUTCOME UNAVAILABLE</th>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Final destination result could not be established.</td>
                        <td className="px-4 py-3 border-r border-stone-200 text-stone-600 leading-relaxed align-top">Must not silently become completed.</td>
                        <td className="px-4 py-3 text-stone-700 leading-relaxed align-top">Unavailable-result reason and known operation references.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* WRITEBACK RECORD CONTRACT */}
              <section className="space-y-4" aria-labelledby="writeback-record-heading">
                <h3 id="writeback-record-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Writeback Record
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  A target Writeback Record reports the outcome of a configured metadata operation and its permitted source references.
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-5 max-w-2xl text-xs space-y-3">
                  <div className="space-y-1">
                    <span className="font-semibold text-stone-900 font-mono block text-[10px]">PURPOSE:</span>
                    <p className="text-stone-600 leading-relaxed text-[11px]">
                      Record the result of a configured metadata-writeback operation after required authorization has been recorded.
                    </p>
                  </div>

                  <hr className="border-stone-200" />

                  <div className="space-y-1">
                    <span className="font-semibold text-stone-900 font-mono block text-[10px]">TARGET CONTENT:</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 font-mono text-[11px]">
                      <li>authorization-record reference</li>
                      <li>Risk Decision reference</li>
                      <li>Validation Bundle or non-success reference</li>
                      <li>effective configuration reference</li>
                      <li>target asset references</li>
                      <li>destination-mapping reference</li>
                      <li>requested record categories</li>
                      <li>accepted record categories</li>
                      <li>rejected record categories</li>
                      <li>writeback outcome</li>
                      <li>destination references when available</li>
                      <li>failure or rejection reason</li>
                      <li>permitted diagnostic references</li>
                      <li>artifact references</li>
                      <li>evaluated revision or scope</li>
                      <li>limitations</li>
                    </ul>
                  </div>

                  <hr className="border-stone-200" />

                  <div className="space-y-1 text-[11px]">
                    <span className="font-semibold text-stone-900 font-mono block text-[10px]">AUTHORITY BOUNDARY:</span>
                    <p className="text-stone-600 leading-relaxed">
                      The Writeback Record reports a destination operation outcome. A completed writeback record means only that the permitted metadata operation completed for the recorded scope. It does not authorize deployment or represent approval.
                    </p>
                  </div>

                  <hr className="border-stone-200" />

                  <div className="space-y-1 text-red-900 text-[11px]">
                    <span className="font-bold font-mono block text-[10px] text-red-800">MUST NOT CONTAIN:</span>
                    <ul className="list-disc pl-4 space-y-1 text-red-800 font-mono">
                      <li>API credentials</li>
                      <li>access tokens</li>
                      <li>private keys</li>
                      <li>raw authorization headers</li>
                      <li>unrestricted Context Pack content</li>
                      <li>unrestricted validation logs</li>
                      <li>secret environment values</li>
                      <li>fabricated destination references</li>
                      <li>model output presented as authorization</li>
                      <li>failed operation presented as completed</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* CONTENT AND SECRET BOUNDARY */}
              <section className="space-y-4" aria-labelledby="writeback-boundary-heading">
                <h3 id="writeback-boundary-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Content and Secret Boundary
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract separates content that may be written from secrets that must remain excluded:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">MAY BE WRITTEN WHEN PERMITTED:</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>recorded risk status</li>
                      <li>concise decision reasons</li>
                      <li>evaluated-scope statement</li>
                      <li>affected asset references</li>
                      <li>validation outcome</li>
                      <li>tested-scope statement</li>
                      <li>limitations</li>
                      <li>owner actions</li>
                      <li>deprecation references</li>
                      <li>incident or failure status</li>
                      <li>permitted artifact references</li>
                    </ul>
                  </div>

                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-red-700 block uppercase">MUST REMAIN SERVER-SIDE OR EXCLUDED:</span>
                    <ul className="list-disc pl-4 text-red-800 space-y-1 font-mono text-[11px]">
                      <li>DataHub credentials</li>
                      <li>GitHub credentials</li>
                      <li>DeepSeek credentials</li>
                      <li>raw authorization headers</li>
                      <li>private keys</li>
                      <li>access tokens</li>
                      <li>secret environment values</li>
                      <li>unrestricted Context Pack content</li>
                      <li>unrestricted repository content</li>
                      <li>unrestricted validation logs</li>
                      <li>unrelated sensitive metadata</li>
                      <li>internal authorization secrets</li>
                    </ul>
                  </div>
                </div>

                <div className="border-l-4 border-[#F2A93B] bg-amber-50/20 p-4 rounded-r text-xs text-amber-900 max-w-2xl leading-relaxed font-mono text-[11px]">
                  <strong>WARNING:</strong> A value is not safe for organizational metadata merely because it appears in a Risk Decision, Validation Bundle, log, or model response. Configured writeback allowlist and redaction rules must evaluate it.
                </div>

                <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed text-[11px]">
                  <strong>NOTE:</strong> Runtime tests should verify that prohibited values are rejected or removed before writeback content is submitted or recorded.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* CONSISTENCY REQUIREMENTS */}
              <section className="space-y-4" aria-labelledby="writeback-consistency-heading">
                <h3 id="writeback-consistency-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Consistency Requirements
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract defines conceptual consistency requirements for validation, decisions, revision, authority, and destinations:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  {/* REVISION CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REVISION CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>writeback applies only to the evaluated revision or change scope</li>
                      <li>a changed candidate must not inherit an old completed writeback status automatically</li>
                      <li>stale decision or validation references must remain visible</li>
                      <li>a newer review may require a new authorization and operation</li>
                    </ul>
                  </div>

                  {/* AUTHORIZATION CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHORIZATION CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>authorization must reference the protected operation</li>
                      <li>authorization must reference required predecessor states</li>
                      <li>authorization must remain distinct from destination completion</li>
                      <li>model output cannot provide authorization</li>
                      <li>worker output cannot provide authorization independently</li>
                    </ul>
                  </div>

                  {/* DECISION CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DECISION CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>BLOCK does not permit deployment, approval representation, or successful-result writeback. An authorized writeback may preserve the BLOCK decision as organizational memory.</li>
                      <li>WARN requirements remain visible</li>
                      <li>acknowledgment does not rewrite WARN into ALLOW</li>
                      <li>ALLOW remains bounded to evaluated scope</li>
                    </ul>
                  </div>

                  {/* VALIDATION CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">VALIDATION CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>Required failed validation prevents successful-validation representation but may be preserved through an authorized validation-failure, incident, or decision record.</li>
                      <li>partial validation must not appear as complete validation</li>
                      <li>stale Validation Bundle must not silently apply to changed input</li>
                    </ul>
                  </div>

                  {/* DESTINATION CONSISTENCY */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2 md:col-span-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DESTINATION CONSISTENCY</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>requested and accepted categories remain distinguishable</li>
                      <li>rejected categories remain visible</li>
                      <li>attempted and completed operations remain distinguishable</li>
                      <li>destination references must correspond to the recorded operation when available</li>
                    </ul>
                  </div>

                  <div className="md:col-span-2 text-xs font-mono text-stone-700 font-semibold bg-stone-50/80 p-3 border border-stone-200 rounded leading-relaxed">
                    Writeback category and outcome semantics must remain explicit so preservation of a non-success result is never confused with approval.
                  </div>
                </div>

                <div className="border-l-4 border-stone-400 bg-stone-50 p-3 rounded-r text-xs text-stone-700 max-w-2xl font-mono leading-relaxed text-[11px]">
                  <strong>Clarification:</strong> These are target consistency requirements. Do not claim a writeback-record validator already exists.
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* TARGET OPERATION SHAPES */}
              <section className="space-y-4" aria-labelledby="writeback-operation-shapes-heading">
                <h3 id="writeback-operation-shapes-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Target Operation Shapes
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  These conceptual interfaces describe the target operations for planning and executing writeback stages:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  {/* Preparation Shape */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL WRITEBACK PREPARATION <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive current Risk Decision reference
receive required Validation Bundle or outcome reference
receive recorded authorization
receive effective writeback configuration
resolve target asset references
select permitted record categories
apply destination mappings
exclude prohibited values
return target writeback operation input`}
                    </pre>
                  </div>

                  {/* Execution Shape */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono tracking-wider text-stone-500 font-bold block uppercase">
                      CONCEPTUAL WRITEBACK EXECUTION <span className="text-stone-400 font-normal">(NON-EXECUTABLE TARGET INTERFACE)</span>
                    </span>
                    <pre className="bg-stone-50 border border-stone-200 p-4 rounded text-xs font-mono text-stone-700 overflow-x-auto leading-relaxed">
{`receive permitted writeback operation
validate required destination mapping
submit configured metadata operation
record accepted and rejected categories
record destination references when available
record completion, partial, rejection, or failure outcome
return target Writeback Record`}
                    </pre>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic max-w-2xl">
                  Exact adapter APIs, destination operations, request formats, entity identifiers, mapping schemas, result payloads, and retry behavior will be documented after repository-backed writeback adapters are implemented and versioned.
                </p>
              </section>

              <hr className="border-stone-200/50" />

              {/* REPEATED ATTEMPTS */}
              <section className="space-y-4" aria-labelledby="writeback-attempts-heading">
                <h3 id="writeback-attempts-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Repeated Attempts
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract defines how repeat operations and superseding states behave:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl text-xs">
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-2">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase font-bold text-[10px]">
                      Repeated Attempt Target Requirements:
                    </span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>a repeated attempt must reference the same reviewed scope or explicitly identify changed input</li>
                      <li>previous Writeback Records should remain referenced</li>
                      <li>a failed attempt must not be overwritten as though it never occurred</li>
                      <li>later successful completion must remain distinguishable from earlier failure</li>
                      <li>repeated attempts must not silently duplicate records once duplicate-handling behavior is implemented</li>
                      <li>a changed destination mapping may require a new operation record</li>
                      <li>a new authorization may be required when evaluated scope or operation content changes</li>
                      <li>current and superseded records should remain distinguishable</li>
                    </ul>
                  </div>
                </div>

                <Callout type="target">
                  The final duplicate-handling, idempotency, supersession, retry, and operation-history model must be derived from the implemented adapter and artifact contracts. This section defines no executable retry behavior.
                </Callout>
              </section>

              <hr className="border-stone-200/50" />

              {/* FAILURE BEHAVIOR */}
              <section className="space-y-4" aria-labelledby="writeback-failure-heading">
                <h3 id="writeback-failure-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Writeback Failure Behavior
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract defines non-success behavior when planning, execution, mapping, or destination access fails:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl text-xs">
                  {/* WRITEBACK CONFIGURATION UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">WRITEBACK CONFIGURATION UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>operation must not begin</li>
                      <li>missing configuration should remain visible</li>
                    </ul>
                  </div>

                  {/* AUTHORIZATION MISSING OR INVALID */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">AUTHORIZATION MISSING OR INVALID</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>operation must not begin</li>
                      <li>destination availability must not bypass authorization</li>
                    </ul>
                  </div>

                  {/* REQUIRED MAPPING UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">REQUIRED MAPPING UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>affected record category must not be submitted</li>
                      <li>missing mapping should remain explicit</li>
                    </ul>
                  </div>

                  {/* PROHIBITED CONTENT DETECTED */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PROHIBITED CONTENT DETECTED</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>prohibited value must not be submitted</li>
                      <li>failure reason should be recorded without reproducing the secret</li>
                    </ul>
                  </div>

                  {/* DESTINATION UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DESTINATION UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>operation must not be reported as completed</li>
                      <li>destination failure reason should be recorded when available</li>
                    </ul>
                  </div>

                  {/* DESTINATION REJECTED OPERATION */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">DESTINATION REJECTED OPERATION</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>rejected categories or fields should remain visible when available</li>
                      <li>no completed status should be inferred</li>
                    </ul>
                  </div>

                  {/* PARTIAL OPERATION */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">PARTIAL OPERATION</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>accepted and rejected categories remain distinguishable</li>
                      <li>full completion must not be reported</li>
                    </ul>
                  </div>

                  {/* OUTCOME UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">OUTCOME UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>final result must not silently become completed</li>
                      <li>known request or adapter references may remain recorded</li>
                    </ul>
                  </div>

                  {/* WRITEBACK RECORD INVALID */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">WRITEBACK RECORD INVALID</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>operation must not be reported as successfully recorded</li>
                      <li>UI must not infer completion from styling</li>
                    </ul>
                  </div>

                  {/* ARTIFACT STORAGE UNAVAILABLE */}
                  <div className="border border-stone-200 rounded p-4 bg-white space-y-1 lg:col-span-3">
                    <span className="font-mono text-[10px] font-bold text-stone-900 block uppercase">ARTIFACT STORAGE UNAVAILABLE</span>
                    <ul className="list-disc pl-4 text-stone-600 space-y-1 text-[11px]">
                      <li>Writeback Record must not be reported as successfully preserved</li>
                      <li>destination operation and artifact-storage success remain distinct</li>
                      <li>retry handling remains undefined</li>
                    </ul>
                  </div>
                </div>
              </section>

              <hr className="border-stone-200/50" />

              {/* WRITEBACK INVARIANTS */}
              <section className="space-y-4" aria-labelledby="writeback-invariants-heading">
                <h3 id="writeback-invariants-heading" className="text-xl font-display font-bold tracking-tight uppercase text-[var(--color-riftless-ink)]">
                  Writeback Invariants
                </h3>
                <p className="text-sm text-[var(--color-riftless-graph-gray)] leading-relaxed">
                  The target writeback contract defines the following writeback invariants:
                </p>

                <div className="border border-stone-200 rounded bg-stone-50/50 p-6 max-w-3xl space-y-3 font-mono text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK INPUT REMAINS IDENTIFIABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">DECISION STATUS REMAINS DETERMINISTIC.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">VALIDATION EVIDENCE REMAINS SCOPE-BOUND.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">AUTHORIZATION REMAINS SEPARATELY RECORDED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">MODEL OUTPUT REMAINS NON-AUTHORIZING.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">DESTINATION MAPPING REMAINS CONFIGURED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">PROHIBITED VALUES REMAIN EXCLUDED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">ATTEMPT REMAINS DISTINCT FROM COMPLETION.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">PARTIAL REMAINS DISTINCT FROM COMPLETED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">DESTINATION SUCCESS REMAINS DISTINCT FROM RECORD STORAGE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">STALE RESULTS DO NOT BECOME CURRENT.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">WRITEBACK OUTCOME REMAINS EXPLICIT.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">BLOCK REMAINS NON-APPROVING.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">FAILED VALIDATION REMAINS PRESERVED.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">NON-SUCCESS OUTCOMES REMAIN PRESERVABLE.</div>
                  </div>
                  <div className="h-px bg-stone-200" />
                  <div className="space-y-1">
                    <div className="font-bold text-[var(--color-riftless-ink)]">PERSISTENCE SUCCESS DOES NOT IMPLY APPROVAL.</div>
                  </div>
                </div>

                <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
                  These statements describe target writeback requirements, not proof that destination adapters, operation validation, duplicate handling, retry orchestration, or Writeback Record persistence have already been implemented.
                </p>
              </section>
            </section>
          ) : activeSection === 'Deployment Handoff' ? (
            <DeploymentHandoffSection />
          ) : activeSection === 'API Reference' ? (
            <ApiReferenceSection />
          ) : activeSection === 'Failure Recovery' ? (
            <FailureRecoverySection />
          ) : activeSection === 'Security' ? (
            <SecuritySection />
          ) : activeSection === 'Observability' ? (
            <ObservabilitySection />
          ) : (
            <article className="space-y-8">
              {/* Target Outline Fallback Area */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase font-semibold">
                  Technical Reference Guide
                </span>
                <h2 className="text-3xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
                  {activeSection}
                </h2>
              </div>

              {/* Callout Target */}
              <Callout type="target">
                This document represents a planned target capability block of the RIFTLESS system architecture.
              </Callout>

              <div className="bg-stone-50 border border-stone-200 rounded p-6 text-stone-700 space-y-4">
                <p className="text-sm leading-relaxed">
                  The <span className="font-semibold text-[var(--color-riftless-ink)]">{activeSection}</span> specifications and operational guides are part of the target system release model.
                </p>
                <p className="text-xs text-[var(--color-riftless-graph-gray)]">
                  Refer to the <button onClick={() => handleSectionClick('Introduction')} className="text-[var(--color-riftless-ink)] font-semibold underline hover:text-stone-600 focus:outline-none transition-colors duration-150">Introduction</button> to read the verified workspace analysis model and deterministic validation architecture rules.
                </p>
              </div>

              <hr className="border-stone-200" />

              <section className="space-y-4">
                <h3 className="text-sm font-mono tracking-wider uppercase text-stone-500 font-semibold">
                  Planned Section Outline Overview
                </h3>
                <ul className="list-disc pl-5 space-y-2 text-xs text-stone-600 font-mono leading-relaxed">
                  <li>Structural configuration schema mappings</li>
                  <li>Deterministic security boundary validations</li>
                  <li>System invariants under active telemetry evaluation</li>
                </ul>
              </section>
            </article>
          )}
        </main>
      </div>
    </div>
  );
}
