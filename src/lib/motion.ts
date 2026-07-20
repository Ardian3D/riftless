import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import type { RefObject } from 'react';

// Register ScrollTrigger once on the client side
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export function registerMotionPlugins() {
  if (typeof window !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);
  }
}

export const MOTION_CONFIG = {
  duration: {
    fast: 0.3,
    normal: 0.6,
    slow: 1.0,
    intro: 1.2,
  },
  ease: {
    out: 'power2.out',
    inOut: 'power2.inOut',
    display: 'power3.out',
    bezier: 'cubic-bezier(0.25, 1, 0.5, 1)',
  }
};

/**
 * Creates a standard GSAP animation context helper to handle easy cleanup on component unmount
 */
export function createGsapContext(scope: RefObject<any> | HTMLElement) {
  const ctx = gsap.context(() => {}, scope);
  return ctx;
}
