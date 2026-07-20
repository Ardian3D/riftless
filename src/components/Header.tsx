/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link, NavLink, useNavigate } from 'react-router-dom';
import { BrandLogo } from './BrandLogo';
import { Button } from './Button';

export function Header() {
  const navigate = useNavigate();

  return (
    <header id="riftless-header" className="w-full bg-white border-b border-slate-200/80 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Brand Logo */}
        <div className="flex items-center">
          <Link
            id="header-logo-link"
            to="/"
            className="focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-ink)] rounded-md p-1 flex items-center"
            aria-label="RIFTLESS Home"
          >
            <BrandLogo />
          </Link>
        </div>

        {/* Right: Desktop Navigation & Action Buttons */}
        <div className="flex items-center gap-6">
          <nav aria-label="Main Navigation" className="hidden md:flex items-center gap-6">
            <NavLink
              id="nav-link-product"
              to="/"
              end
              className={({ isActive }) =>
                `text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-ink)] rounded-md px-2 py-1 relative pb-1.5 after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[var(--color-riftless-ink)] after:transition-transform after:duration-300 motion-reduce:after:transition-none ${
                  isActive
                    ? 'text-[var(--color-riftless-ink)] font-semibold after:scale-x-100'
                    : 'text-[var(--color-riftless-graph-gray)] hover:text-[var(--color-riftless-ink)] after:scale-x-0 hover:after:scale-x-100 after:origin-left'
                }`
              }
            >
              Product
            </NavLink>
            <NavLink
              id="nav-link-architecture"
              to="/architecture"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-ink)] rounded-md px-2 py-1 relative pb-1.5 after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[var(--color-riftless-ink)] after:transition-transform after:duration-300 motion-reduce:after:transition-none ${
                  isActive
                    ? 'text-[var(--color-riftless-ink)] font-semibold after:scale-x-100'
                    : 'text-[var(--color-riftless-graph-gray)] hover:text-[var(--color-riftless-ink)] after:scale-x-0 hover:after:scale-x-100 after:origin-left'
                }`
              }
            >
              Architecture
            </NavLink>
            <NavLink
              id="nav-link-docs"
              to="/docs"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-ink)] rounded-md px-2 py-1 relative pb-1.5 after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[var(--color-riftless-ink)] after:transition-transform after:duration-300 motion-reduce:after:transition-none ${
                  isActive
                    ? 'text-[var(--color-riftless-ink)] font-semibold after:scale-x-100'
                    : 'text-[var(--color-riftless-graph-gray)] hover:text-[var(--color-riftless-ink)] after:scale-x-0 hover:after:scale-x-100 after:origin-left'
                }`
              }
            >
              Docs
            </NavLink>
            <NavLink
              id="nav-link-demo"
              to="/demo"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-riftless-ink)] rounded-md px-2 py-1 relative pb-1.5 after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[var(--color-riftless-ink)] after:transition-transform after:duration-300 motion-reduce:after:transition-none ${
                  isActive
                    ? 'text-[var(--color-riftless-ink)] font-semibold after:scale-x-100'
                    : 'text-[var(--color-riftless-graph-gray)] hover:text-[var(--color-riftless-ink)] after:scale-x-0 hover:after:scale-x-100 after:origin-left'
                }`
              }
            >
              Demo
            </NavLink>
          </nav>

          <div className="flex items-center gap-2">
            <Button
              id="btn-view-source"
              variant="outline"
              size="sm"
              onClick={() => {
                window.open('https://github.com', '_blank', 'noopener,noreferrer');
              }}
              className="text-xs py-1.5 px-3 border-slate-200 text-[var(--color-riftless-graph-gray)] hover:text-[var(--color-riftless-ink)] hover:border-slate-300"
            >
              View Source
            </Button>
            
            {/* Quick Demo Action for mobile layout */}
            <Button
              id="btn-header-demo-mobile"
              variant="primary"
              size="sm"
              onClick={() => navigate('/demo')}
              className="md:hidden text-xs py-1.5 px-3 bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] hover:bg-slate-800"
            >
              Demo
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
