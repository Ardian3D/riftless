/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link } from 'react-router-dom';
import { BrandLogo } from '../BrandLogo';

export function PublicFooter() {
  return (
    <footer className="w-full bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] py-16 px-4 sm:px-6 lg:px-8 border-t border-slate-800/80 select-none">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-12 md:gap-8 items-start">
        
        {/* Brand Info */}
        <div className="md:col-span-5 space-y-4">
          <div className="bg-[var(--color-riftless-paper)] px-3.5 py-2 rounded inline-flex items-center justify-center border border-slate-200/40 shadow-sm">
            <BrandLogo />
          </div>
          <p className="text-sm font-sans text-[var(--color-riftless-muted)] max-w-sm italic">
            “Ship changes. Not fallout.”
          </p>
        </div>

        {/* Navigation Links */}
        <div className="md:col-span-4 grid grid-cols-2 gap-4">
          <div className="space-y-3">
            <span className="block text-[10px] font-mono tracking-widest text-slate-500 uppercase">
              SYSTEM
            </span>
            <ul className="space-y-2 text-xs font-mono text-[var(--color-riftless-muted)]">
              <li>
                <Link to="/" className="inline-block hover:text-white hover:pl-1 transition-all duration-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-riftless-signal)] rounded px-1 motion-reduce:hover:pl-0">Product</Link>
              </li>
              <li>
                <Link to="/architecture" className="inline-block hover:text-white hover:pl-1 transition-all duration-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-riftless-signal)] rounded px-1 motion-reduce:hover:pl-0">Architecture</Link>
              </li>
              <li>
                <Link to="/docs" className="inline-block hover:text-white hover:pl-1 transition-all duration-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-riftless-signal)] rounded px-1 motion-reduce:hover:pl-0">Docs</Link>
              </li>
            </ul>
          </div>

          <div className="space-y-3">
            <span className="block text-[10px] font-mono tracking-widest text-slate-500 uppercase">
              RESOURCES
            </span>
            <ul className="space-y-2 text-xs font-mono text-[var(--color-riftless-muted)]">
              <li>
                <Link to="/demo" className="inline-block hover:text-white hover:pl-1 transition-all duration-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-riftless-signal)] rounded px-1 motion-reduce:hover:pl-0">Demo</Link>
              </li>
              <li>
                <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="inline-block hover:text-white hover:pl-1 transition-all duration-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-riftless-signal)] rounded px-1 motion-reduce:hover:pl-0">
                  View Source
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Legal / Copyright */}
        <div className="md:col-span-3 space-y-3 font-mono text-xs text-[var(--color-riftless-muted)] md:text-right">
          <span className="block text-[10px] tracking-widest text-slate-500 uppercase">
            LEGAL
          </span>
          <p className="hover:text-white hover:pl-1 transition-all duration-300 inline-block motion-reduce:hover:pl-0">Open source under Apache License 2.0.</p>
          <p className="text-slate-500 text-[11px] pt-2">RIFTLESS &copy; 2026</p>
        </div>

      </div>
    </footer>
  );
}
