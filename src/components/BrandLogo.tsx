/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import riftlessLogo from '../assets/brand/riftless-logo.png';

interface BrandLogoProps {
  className?: string;
  alt?: string;
  variant?: 'full' | 'symbol';
}

export function BrandLogo({ className = '', alt = 'RIFTLESS' }: BrandLogoProps) {
  // TODO: Symbol-only variant is postponed until official symbol asset is available.
  // Currently only supporting full logo (riftless-logo.png) as requested.
  return (
    <div className={`inline-flex items-center justify-center bg-transparent ${className}`}>
      <img
        id="riftless-brand-logo-img"
        src={riftlessLogo}
        alt={alt}
        className="w-[105px] md:w-[115px] h-auto object-contain select-none"
        referrerPolicy="no-referrer"
      />
    </div>
  );
}
