/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Outlet } from 'react-router-dom';
import { Header } from '../components/Header';
import { PublicFooter } from '../components/layout/PublicFooter';

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-[var(--color-riftless-paper)] text-[var(--color-riftless-ink)] font-sans antialiased flex flex-col justify-between selection:bg-[var(--color-riftless-ink)] selection:text-[var(--color-riftless-paper)]">
      {/* Background Subtle Accent */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,#b8b8b0_0%,transparent_70%)] opacity-10 pointer-events-none" />

      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <main className="relative flex-grow flex flex-col z-10">
        <Outlet />
      </main>

      {/* Shared Dark Branded Footer */}
      <PublicFooter />
    </div>
  );
}
