/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { NavLink, Outlet, Link } from 'react-router-dom';
import { BrandLogo } from '../components/BrandLogo';

export function AppLayout() {
  return (
    <div className="min-h-screen bg-riftless-ink text-slate-100 font-sans antialiased flex flex-col selection:bg-[var(--color-riftless-signal)] selection:text-[var(--color-riftless-ink)]">
      {/* App Header */}
      <header className="w-full bg-riftless-ink border-b border-slate-800 sticky top-0 z-50">
        {/* Desktop Header Layout */}
        <div className="hidden md:flex max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <Link
                to="/"
                className="focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] rounded-md flex items-center"
                aria-label="RIFTLESS Home"
              >
                {/* Wrapped in warm-paper background wrapper to preserve official branding colors on a dark background */}
                <div className="bg-[var(--color-riftless-paper)] px-2 py-1 rounded flex items-center justify-center">
                  <BrandLogo />
                </div>
              </Link>
              <span className="text-[10px] font-mono tracking-widest text-[var(--color-riftless-signal)] uppercase border border-[var(--color-riftless-signal)]/30 px-2 py-0.5 rounded bg-[var(--color-riftless-signal)]/10 font-bold">
                CONSOLE
              </span>
            </div>

            {/* Desktop Dashboard Navigation */}
            <nav aria-label="Application Navigation" className="flex items-center gap-4">
              <NavLink
                to="/app/overview"
                className={({ isActive }) =>
                  `text-sm font-medium px-3 py-1.5 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] ${
                    isActive
                      ? 'bg-slate-800 text-white font-semibold border-b-2 border-[var(--color-riftless-signal)]'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`
                }
              >
                Overview
              </NavLink>
              <NavLink
                to="/app/analyze"
                className={({ isActive }) =>
                  `text-sm font-medium px-3 py-1.5 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] ${
                    isActive
                      ? 'bg-slate-800 text-white font-semibold border-b-2 border-[var(--color-riftless-signal)]'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`
                }
              >
                Analyze
              </NavLink>
              <NavLink
                to="/app/runs"
                className={({ isActive }) =>
                  `text-sm font-medium px-3 py-1.5 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] ${
                    isActive
                      ? 'bg-slate-800 text-white font-semibold border-b-2 border-[var(--color-riftless-signal)]'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`
                }
              >
                Runs
              </NavLink>
            </nav>
          </div>

          <div className="flex items-center">
            <Link
              to="/"
              className="text-xs font-mono tracking-wider text-slate-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] px-2 py-1 rounded whitespace-nowrap"
            >
              ← Exit App
            </Link>
          </div>
        </div>

        {/* Mobile Header Layout (2-row system) */}
        <div className="md:hidden flex flex-col w-full px-4 py-2.5 gap-2">
          {/* Row 1: Logo left, Exit App right */}
          <div className="flex items-center justify-between h-11">
            <Link
              to="/"
              className="focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] rounded-md flex items-center"
              aria-label="RIFTLESS Home"
            >
              <div className="bg-[var(--color-riftless-paper)] px-2 py-1 rounded flex items-center justify-center">
                <BrandLogo />
              </div>
            </Link>

            <Link
              to="/"
              className="text-xs font-mono tracking-wider text-slate-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] px-2 py-1.5 rounded whitespace-nowrap"
            >
              ← Exit App
            </Link>
          </div>

          {/* Row 2: Navigation across screen width */}
          <nav aria-label="Application Mobile Navigation" className="flex items-center gap-1 border-t border-slate-800/80 pt-2 pb-0.5">
            <NavLink
              to="/app/overview"
              className={({ isActive }) =>
                `flex-1 text-center text-xs font-medium py-2 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] ${
                  isActive
                    ? 'bg-slate-800 text-[var(--color-riftless-signal)] font-semibold border-b border-[var(--color-riftless-signal)]'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`
              }
            >
              Overview
            </NavLink>
            <NavLink
              to="/app/analyze"
              className={({ isActive }) =>
                `flex-1 text-center text-xs font-medium py-2 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] ${
                  isActive
                    ? 'bg-slate-800 text-[var(--color-riftless-signal)] font-semibold border-b border-[var(--color-riftless-signal)]'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`
              }
            >
              Analyze
            </NavLink>
            <NavLink
              to="/app/runs"
              className={({ isActive }) =>
                `flex-1 text-center text-xs font-medium py-2 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-signal)] ${
                  isActive
                    ? 'bg-slate-800 text-[var(--color-riftless-signal)] font-semibold border-b border-[var(--color-riftless-signal)]'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`
              }
            >
              Runs
            </NavLink>
          </nav>
        </div>
      </header>

      {/* Main Panel */}
      <main className="flex-grow max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>

      {/* App Footer */}
      <footer className="py-6 text-center text-[10px] text-[var(--color-riftless-graph-gray)] font-mono tracking-wide uppercase border-t border-slate-200/50 mt-auto">
        <p>Riftless Console &copy; {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}
