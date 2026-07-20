/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/Button';
import { BrandLogo } from '../components/BrandLogo';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { registerMotionPlugins } from '../lib/motion';

gsap.registerPlugin(ScrollTrigger);

export function HomePage() {
  const isReducedMotion = useReducedMotion();
  const heroRef = useRef<HTMLDivElement>(null);
  const problemRef = useRef<HTMLDivElement>(null);
  const systemRef = useRef<HTMLDivElement>(null);
  const contextRef = useRef<HTMLDivElement>(null);
  const repairRef = useRef<HTMLDivElement>(null);
  const memoryRef = useRef<HTMLDivElement>(null);
  const readyToShipRef = useRef<HTMLDivElement>(null);



  useEffect(() => {
    if (isReducedMotion) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        defaults: {
          ease: 'power3.out',
          duration: 0.8
        }
      });

      tl.fromTo('.hero-label', 
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.6 }
      );

      tl.fromTo('.hero-headline', 
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.8 },
        '-=0.4'
      );

      tl.fromTo('.hero-sub', 
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.6 },
        '-=0.5'
      );

      tl.fromTo('.hero-cta-container', 
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.6 },
        '-=0.4'
      );

      tl.fromTo('.hero-proof', 
        { opacity: 0 },
        { opacity: 1, duration: 0.6 },
        '-=0.3'
      );

      tl.fromTo('.hero-lineage', 
        { opacity: 0, scale: 0.96 },
        { opacity: 1, scale: 1, duration: 0.8 },
        '-=0.5'
      );
    }, heroRef);

    return () => ctx.revert();
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    const q = gsap.utils.selector(problemRef);
    let active = true;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: problemRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      // Initial States
      gsap.set(q('.problem-label'), { autoAlpha: 0, y: 18 });
      gsap.set(q('.problem-title'), { autoAlpha: 0, y: 28 });
      gsap.set(q('.problem-description'), { autoAlpha: 0, y: 16 });
      gsap.set(q('.problem-graph'), { autoAlpha: 0, y: 20, scale: 0.96 });

      gsap.set([
        q('.prob-node-root'),
        q('.prob-conn-normal'),
        q('.prob-node-mid-normal'),
        q('.prob-node-end-normal'),
        q('.prob-conn-red-1'),
        q('.prob-node-red-1'),
        q('.prob-label-red-1'),
        q('.prob-conn-red-2'),
        q('.prob-node-red-2'),
        q('.prob-label-red-2')
      ], { opacity: 0 });

      // Timeline Animations
      tl.to(q('.problem-label'), {
        autoAlpha: 1,
        y: 0,
        duration: 0.5,
        ease: 'power2.out'
      });

      tl.to(q('.problem-title'), {
        autoAlpha: 1,
        y: 0,
        duration: 0.7,
        ease: 'power2.out'
      }, '-=0.3');

      tl.to(q('.problem-description'), {
        autoAlpha: 1,
        y: 0,
        duration: 0.5,
        ease: 'power2.out'
      }, '-=0.3');

      tl.to(q('.problem-graph'), {
        autoAlpha: 1,
        y: 0,
        scale: 1.0,
        duration: 0.7,
        ease: 'power2.out'
      }, '-=0.3');

      // SVG Graph Elements Sequence
      tl.fromTo(q('.prob-node-root'),
        { opacity: 0, scale: 0.9, transformOrigin: 'center center' },
        { opacity: 1, scale: 1, duration: 0.5 },
        '-=0.2'
      );

      tl.fromTo(q('.prob-conn-normal'),
        { opacity: 0 },
        { opacity: 1, duration: 0.4, stagger: 0.1 },
        '-=0.15'
      );

      tl.fromTo([q('.prob-node-mid-normal'), q('.prob-node-end-normal')],
        { opacity: 0, scale: 0.9, transformOrigin: 'center center' },
        { opacity: 1, scale: 1, duration: 0.5, stagger: 0.1 },
        '-=0.2'
      );

      tl.fromTo(q('.prob-conn-red-1'),
        { opacity: 0 },
        { opacity: 1, duration: 0.5 },
        '-=0.15'
      );

      tl.fromTo(q('.prob-node-red-1'),
        { opacity: 0, scale: 0.9, transformOrigin: 'center center' },
        { opacity: 1, scale: 1, duration: 0.5 },
        '-=0.2'
      );

      tl.fromTo(q('.prob-label-red-1'),
        { opacity: 0, y: 8 },
        { opacity: 1, y: 0, duration: 0.4 },
        '-=0.2'
      );

      tl.fromTo(q('.prob-conn-red-2'),
        { opacity: 0 },
        { opacity: 1, duration: 0.5 },
        '-=0.15'
      );

      tl.fromTo(q('.prob-node-red-2'),
        { opacity: 0, scale: 0.9, transformOrigin: 'center center' },
        { opacity: 1, scale: 1, duration: 0.5 },
        '-=0.2'
      );

      tl.fromTo(q('.prob-label-red-2'),
        { opacity: 0, y: 8 },
        { opacity: 1, y: 0, duration: 0.4 },
        '-=0.2'
      );

    }, problemRef);

    requestAnimationFrame(() => {
      if (active) ScrollTrigger.refresh();
    });

    if (typeof document !== 'undefined' && document.fonts) {
      document.fonts.ready.then(() => {
        if (active) ScrollTrigger.refresh();
      });
    }

    return () => {
      active = false;
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();
    const q = gsap.utils.selector(systemRef);
    let active = true;

    const mm = gsap.matchMedia(systemRef);

    // Desktop Layout >= 1024px
    mm.add("(min-width: 1024px)", () => {
      // Set initial states
      gsap.set(q('.system-label'), { autoAlpha: 0, y: 18 });
      gsap.set([q('.system-word-1'), q('.system-word-2'), q('.system-word-3'), q('.system-word-4')], { autoAlpha: 0, y: 26 });
      gsap.set(q('.system-sub'), { autoAlpha: 0, y: 16 });
      
      gsap.set([q('.sys-dot-1'), q('.sys-dot-2'), q('.sys-dot-3'), q('.sys-dot-4')], { autoAlpha: 0, scale: 0.94 });
      gsap.set([q('.sys-content-1'), q('.sys-content-2'), q('.sys-content-3'), q('.sys-content-4')], { autoAlpha: 0, scale: 0.94 });
      
      gsap.set([q('.sys-conn-1.sys-conn-desktop'), q('.sys-conn-2.sys-conn-desktop'), q('.sys-conn-3.sys-conn-desktop')], { autoAlpha: 0, scaleX: 0, transformOrigin: "left center" });
      gsap.set(q('.system-output-strip'), { autoAlpha: 0, y: 12 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: systemRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      tl.to(q('.system-label'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' })
        .to([q('.system-word-1'), q('.system-word-2'), q('.system-word-3'), q('.system-word-4')], {
          autoAlpha: 1,
          y: 0,
          duration: 0.55,
          stagger: 0.10,
          ease: 'power2.out'
        }, '-=0.35')
        .to(q('.system-sub'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.4')
        
        // Step 1
        .to([q('.sys-dot-1'), q('.sys-content-1')], { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.2')
        // Connector 1
        .to(q('.sys-conn-1.sys-conn-desktop'), { autoAlpha: 1, scaleX: 1, duration: 0.4, ease: 'none' }, '-=0.15')
        
        // Step 2
        .to([q('.sys-dot-2'), q('.sys-content-2')], { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.15')
        // Connector 2
        .to(q('.sys-conn-2.sys-conn-desktop'), { autoAlpha: 1, scaleX: 1, duration: 0.4, ease: 'none' }, '-=0.15')
        
        // Step 3
        .to([q('.sys-dot-3'), q('.sys-content-3')], { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.15')
        // Connector 3
        .to(q('.sys-conn-3.sys-conn-desktop'), { autoAlpha: 1, scaleX: 1, duration: 0.4, ease: 'none' }, '-=0.15')
        
        // Step 4
        .to([q('.sys-dot-4'), q('.sys-content-4')], { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.15')
        
        // Output strip
        .to(q('.system-output-strip'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.2');
    });

    // Mobile Layout < 1024px
    mm.add("(max-width: 1023px)", () => {
      // Set initial states
      gsap.set(q('.system-label'), { autoAlpha: 0, y: 18 });
      gsap.set([q('.system-word-1'), q('.system-word-2'), q('.system-word-3'), q('.system-word-4')], { autoAlpha: 0, y: 26 });
      gsap.set(q('.system-sub'), { autoAlpha: 0, y: 16 });
      
      gsap.set([q('.sys-dot-1'), q('.sys-dot-2'), q('.sys-dot-3'), q('.sys-dot-4')], { autoAlpha: 0, scale: 0.94 });
      gsap.set([q('.sys-content-1'), q('.sys-content-2'), q('.sys-content-3'), q('.sys-content-4')], { autoAlpha: 0, scale: 0.94 });
      
      gsap.set([q('.sys-conn-1.sys-conn-mobile'), q('.sys-conn-2.sys-conn-mobile'), q('.sys-conn-3.sys-conn-mobile')], { autoAlpha: 0, scaleY: 0, transformOrigin: "top center" });
      gsap.set(q('.system-output-strip'), { autoAlpha: 0, y: 12 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: systemRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      tl.to(q('.system-label'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' })
        .to([q('.system-word-1'), q('.system-word-2'), q('.system-word-3'), q('.system-word-4')], {
          autoAlpha: 1,
          y: 0,
          duration: 0.55,
          stagger: 0.10,
          ease: 'power2.out'
        }, '-=0.35')
        .to(q('.system-sub'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.4')
        
        // Step 1
        .to([q('.sys-dot-1'), q('.sys-content-1')], { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.2')
        // Connector 1
        .to(q('.sys-conn-1.sys-conn-mobile'), { autoAlpha: 1, scaleY: 1, duration: 0.4, ease: 'none' }, '-=0.15')
        
        // Step 2
        .to([q('.sys-dot-2'), q('.sys-content-2')], { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.15')
        // Connector 2
        .to(q('.sys-conn-2.sys-conn-mobile'), { autoAlpha: 1, scaleY: 1, duration: 0.4, ease: 'none' }, '-=0.15')
        
        // Step 3
        .to([q('.sys-dot-3'), q('.sys-content-3')], { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.15')
        // Connector 3
        .to(q('.sys-conn-3.sys-conn-mobile'), { autoAlpha: 1, scaleY: 1, duration: 0.4, ease: 'none' }, '-=0.15')
        
        // Step 4
        .to([q('.sys-dot-4'), q('.sys-content-4')], { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.15')
        
        // Output strip
        .to(q('.system-output-strip'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.2');
    });

    requestAnimationFrame(() => {
      if (active) ScrollTrigger.refresh();
    });

    if (typeof document !== 'undefined' && document.fonts) {
      document.fonts.ready.then(() => {
        if (active) ScrollTrigger.refresh();
      });
    }

    return () => {
      active = false;
      mm.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();
    const q = gsap.utils.selector(contextRef);
    let active = true;

    const mm = gsap.matchMedia(contextRef);

    // Desktop Layout >= 1024px
    mm.add("(min-width: 1024px)", () => {
      // Initial States
      gsap.set(q('.context-label'), { autoAlpha: 0, y: 18 });
      gsap.set(q('.context-line-1'), { autoAlpha: 0, y: 26 });
      gsap.set(q('.context-line-2'), { autoAlpha: 0, y: 26 });
      gsap.set(q('.context-badge'), { autoAlpha: 0, y: 14 });
      gsap.set(q('.context-desc'), { autoAlpha: 0, y: 14 });
      
      gsap.set(q('.context-node-center'), { autoAlpha: 0, scale: 0.94, transformOrigin: 'center center' });
      
      const connectors = [
        '.context-conn-schema',
        '.context-conn-lineage',
        '.context-conn-query',
        '.context-conn-ownership',
        '.context-conn-governance',
        '.context-conn-quality',
        '.context-conn-ml'
      ];
      connectors.forEach(conn => {
        gsap.set(q(conn), { autoAlpha: 0, attr: { x2: 260, y2: 190 } });
      });

      const nodes = [
        '.context-node-schema',
        '.context-node-lineage',
        '.context-node-query',
        '.context-node-ownership',
        '.context-node-governance',
        '.context-node-quality',
        '.context-node-ml'
      ];
      nodes.forEach(node => {
        gsap.set(q(node), { autoAlpha: 0, scale: 0.94, transformOrigin: 'center center' });
      });

      gsap.set(q('.context-output-badge'), { autoAlpha: 0, y: 12 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: contextRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      tl.to(q('.context-label'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' })
        .to(q('.context-line-1'), { autoAlpha: 1, y: 0, duration: 0.65, ease: 'power2.out' }, '-=0.35')
        .to(q('.context-line-2'), { autoAlpha: 1, y: 0, duration: 0.65, ease: 'power2.out' }, '-=0.45')
        .to([q('.context-badge'), q('.context-desc')], { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out', stagger: 0.1 }, '-=0.45')
        
        // Center Node
        .to(q('.context-node-center'), { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.3')
        
        // SCHEMA Node & Connector
        .to(q('.context-conn-schema'), { autoAlpha: 1, attr: { x2: 420, y2: 110 }, duration: 0.4, ease: 'power2.out' }, '-=0.25')
        .to(q('.context-node-schema'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.3')

        // COLUMN LINEAGE Node & Connector
        .to(q('.context-conn-lineage'), { autoAlpha: 1, attr: { x2: 440, y2: 190 }, duration: 0.4, ease: 'power2.out' }, '-=0.25')
        .to(q('.context-node-lineage'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.3')

        // Staggered other connectors and nodes
        .to(q('.context-conn-query'), { autoAlpha: 1, attr: { x2: 260, y2: 60 }, duration: 0.35, ease: 'power2.out' }, '-=0.2')
        .to(q('.context-node-query'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.25')

        .to(q('.context-conn-ownership'), { autoAlpha: 1, attr: { x2: 80, y2: 190 }, duration: 0.35, ease: 'power2.out' }, '-=0.2')
        .to(q('.context-node-ownership'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.25')

        .to(q('.context-conn-governance'), { autoAlpha: 1, attr: { x2: 100, y2: 110 }, duration: 0.35, ease: 'power2.out' }, '-=0.2')
        .to(q('.context-node-governance'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.25')

        .to(q('.context-conn-quality'), { autoAlpha: 1, attr: { x2: 100, y2: 270 }, duration: 0.35, ease: 'power2.out' }, '-=0.2')
        .to(q('.context-node-quality'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.25')

        .to(q('.context-conn-ml'), { autoAlpha: 1, attr: { x2: 420, y2: 270 }, duration: 0.35, ease: 'power2.out' }, '-=0.2')
        .to(q('.context-node-ml'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.25')

        // Output Strip
        .to(q('.context-output-badge'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.2');
    });

    // Mobile Layout < 1023px
    mm.add("(max-width: 1023px)", () => {
      // Initial States with max 8px translation
      gsap.set(q('.context-label'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.context-line-1'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.context-line-2'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.context-badge'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.context-desc'), { autoAlpha: 0, y: 8 });
      
      gsap.set(q('.context-node-center'), { autoAlpha: 0, scale: 0.96, transformOrigin: 'center center' });
      
      const connectors = [
        '.context-conn-schema',
        '.context-conn-lineage',
        '.context-conn-query',
        '.context-conn-ownership',
        '.context-conn-governance',
        '.context-conn-quality',
        '.context-conn-ml'
      ];
      connectors.forEach(conn => {
        gsap.set(q(conn), { autoAlpha: 0, attr: { x2: 260, y2: 190 } });
      });

      const nodes = [
        '.context-node-schema',
        '.context-node-lineage',
        '.context-node-query',
        '.context-node-ownership',
        '.context-node-governance',
        '.context-node-quality',
        '.context-node-ml'
      ];
      nodes.forEach(node => {
        gsap.set(q(node), { autoAlpha: 0, scale: 0.96, transformOrigin: 'center center' });
      });

      gsap.set(q('.context-output-badge'), { autoAlpha: 0, y: 8 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: contextRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      // Faster timeline for mobile
      tl.to(q('.context-label'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' })
        .to(q('.context-line-1'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.25')
        .to(q('.context-line-2'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.35')
        .to([q('.context-badge'), q('.context-desc')], { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.35')
        
        // Center Node
        .to(q('.context-node-center'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.25')
        
        // SCHEMA Node & Connector
        .to(q('.context-conn-schema'), { autoAlpha: 1, attr: { x2: 420, y2: 110 }, duration: 0.3, ease: 'power2.out' }, '-=0.2')
        .to(q('.context-node-schema'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.25')

        // COLUMN LINEAGE Node & Connector
        .to(q('.context-conn-lineage'), { autoAlpha: 1, attr: { x2: 440, y2: 190 }, duration: 0.3, ease: 'power2.out' }, '-=0.2')
        .to(q('.context-node-lineage'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.25')

        // Staggered other connectors and nodes (very fast)
        .to(q('.context-conn-query'), { autoAlpha: 1, attr: { x2: 260, y2: 60 }, duration: 0.25, ease: 'power2.out' }, '-=0.15')
        .to(q('.context-node-query'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.2')

        .to(q('.context-conn-ownership'), { autoAlpha: 1, attr: { x2: 80, y2: 190 }, duration: 0.25, ease: 'power2.out' }, '-=0.15')
        .to(q('.context-node-ownership'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.2')

        .to(q('.context-conn-governance'), { autoAlpha: 1, attr: { x2: 100, y2: 110 }, duration: 0.25, ease: 'power2.out' }, '-=0.15')
        .to(q('.context-node-governance'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.2')

        .to(q('.context-conn-quality'), { autoAlpha: 1, attr: { x2: 100, y2: 270 }, duration: 0.25, ease: 'power2.out' }, '-=0.15')
        .to(q('.context-node-quality'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.2')

        .to(q('.context-conn-ml'), { autoAlpha: 1, attr: { x2: 420, y2: 270 }, duration: 0.25, ease: 'power2.out' }, '-=0.15')
        .to(q('.context-node-ml'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.2')

        // Output Strip
        .to(q('.context-output-badge'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.15');
    });

    requestAnimationFrame(() => {
      if (active) ScrollTrigger.refresh();
    });

    if (typeof document !== 'undefined' && document.fonts) {
      document.fonts.ready.then(() => {
        if (active) ScrollTrigger.refresh();
      });
    }

    return () => {
      active = false;
      mm.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();
    const q = gsap.utils.selector(repairRef);
    let active = true;

    const mm = gsap.matchMedia(repairRef);

    // Desktop Layout >= 1024px
    mm.add("(min-width: 1024px)", () => {
      // Set initial states
      gsap.set(q('.repair-label'), { autoAlpha: 0, y: 18 });
      gsap.set([q('.repair-title-1'), q('.repair-title-2')], { autoAlpha: 0, y: 28 });
      gsap.set(q('.repair-desc'), { autoAlpha: 0, y: 16 });
      gsap.set(q('.repair-flow-label'), { autoAlpha: 0, y: 12 });

      // Panels
      gsap.set(q('.repair-panel-change'), { autoAlpha: 0, scale: 0.96, transformOrigin: 'center center' });
      gsap.set(q('.repair-panel-remediation'), { autoAlpha: 0, scale: 0.96, transformOrigin: 'center center' });

      // Left panel elements
      gsap.set(q('.repair-diff-line'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.repair-risk-badge'), { autoAlpha: 0, scale: 0.8, transformOrigin: 'center center' });
      gsap.set(q('.repair-blast-info'), { autoAlpha: 0, y: 10 });

      // Connector (Desktop only)
      gsap.set(q('.repair-connector-left'), { autoAlpha: 0, scaleX: 0, transformOrigin: 'left center' });
      gsap.set(q('.repair-connector-dot'), { autoAlpha: 0, scale: 0, transformOrigin: 'center center' });
      gsap.set(q('.repair-connector-right'), { autoAlpha: 0, scaleX: 0, transformOrigin: 'left center' });

      // Right panel elements
      gsap.set(q('.repair-active-badge'), { autoAlpha: 0, scale: 0.8, transformOrigin: 'center center' });
      gsap.set(q('.repair-patch-line'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.repair-artifact-item'), { autoAlpha: 0, x: -10 });

      // Validation Steps
      gsap.set([q('.repair-val-1'), q('.repair-val-2'), q('.repair-val-3'), q('.repair-val-4')], { autoAlpha: 0, y: 12 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: repairRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      tl.to(q('.repair-label'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' })
        .to([q('.repair-title-1'), q('.repair-title-2')], { autoAlpha: 1, y: 0, duration: 0.7, ease: 'power2.out', stagger: 0.15 }, '-=0.35')
        .to(q('.repair-desc'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.4')
        .to(q('.repair-flow-label'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.3')
        
        // Show Proposed Change Panel
        .to(q('.repair-panel-change'), { autoAlpha: 1, scale: 1, duration: 0.6, ease: 'power2.out' }, '-=0.25')
        
        // Animating inside Left Panel
        .to(q('.repair-diff-line'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.3')
        .to(q('.repair-risk-badge'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'back.out(1.7)' }, '-=0.35')
        .to(q('.repair-blast-info'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.3')

        // Connectors (Red line -> Dot -> Lime line)
        .to(q('.repair-connector-left'), { autoAlpha: 1, scaleX: 1, duration: 0.3, ease: 'none' }, '-=0.15')
        .to(q('.repair-connector-dot'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'back.out(1.7)' }, '-=0.1')
        .to(q('.repair-connector-right'), { autoAlpha: 1, scaleX: 1, duration: 0.3, ease: 'none' }, '-=0.1')

        // Show Remediation Panel
        .to(q('.repair-panel-remediation'), { autoAlpha: 1, scale: 1, duration: 0.6, ease: 'power2.out' }, '-=0.2')

        // Animating inside Right Panel
        .to(q('.repair-active-badge'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'back.out(1.7)' }, '-=0.4')
        .to(q('.repair-patch-line'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.35')
        .to(q('.repair-artifact-item'), { autoAlpha: 1, x: 0, duration: 0.35, stagger: 0.08, ease: 'power2.out' }, '-=0.3')

        // Validation Steps
        .to([q('.repair-val-1'), q('.repair-val-2'), q('.repair-val-3'), q('.repair-val-4')], {
          autoAlpha: 1,
          y: 0,
          duration: 0.4,
          stagger: 0.1,
          ease: 'power2.out'
        }, '-=0.2');
    });

    // Mobile Layout < 1024px
    mm.add("(max-width: 1023px)", () => {
      // Set initial states (with max 8px translation)
      gsap.set(q('.repair-label'), { autoAlpha: 0, y: 8 });
      gsap.set([q('.repair-title-1'), q('.repair-title-2')], { autoAlpha: 0, y: 8 });
      gsap.set(q('.repair-desc'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.repair-flow-label'), { autoAlpha: 0, y: 8 });

      // Panels
      gsap.set(q('.repair-panel-change'), { autoAlpha: 0, scale: 0.98, transformOrigin: 'center center' });
      gsap.set(q('.repair-panel-remediation'), { autoAlpha: 0, scale: 0.98, transformOrigin: 'center center' });

      // Left panel elements
      gsap.set(q('.repair-diff-line'), { autoAlpha: 0, y: 4 });
      gsap.set(q('.repair-risk-badge'), { autoAlpha: 0, scale: 0.9, transformOrigin: 'center center' });
      gsap.set(q('.repair-blast-info'), { autoAlpha: 0, y: 4 });

      // Right panel elements
      gsap.set(q('.repair-active-badge'), { autoAlpha: 0, scale: 0.9, transformOrigin: 'center center' });
      gsap.set(q('.repair-patch-line'), { autoAlpha: 0, y: 4 });
      gsap.set(q('.repair-artifact-item'), { autoAlpha: 0, x: -4 });

      // Validation Steps
      gsap.set([q('.repair-val-1'), q('.repair-val-2'), q('.repair-val-3'), q('.repair-val-4')], { autoAlpha: 0, y: 6 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: repairRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      tl.to(q('.repair-label'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' })
        .to([q('.repair-title-1'), q('.repair-title-2')], { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out', stagger: 0.1 }, '-=0.25')
        .to(q('.repair-desc'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.3')
        .to(q('.repair-flow-label'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.25')
        
        // Show Proposed Change Panel
        .to(q('.repair-panel-change'), { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.2')
        
        // Animating inside Left Panel
        .to(q('.repair-diff-line'), { autoAlpha: 1, y: 0, duration: 0.35, ease: 'power2.out' }, '-=0.25')
        .to(q('.repair-risk-badge'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.3')
        .to(q('.repair-blast-info'), { autoAlpha: 1, y: 0, duration: 0.35, ease: 'power2.out' }, '-=0.25')

        // Show Remediation Panel
        .to(q('.repair-panel-remediation'), { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.15')

        // Animating inside Right Panel
        .to(q('.repair-active-badge'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.3')
        .to(q('.repair-patch-line'), { autoAlpha: 1, y: 0, duration: 0.35, ease: 'power2.out' }, '-=0.25')
        .to(q('.repair-artifact-item'), { autoAlpha: 1, x: 0, duration: 0.3, stagger: 0.05, ease: 'power2.out' }, '-=0.25')

        // Validation Steps (Faster stagger)
        .to([q('.repair-val-1'), q('.repair-val-2'), q('.repair-val-3'), q('.repair-val-4')], {
          autoAlpha: 1,
          y: 0,
          duration: 0.35,
          stagger: 0.06,
          ease: 'power2.out'
        }, '-=0.15');
    });

    requestAnimationFrame(() => {
      if (active) ScrollTrigger.refresh();
    });

    if (typeof document !== 'undefined' && document.fonts) {
      document.fonts.ready.then(() => {
        if (active) ScrollTrigger.refresh();
      });
    }

    return () => {
      active = false;
      mm.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();
    const q = gsap.utils.selector(memoryRef);
    let active = true;

    const mm = gsap.matchMedia(memoryRef);

    // Desktop Layout >= 1024px
    mm.add("(min-width: 1024px)", () => {
      // Set initial states
      gsap.set(q('.memory-label'), { autoAlpha: 0, y: 18 });
      gsap.set(q('.memory-title-line'), { autoAlpha: 0, y: 26 });
      gsap.set(q('.memory-statement'), { autoAlpha: 0, y: 14 });
      gsap.set(q('.memory-desc'), { autoAlpha: 0, y: 14 });
      gsap.set(q('.memory-flow-label'), { autoAlpha: 0, y: 14 });
      gsap.set(q('.memory-sync-header'), { autoAlpha: 0, y: 14 });
      gsap.set(q('.memory-list-item'), { autoAlpha: 0, y: 14 });

      // Nodes & Connectors
      gsap.set(q('.memory-node-center'), { autoAlpha: 0, scale: 0.94, transformOrigin: 'center center' });
      
      const connectors = [
        '.memory-conn-risk',
        '.memory-conn-decision',
        '.memory-conn-deprecation',
        '.memory-conn-validation',
        '.memory-conn-owner',
        '.memory-conn-incident'
      ];
      connectors.forEach(conn => {
        gsap.set(q(conn), { autoAlpha: 0, attr: { x2: 260, y2: 190 } });
      });

      const nodes = [
        '.memory-node-risk',
        '.memory-node-decision',
        '.memory-node-deprecation',
        '.memory-node-validation',
        '.memory-node-owner',
        '.memory-node-incident'
      ];
      nodes.forEach(node => {
        gsap.set(q(node), { autoAlpha: 0, scale: 0.94, transformOrigin: 'center center' });
      });

      gsap.set(q('.memory-registry-success'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.memory-output-record'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.memory-workflow-label'), { autoAlpha: 0, y: 12 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: memoryRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      tl.to(q('.memory-label'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' })
        .to(q('.memory-title-line'), { autoAlpha: 1, y: 0, duration: 0.6, ease: 'power2.out', stagger: 0.1 }, '-=0.35')
        .to(q('.memory-statement'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.4')
        .to([q('.memory-desc'), q('.memory-sync-header'), q('.memory-list-item')], { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out', stagger: 0.08 }, '-=0.3')
        .to(q('.memory-flow-label'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.25')
        
        // Center node
        .to(q('.memory-node-center'), { autoAlpha: 1, scale: 1, duration: 0.5, ease: 'power2.out' }, '-=0.2')

        // Connector & Node Risk
        .to(q('.memory-conn-risk'), { autoAlpha: 1, attr: { x2: 110, y2: 90 }, duration: 0.4, ease: 'power2.out' }, '-=0.15')
        .to(q('.memory-node-risk'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.25')

        // Connector & Node Decision
        .to(q('.memory-conn-decision'), { autoAlpha: 1, attr: { x2: 110, y2: 190 }, duration: 0.4, ease: 'power2.out' }, '-=0.2')
        .to(q('.memory-node-decision'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.25')

        // Connector & Node Deprecation
        .to(q('.memory-conn-deprecation'), { autoAlpha: 1, attr: { x2: 110, y2: 290 }, duration: 0.4, ease: 'power2.out' }, '-=0.2')
        .to(q('.memory-node-deprecation'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.25')

        // Connector & Node Validation
        .to(q('.memory-conn-validation'), { autoAlpha: 1, attr: { x2: 410, y2: 90 }, duration: 0.4, ease: 'power2.out' }, '-=0.2')
        .to(q('.memory-node-validation'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.25')

        // Connector & Node Owner (Passive)
        .to(q('.memory-conn-owner'), { autoAlpha: 1, attr: { x2: 410, y2: 190 }, duration: 0.35, ease: 'power2.out' }, '-=0.2')
        .to(q('.memory-node-owner'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.25')

        // Connector & Node Incident (Passive)
        .to(q('.memory-conn-incident'), { autoAlpha: 1, attr: { x2: 410, y2: 290 }, duration: 0.35, ease: 'power2.out' }, '-=0.2')
        .to(q('.memory-node-incident'), { autoAlpha: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, '-=0.25')

        // Registry Success
        .to(q('.memory-registry-success'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.15')

        // Output records
        .to(q('.memory-output-record'), { autoAlpha: 1, y: 0, duration: 0.4, stagger: 0.08, ease: 'power2.out' }, '-=0.2')

        // Workflow example label
        .to(q('.memory-workflow-label'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.15');
    });

    // Mobile Layout < 1024px
    mm.add("(max-width: 1023px)", () => {
      // Set initial states (with max 8px translation)
      gsap.set(q('.memory-label'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.memory-title-line'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.memory-statement'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.memory-desc'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.memory-flow-label'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.memory-sync-header'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.memory-list-item'), { autoAlpha: 0, y: 6 });

      // Nodes & Connectors
      gsap.set(q('.memory-node-center'), { autoAlpha: 0, scale: 0.96, transformOrigin: 'center center' });
      
      const connectors = [
        '.memory-conn-risk',
        '.memory-conn-decision',
        '.memory-conn-deprecation',
        '.memory-conn-validation',
        '.memory-conn-owner',
        '.memory-conn-incident'
      ];
      connectors.forEach(conn => {
        gsap.set(q(conn), { autoAlpha: 0, attr: { x2: 260, y2: 190 } });
      });

      const nodes = [
        '.memory-node-risk',
        '.memory-node-decision',
        '.memory-node-deprecation',
        '.memory-node-validation',
        '.memory-node-owner',
        '.memory-node-incident'
      ];
      nodes.forEach(node => {
        gsap.set(q(node), { autoAlpha: 0, scale: 0.96, transformOrigin: 'center center' });
      });

      gsap.set(q('.memory-registry-success'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.memory-output-record'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.memory-workflow-label'), { autoAlpha: 0, y: 6 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: memoryRef.current,
          start: 'top 78%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      // Shorter durations and faster staggers on mobile
      tl.to(q('.memory-label'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' })
        .to(q('.memory-title-line'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out', stagger: 0.06 }, '-=0.25')
        .to(q('.memory-statement'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.3')
        .to([q('.memory-desc'), q('.memory-sync-header'), q('.memory-list-item')], { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out', stagger: 0.05 }, '-=0.25')
        .to(q('.memory-flow-label'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.2')
        
        // Center node
        .to(q('.memory-node-center'), { autoAlpha: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.15')

        // Connectors and Nodes (fast build-up on mobile so graph is not empty for long)
        .to(q('.memory-conn-risk'), { autoAlpha: 1, attr: { x2: 110, y2: 90 }, duration: 0.3, ease: 'power2.out' }, '-=0.1')
        .to(q('.memory-node-risk'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.2')

        .to(q('.memory-conn-decision'), { autoAlpha: 1, attr: { x2: 110, y2: 190 }, duration: 0.3, ease: 'power2.out' }, '-=0.15')
        .to(q('.memory-node-decision'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.2')

        .to(q('.memory-conn-deprecation'), { autoAlpha: 1, attr: { x2: 110, y2: 290 }, duration: 0.3, ease: 'power2.out' }, '-=0.15')
        .to(q('.memory-node-deprecation'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.2')

        .to(q('.memory-conn-validation'), { autoAlpha: 1, attr: { x2: 410, y2: 90 }, duration: 0.3, ease: 'power2.out' }, '-=0.15')
        .to(q('.memory-node-validation'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.2')

        .to(q('.memory-conn-owner'), { autoAlpha: 1, attr: { x2: 410, y2: 190 }, duration: 0.25, ease: 'power2.out' }, '-=0.15')
        .to(q('.memory-node-owner'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.2')

        .to(q('.memory-conn-incident'), { autoAlpha: 1, attr: { x2: 410, y2: 290 }, duration: 0.25, ease: 'power2.out' }, '-=0.15')
        .to(q('.memory-node-incident'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.2')

        // Registry Success
        .to(q('.memory-registry-success'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.1')

        // Output records (very fast stagger)
        .to(q('.memory-output-record'), { autoAlpha: 1, y: 0, duration: 0.3, stagger: 0.04, ease: 'power2.out' }, '-=0.15')

        // Workflow example label
        .to(q('.memory-workflow-label'), { autoAlpha: 1, y: 0, duration: 0.3, ease: 'power2.out' }, '-=0.1');
    });

    requestAnimationFrame(() => {
      if (active) ScrollTrigger.refresh();
    });

    if (typeof document !== 'undefined' && document.fonts) {
      document.fonts.ready.then(() => {
        if (active) ScrollTrigger.refresh();
      });
    }

    return () => {
      active = false;
      mm.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();
    const q = gsap.utils.selector(readyToShipRef);
    let active = true;

    const mm = gsap.matchMedia(readyToShipRef);

    // Desktop Layout >= 1024px
    mm.add("(min-width: 1024px)", () => {
      // Set initial states
      gsap.set(q('.ship-label'), { autoAlpha: 0, y: 16 });
      gsap.set(q('.ship-title-line'), { autoAlpha: 0, y: 28 });
      gsap.set(q('.ship-desc'), { autoAlpha: 0, y: 14 });

      // Lineage SVG elements
      gsap.set(q('.ship-node-1'), { autoAlpha: 0, scale: 0, transformOrigin: 'center center' });
      gsap.set(q('.ship-conn-1'), { autoAlpha: 0, attr: { x2: 16 } });
      gsap.set(q('.ship-node-2'), { autoAlpha: 0, scale: 0, transformOrigin: 'center center' });
      gsap.set(q('.ship-conn-2'), { autoAlpha: 0, attr: { x2: 56 } });
      gsap.set(q('.ship-node-3'), { autoAlpha: 0, scale: 0, transformOrigin: 'center center' });

      // CTA Buttons & Technical line
      gsap.set(q('.ship-cta-btn'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.ship-tech-line'), { autoAlpha: 0 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: readyToShipRef.current,
          start: 'top 82%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      tl.to(q('.ship-label'), { autoAlpha: 1, y: 0, duration: 0.45, ease: 'power2.out' })
        .to(q('.ship-title-line'), { autoAlpha: 1, y: 0, duration: 0.65, ease: 'power2.out', stagger: 0.1 }, '-=0.3')
        .to(q('.ship-desc'), { autoAlpha: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.4')
        
        // Lineage
        .to(q('.ship-node-1'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.25')
        .to(q('.ship-conn-1'), { autoAlpha: 1, attr: { x2: 48 }, duration: 0.35, ease: 'power2.out' }, '-=0.1')
        .to(q('.ship-node-2'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.15')
        .to(q('.ship-conn-2'), { autoAlpha: 1, attr: { x2: 84 }, duration: 0.35, ease: 'power2.out' }, '-=0.1')
        .to(q('.ship-node-3'), { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out' }, '-=0.15')

        // CTA Buttons
        .to(q('.ship-cta-btn'), { autoAlpha: 1, y: 0, duration: 0.5, stagger: 0.08, ease: 'power2.out' }, '-=0.2')

        // Technical line
        .to(q('.ship-tech-line'), { autoAlpha: 1, duration: 0.5, ease: 'power2.out' }, '-=0.25');
    });

    // Mobile Layout < 1024px
    mm.add("(max-width: 1023px)", () => {
      // Set initial states (translation max 8px)
      gsap.set(q('.ship-label'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.ship-title-line'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.ship-desc'), { autoAlpha: 0, y: 8 });

      // Lineage SVG elements
      gsap.set(q('.ship-node-1'), { autoAlpha: 0, scale: 0, transformOrigin: 'center center' });
      gsap.set(q('.ship-conn-1'), { autoAlpha: 0, attr: { x2: 16 } });
      gsap.set(q('.ship-node-2'), { autoAlpha: 0, scale: 0, transformOrigin: 'center center' });
      gsap.set(q('.ship-conn-2'), { autoAlpha: 0, attr: { x2: 56 } });
      gsap.set(q('.ship-node-3'), { autoAlpha: 0, scale: 0, transformOrigin: 'center center' });

      // CTA Buttons & Technical line
      gsap.set(q('.ship-cta-btn'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.ship-tech-line'), { autoAlpha: 0 });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: readyToShipRef.current,
          start: 'top 82%',
          toggleActions: 'play none none none',
          once: true,
        }
      });

      // Shorter durations, quicker transitions
      tl.to(q('.ship-label'), { autoAlpha: 1, y: 0, duration: 0.35, ease: 'power2.out' })
        .to(q('.ship-title-line'), { autoAlpha: 1, y: 0, duration: 0.45, ease: 'power2.out', stagger: 0.06 }, '-=0.25')
        .to(q('.ship-desc'), { autoAlpha: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.35')
        
        // Lineage
        .to(q('.ship-node-1'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.25')
        .to(q('.ship-conn-1'), { autoAlpha: 1, attr: { x2: 48 }, duration: 0.25, ease: 'power2.out' }, '-=0.1')
        .to(q('.ship-node-2'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.1')
        .to(q('.ship-conn-2'), { autoAlpha: 1, attr: { x2: 84 }, duration: 0.25, ease: 'power2.out' }, '-=0.1')
        .to(q('.ship-node-3'), { autoAlpha: 1, scale: 1, duration: 0.25, ease: 'power2.out' }, '-=0.1')

        // CTA Buttons
        .to(q('.ship-cta-btn'), { autoAlpha: 1, y: 0, duration: 0.4, stagger: 0.05, ease: 'power2.out' }, '-=0.15')

        // Technical line
        .to(q('.ship-tech-line'), { autoAlpha: 1, duration: 0.4, ease: 'power2.out' }, '-=0.2');
    });

    requestAnimationFrame(() => {
      if (active) ScrollTrigger.refresh();
    });

    if (typeof document !== 'undefined' && document.fonts) {
      document.fonts.ready.then(() => {
        if (active) ScrollTrigger.refresh();
      });
    }

    return () => {
      active = false;
      mm.revert();
    };
  }, [isReducedMotion]);

  return (
    <div className="w-full flex flex-col">
      {/* 1. HERO SECTION (Warm Paper Background) */}
      <section id="hero" ref={heroRef} className="relative flex items-center min-h-[calc(100vh-8rem)] py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full overflow-hidden select-none bg-[var(--color-riftless-paper)]">
        {/* Background Subtle Lines */}
        <div className="absolute inset-0 -z-10 opacity-30">
          <div className="absolute top-[20%] left-0 w-full h-[1px] bg-[var(--color-border)]" />
          <div className="absolute top-[60%] left-0 w-full h-[1px] bg-[var(--color-border)]" />
          <div className="absolute left-[30%] top-0 h-full w-[1px] bg-[var(--color-border)]" />
          <div className="absolute left-[70%] top-0 h-full w-[1px] bg-[var(--color-border)]" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center w-full z-10">
          {/* Left Column: Headline and Content (7 columns on large screens) */}
          <div className="lg:col-span-7 flex flex-col items-start text-left space-y-6 md:space-y-8">
            {/* Accent Label */}
            <div className="inline-flex items-center gap-2 hero-label">
              <span className="text-xs font-mono font-bold tracking-[0.25em] text-[var(--color-riftless-ink)] uppercase">
                [ RIFTLESS ]
              </span>
              <span className="w-1.5 h-1.5 bg-[var(--color-riftless-signal)] rounded-full animate-pulse" />
            </div>

            {/* Headline */}
            <div className="space-y-3 hero-headline">
              <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-display font-extrabold tracking-tighter uppercase text-[var(--color-riftless-ink)] leading-[0.95] sm:leading-[0.9]">
                Ship changes.
                <br />
                <span className="text-[var(--color-riftless-graph-gray)]">Not fallout.</span>
              </h1>
            </div>

            {/* Subtitle */}
            <p className="text-base sm:text-lg md:text-xl font-sans text-[var(--color-riftless-graph-gray)] max-w-xl leading-relaxed hero-sub">
              The context-aware agent that finds the blast radius,
              repairs breaking data changes, and validates every fix.
            </p>

            {/* Call to Actions (CTA) */}
            <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto hero-cta-container">
              <Link to="/demo" className="w-full sm:w-auto focus:outline-none group">
                <Button
                  id="hero-primary-cta"
                  variant="primary"
                  className="w-full sm:w-auto px-8 py-3 text-sm font-mono uppercase tracking-wider bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] hover:bg-slate-800 transition-all shadow-sm rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--color-riftless-ink)]"
                >
                  Run the Demo <span className="inline-block transition-transform duration-300 group-hover:translate-x-1.5 motion-reduce:transition-none">→</span>
                </Button>
              </Link>
              <Link to="/app/overview" className="w-full sm:w-auto focus:outline-none group">
                <Button
                  id="hero-secondary-cta"
                  variant="outline"
                  className="w-full sm:w-auto px-8 py-3 text-sm font-mono uppercase tracking-wider border-[var(--color-riftless-ink)] text-[var(--color-riftless-ink)] hover:bg-[var(--color-riftless-ink)] hover:text-[var(--color-riftless-paper)] transition-all rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--color-riftless-ink)]"
                >
                  Launch Console <span className="inline-block transition-transform duration-300 group-hover:translate-x-1.5 motion-reduce:transition-none">→</span>
                </Button>
              </Link>
            </div>

            {/* Supporting & Proof Lines */}
            <div className="w-full max-w-xl pt-6 md:pt-8 border-t border-[var(--color-border)] hero-proof">
              <p className="text-[11px] sm:text-xs font-mono text-[var(--color-riftless-graph-gray)] leading-relaxed uppercase tracking-wider">
                Powered by DataHub context. Reasoned with DeepSeek. Proven by executable validation.
              </p>
            </div>
          </div>

          {/* Right Column: Lineage Visualization (5 columns on large screens) */}
          <div className="lg:col-span-5 flex items-center justify-center relative w-full h-[320px] sm:h-[380px] lg:h-[450px] hero-lineage">
            {/* Elegant SVG Lineage Layout */}
            <svg
              id="hero-lineage-svg"
              viewBox="0 0 450 380"
              className="w-full h-full max-w-md lg:max-w-full drop-shadow-sm select-none"
              aria-hidden="true"
            >
              {/* Defs for markers or patterns */}
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 2 L 8 5 L 0 8 z" fill="var(--color-riftless-graph-gray)" />
                </marker>
                <marker
                  id="arrow-lime"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 2 L 8 5 L 0 8 z" fill="var(--color-riftless-signal)" />
                </marker>
              </defs>

              {/* Lineage Paths */}
              {/* Path 1: Broken/Fallout Lineage Path */}
              <g id="lineage-broken-group">
                {/* Healthy start */}
                <line
                  x1="80"
                  y1="100"
                  x2="180"
                  y2="100"
                  stroke="var(--color-riftless-graph-gray)"
                  strokeWidth="1.5"
                  strokeDasharray="4 2"
                  className="opacity-60"
                />
                {/* Broken gap connector */}
                <line
                  x1="220"
                  y1="100"
                  x2="280"
                  y2="150"
                  stroke="var(--color-riftless-critical)"
                  strokeWidth="2"
                  strokeDasharray="3 3"
                />
                {/* Cross symbol indicating broken pipe */}
                <g transform="translate(250, 125)">
                  <circle cx="0" cy="0" r="8" fill="var(--color-riftless-critical)" />
                  <path d="M -3 -3 L 3 3 M 3 -3 L -3 3" stroke="var(--color-riftless-paper)" strokeWidth="1.5" />
                </g>
                <line
                  x1="280"
                  y1="150"
                  x2="370"
                  y2="150"
                  stroke="var(--color-riftless-graph-gray)"
                  strokeWidth="1.5"
                  strokeDasharray="4 2"
                  className="opacity-40"
                />
              </g>

              {/* Path 2: Healthy Flow Path */}
              <g id="lineage-healthy-group">
                <line
                  x1="80"
                  y1="280"
                  x2="200"
                  y2="280"
                  stroke="var(--color-riftless-graph-gray)"
                  strokeWidth="1.5"
                  markerEnd="url(#arrow)"
                  className="opacity-70"
                />
                <line
                  x1="200"
                  y1="280"
                  x2="320"
                  y2="280"
                  stroke="var(--color-riftless-graph-gray)"
                  strokeWidth="1.5"
                  markerEnd="url(#arrow)"
                  className="opacity-40"
                />
              </g>

              {/* ONE LIME CONNECTOR: Riftless Intervention Path */}
              <g id="lineage-riftless-remediation">
                <path
                  d="M 200 100 Q 285 40 370 150"
                  fill="none"
                  stroke="var(--color-riftless-signal)"
                  strokeWidth="3.5"
                  markerEnd="url(#arrow-lime)"
                  strokeDasharray="500"
                  strokeDashoffset="0"
                  className="transition-all duration-1000"
                />
                {/* Glow trace dot on the lime connector */}
                <circle cx="282" cy="58" r="4.5" fill="var(--color-riftless-signal)" className="animate-ping" />
                <circle cx="282" cy="58" r="3.5" fill="var(--color-riftless-ink)" stroke="var(--color-riftless-signal)" strokeWidth="2" />
              </g>

              {/* Nodes Overlay */}
              {/* Top Row: Users Core pipeline */}
              <g id="node-users-raw" transform="translate(80, 100)">
                <circle cx="0" cy="0" r="16" fill="var(--color-riftless-ink)" stroke="var(--color-riftless-graph-gray)" strokeWidth="1.5" />
                <text x="0" y="28" fill="var(--color-riftless-ink)" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">USERS_RAW</text>
                <circle cx="0" cy="0" r="4" fill="var(--color-riftless-paper)" />
              </g>

              <g id="node-stg-users" transform="translate(200, 100)">
                <circle cx="0" cy="0" r="16" fill="var(--color-riftless-paper)" stroke="var(--color-riftless-ink)" strokeWidth="2" />
                <text x="0" y="-22" fill="var(--color-riftless-ink)" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">STG_USERS</text>
                <path d="M -5 0 L 5 0 M 0 -5 L 0 5" stroke="var(--color-riftless-ink)" strokeWidth="1.5" />
              </g>

              <g id="node-fct-active-users" transform="translate(370, 150)">
                <circle cx="0" cy="0" r="18" fill="var(--color-riftless-paper)" stroke="var(--color-riftless-ink)" strokeWidth="1.5" />
                <text x="0" y="30" fill="var(--color-riftless-ink)" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">ACTIVE_USERS</text>
                <rect x="-4" y="-4" width="8" height="8" fill="var(--color-riftless-ink)" />
              </g>

              {/* Bottom Row: Orders Core pipeline */}
              <g id="node-orders-raw" transform="translate(80, 280)">
                <circle cx="0" cy="0" r="14" fill="var(--color-riftless-paper)" stroke="var(--color-riftless-graph-gray)" strokeWidth="1.5" />
                <text x="0" y="26" fill="var(--color-riftless-graph-gray)" fontSize="9" fontFamily="monospace" textAnchor="middle">ORDERS_RAW</text>
                <circle cx="0" cy="0" r="3" fill="var(--color-riftless-graph-gray)" />
              </g>

              <g id="node-stg-orders" transform="translate(200, 280)">
                <circle cx="0" cy="0" r="14" fill="var(--color-riftless-paper)" stroke="var(--color-riftless-graph-gray)" strokeWidth="1.5" />
                <text x="0" y="-20" fill="var(--color-riftless-graph-gray)" fontSize="9" fontFamily="monospace" textAnchor="middle">STG_ORDERS</text>
                <circle cx="0" cy="0" r="3" fill="var(--color-riftless-graph-gray)" />
              </g>

              <g id="node-fct-revenue" transform="translate(320, 280)">
                <circle cx="0" cy="0" r="14" fill="var(--color-riftless-paper)" stroke="var(--color-riftless-graph-gray)" strokeWidth="1.5" />
                <text x="0" y="26" fill="var(--color-riftless-graph-gray)" fontSize="9" fontFamily="monospace" textAnchor="middle">FCT_REVENUE</text>
                <rect x="-3" y="-3" width="6" height="6" fill="var(--color-riftless-graph-gray)" />
              </g>

              {/* Floating Annotation Box */}
              <g id="remediation-badge" transform="translate(210, 20)">
                <rect x="0" y="0" width="130" height="22" rx="4" fill="var(--color-riftless-ink)" />
                <text x="65" y="14" fill="var(--color-riftless-signal)" fontSize="8" fontFamily="monospace" textAnchor="middle" fontWeight="bold">RIFTLESS REMEDIATION</text>
              </g>
            </svg>
          </div>
        </div>
      </section>

      {/* 2. PROBLEM STATEMENT SECTION (Riftless Ink Dark Background) */}
      <section id="problem" ref={problemRef} className="w-full bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] py-20 px-4 sm:px-6 lg:px-8 border-t border-[var(--color-riftless-ink)]">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 items-center">
          
          {/* Left/Top Content Column */}
          <div className="lg:col-span-5 flex flex-col items-start space-y-6 text-left">
            {/* Index Label */}
            <span className="text-xs font-mono font-bold tracking-[0.2em] text-[var(--color-riftless-muted)] uppercase problem-label">
              01 / THE PROBLEM
            </span>

            {/* Large Asymmetrical Headline */}
            <h2 className="text-3xl sm:text-5xl md:text-6xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-paper)] problem-headline problem-title">
              A SMALL CHANGE
              <br />
              <span className="text-[var(--color-riftless-critical)]">CAN BREAK</span>
              <br />
              THE ENTIRE GRAPH.
            </h2>

            {/* Editorial Supporting Paragraph */}
            <div className="space-y-4 max-w-lg text-sm sm:text-base font-sans text-[var(--color-riftless-muted)] leading-relaxed problem-sub problem-description">
              <p>
                A renamed field can silently break pipelines, dashboards,
                features, and production models across multiple teams.
              </p>
              <p className="font-semibold text-white">
                RIFTLESS sees the dependencies your code review cannot.
              </p>
            </div>
          </div>

          {/* Right/Bottom SVG Diagram Column */}
          <div className="lg:col-span-7 flex items-center justify-center relative w-full h-[340px] sm:h-[400px] lg:h-[460px] problem-graph-container problem-graph">
            {/* Custom precise dependency fallout SVG diagram */}
            <svg
              id="problem-graph-svg"
              viewBox="0 0 520 340"
              className="w-full h-full max-w-xl lg:max-w-full select-none"
              aria-hidden="true"
            >
              <defs>
                <marker
                  id="arrow-gray"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="5"
                  markerHeight="5"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 2 L 8 5 L 0 8 z" fill="#68707C" />
                </marker>
                <marker
                  id="arrow-red"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="5"
                  markerHeight="5"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 2 L 8 5 L 0 8 z" fill="var(--color-riftless-critical)" />
                </marker>
              </defs>

              {/* Lineage Connectors */}
              {/* Upstream to dbt Models */}
              <line className="prob-conn-normal" x1="75" y1="170" x2="235" y2="85" stroke="#4B5563" strokeWidth="1" markerEnd="url(#arrow-gray)" />
              <line className="prob-conn-normal" x1="75" y1="170" x2="235" y2="170" stroke="#4B5563" strokeWidth="1" markerEnd="url(#arrow-gray)" />
              
              {/* Red Critical Broken Line */}
              <path className="prob-conn-red-1" d="M 75 170 Q 155 220 235 255" fill="none" stroke="var(--color-riftless-critical)" strokeWidth="1.5" strokeDasharray="4 2" markerEnd="url(#arrow-red)" />
              
              {/* Middle Layer to Consumers */}
              <line className="prob-conn-normal" x1="235" y1="85" x2="410" y2="60" stroke="#4B5563" strokeWidth="1" markerEnd="url(#arrow-gray)" />
              <line className="prob-conn-normal" x1="235" y1="170" x2="410" y2="170" stroke="#4B5563" strokeWidth="1" markerEnd="url(#arrow-gray)" />
              
              {/* Red Critical Downstream Fallout Line */}
              <line className="prob-conn-red-2" x1="235" y1="255" x2="410" y2="280" stroke="var(--color-riftless-critical)" strokeWidth="1.5" strokeDasharray="3 3" markerEnd="url(#arrow-red)" />

              {/* Upstream Node (USERS.EMAIL) */}
              <g className="prob-node-root" transform="translate(75, 170)">
                <rect x="-60" y="-17" width="120" height="34" rx="4" fill="#1E293B" stroke="#68707C" strokeWidth="1.5" />
                <text x="0" y="5" fill="var(--color-riftless-paper)" fontSize="11" fontFamily="monospace" textAnchor="middle" fontWeight="bold">USERS.EMAIL</text>
                <text x="0" y="-24" fill="var(--color-riftless-critical)" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">RENAME FIELD ⚠️</text>
              </g>

              {/* Middle dbt nodes */}
              <g className="prob-node-mid-normal" transform="translate(235, 85)">
                <rect x="-52" y="-14" width="104" height="28" rx="3" fill="#1E293B" stroke="#4B5563" strokeWidth="1" />
                <text x="0" y="4" fill="#9CA3AF" fontSize="10" fontFamily="monospace" textAnchor="middle">stg_users.sql</text>
              </g>
              <g className="prob-node-mid-normal" transform="translate(235, 170)">
                <rect x="-52" y="-14" width="104" height="28" rx="3" fill="#1E293B" stroke="#4B5563" strokeWidth="1" />
                <text x="0" y="4" fill="#9CA3AF" fontSize="10" fontFamily="monospace" textAnchor="middle">fct_orders.sql</text>
              </g>
              <g className="prob-node-red-1" transform="translate(235, 255)">
                <rect x="-55" y="-14" width="110" height="28" rx="3" fill="#7F1D1D" stroke="var(--color-riftless-critical)" strokeWidth="1" />
                <text x="0" y="4" fill="var(--color-riftless-paper)" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">fct_user_cohorts</text>
                <text x="0" y="26" className="prob-label-red-1" fill="var(--color-riftless-critical)" fontSize="9.5" fontFamily="monospace" textAnchor="middle" fontWeight="bold">COMPILE ERROR</text>
              </g>

              {/* Consumers */}
              <g className="prob-node-end-normal" transform="translate(410, 60)">
                <rect x="-58" y="-14" width="116" height="28" rx="3" fill="#1E293B" stroke="#4B5563" strokeWidth="1" />
                <text x="0" y="4" fill="#9CA3AF" fontSize="10" fontFamily="monospace" textAnchor="middle">ML Feature Store</text>
              </g>
              <g className="prob-node-end-normal" transform="translate(410, 170)">
                <rect x="-58" y="-14" width="116" height="28" rx="3" fill="#1E293B" stroke="#4B5563" strokeWidth="1" />
                <text x="0" y="4" fill="#9CA3AF" fontSize="10" fontFamily="monospace" textAnchor="middle">Finance Report</text>
              </g>
              <g className="prob-node-red-2" transform="translate(410, 280)">
                <rect x="-58" y="-14" width="116" height="28" rx="3" fill="#7F1D1D" stroke="var(--color-riftless-critical)" strokeWidth="1" />
                <text x="0" y="4" fill="var(--color-riftless-paper)" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">Exec KPI Dash</text>
                <text x="0" y="26" className="prob-label-red-2" fill="var(--color-riftless-critical)" fontSize="9.5" fontFamily="monospace" textAnchor="middle" fontWeight="bold">BROKEN CHART</text>
              </g>
            </svg>
          </div>

        </div>
      </section>

      {/* 3. HOW RIFTLESS WORKS SECTION (02 / THE SYSTEM) */}
      <section id="system" ref={systemRef} className="w-full bg-[var(--color-riftless-paper)] text-[var(--color-riftless-ink)] py-24 px-4 sm:px-6 lg:px-8 border-t border-[var(--color-border)] select-none overflow-hidden">
        <div className="max-w-7xl mx-auto space-y-16">
          
          {/* Section Header: Label, Headline, and Supporting Copy */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-6 flex flex-col items-start space-y-6">
              {/* Index Label */}
              <span className="text-xs font-mono font-bold tracking-[0.2em] text-[var(--color-riftless-graph-gray)] uppercase system-label">
                02 / THE SYSTEM
              </span>

              {/* Headline */}
              <h2 className="text-4xl sm:text-6xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-ink)]">
                <span className="block system-word-1">CONTEXT.</span>
                <span className="block system-word-2">DECISION.</span>
                <span className="block system-word-3">REPAIR.</span>
                <span className="block system-word-4">PROOF.</span>
              </h2>
            </div>

            <div className="lg:col-span-6 lg:pt-10">
              <p className="text-lg sm:text-xl font-sans text-[var(--color-riftless-graph-gray)] max-w-xl leading-relaxed system-sub">
                RIFTLESS reads the real data graph before it reviews a change.
                Every decision is grounded, every repair is generated, and every result is validated.
              </p>
            </div>
          </div>

          {/* Continuous Lineage Flow Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-12 lg:gap-8 pt-8 relative">
            
            {/* Step 1 */}
            <div className="relative flex flex-col items-center text-center group">
              {/* Connecting Line (Desktop: Right, Mobile: Down) */}
              <div className="sys-conn-1 sys-conn-desktop absolute top-2.5 left-1/2 w-full h-[1.5px] bg-slate-300/60 hidden lg:block -z-0 origin-left" />
              <div className="sys-conn-1 sys-conn-mobile absolute top-2.5 left-1/2 -translate-x-1/2 w-[1.5px] h-full bg-slate-300/60 lg:hidden -z-0 origin-top" />
              
              {/* Node Dot */}
              <div className="sys-dot-1 w-5 h-5 rounded-full border-2 border-[var(--color-riftless-ink)] bg-[var(--color-riftless-paper)] z-10 flex items-center justify-center relative mb-6">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-riftless-ink)]" />
              </div>

              {/* Large Number & Technical Label */}
              <div className="sys-content-1 space-y-2 relative z-10 px-4">
                <span className="block text-5xl font-display font-extrabold tracking-tighter text-[var(--color-riftless-graph-gray)] opacity-40">
                  01
                </span>
                <span className="block text-xs font-mono font-bold tracking-widest text-[var(--color-riftless-ink)] uppercase">
                  CONTEXT
                </span>
                <p className="text-sm font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed pt-2 max-w-xs mx-auto">
                  Read schemas, lineage, ownership, quality, and ML metadata from DataHub.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative flex flex-col items-center text-center group">
              {/* Connecting Line (Desktop: Right, Mobile: Down) */}
              <div className="sys-conn-2 sys-conn-desktop absolute top-2.5 left-1/2 w-full h-[1.5px] bg-slate-300/60 hidden lg:block -z-0 origin-left" />
              <div className="sys-conn-2 sys-conn-mobile absolute top-2.5 left-1/2 -translate-x-1/2 w-[1.5px] h-full bg-slate-300/60 lg:hidden -z-0 origin-top" />

              {/* Node Dot */}
              <div className="sys-dot-2 w-5 h-5 rounded-full border-2 border-[var(--color-riftless-ink)] bg-[var(--color-riftless-paper)] z-10 flex items-center justify-center relative mb-6">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-riftless-ink)]" />
              </div>

              {/* Large Number & Technical Label */}
              <div className="sys-content-2 space-y-2 relative z-10 px-4">
                <span className="block text-5xl font-display font-extrabold tracking-tighter text-[var(--color-riftless-graph-gray)] opacity-40">
                  02
                </span>
                <span className="block text-xs font-mono font-bold tracking-widest text-[var(--color-riftless-ink)] uppercase">
                  DECISION
                </span>
                <p className="text-sm font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed pt-2 max-w-xs mx-auto">
                  Calculate deterministic risk and decide whether to allow, warn, or block.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative flex flex-col items-center text-center group">
              {/* Connecting Line (Desktop: Right, Mobile: Down) - LIME GREEN final connector */}
              <div className="sys-conn-3 sys-conn-desktop absolute top-2.5 left-1/2 w-full h-[2.5px] bg-[var(--color-riftless-signal)] hidden lg:block -z-0 origin-left" />
              <div className="sys-conn-3 sys-conn-mobile absolute top-2.5 left-1/2 -translate-x-1/2 w-[2.5px] h-full bg-[var(--color-riftless-signal)] lg:hidden -z-0 origin-top" />

              {/* Node Dot */}
              <div className="sys-dot-3 w-5 h-5 rounded-full border-2 border-[var(--color-riftless-ink)] bg-[var(--color-riftless-paper)] z-10 flex items-center justify-center relative mb-6">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-riftless-ink)]" />
              </div>

              {/* Large Number & Technical Label */}
              <div className="sys-content-3 space-y-2 relative z-10 px-4">
                <span className="block text-5xl font-display font-extrabold tracking-tighter text-[var(--color-riftless-graph-gray)] opacity-40">
                  03
                </span>
                <span className="block text-xs font-mono font-bold tracking-widest text-[var(--color-riftless-ink)] uppercase">
                  REPAIR
                </span>
                <p className="text-sm font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed pt-2 max-w-xs mx-auto">
                  Use DeepSeek to generate compatibility code, tests, rollback, and documentation.
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="relative flex flex-col items-center text-center group">
              {/* No line extending right or down */}

              {/* Node Dot with Lime Accents */}
              <div className="sys-dot-4 w-5 h-5 rounded-full border-2 border-[var(--color-riftless-signal)] bg-[var(--color-riftless-ink)] z-10 flex items-center justify-center relative mb-6">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-riftless-signal)]" />
              </div>

              {/* Large Number & Technical Label */}
              <div className="sys-content-4 space-y-2 relative z-10 px-4">
                <span className="block text-5xl font-display font-extrabold tracking-tighter text-[var(--color-riftless-signal)]">
                  04
                </span>
                <span className="block text-xs font-mono font-bold tracking-widest text-[var(--color-riftless-ink)] uppercase">
                  PROOF
                </span>
                <p className="text-sm font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed pt-2 max-w-xs mx-auto">
                  Execute SQL, compile dbt, run tests, and write the verified decision back.
                </p>
              </div>
            </div>

          </div>

          {/* Dynamic Small Flow Output Indicator Footer */}
          <div className="pt-12 border-t border-[var(--color-border)] flex justify-center system-output-strip">
            <div className="inline-flex flex-wrap items-center justify-center gap-2 sm:gap-4 px-6 py-3 bg-[var(--color-riftless-ink)] rounded text-xs font-mono uppercase tracking-wider text-[var(--color-riftless-paper)] shadow-sm">
              <span className="text-[var(--color-riftless-muted)]">DATAHUB CONTEXT</span>
              <span className="text-[var(--color-riftless-graph-gray)]">→</span>
              <span className="text-[var(--color-riftless-warning)]">RISK DECISION</span>
              <span className="text-[var(--color-riftless-graph-gray)]">→</span>
              <span className="text-[var(--color-riftless-signal)]">GENERATED PATCH</span>
              <span className="text-[var(--color-riftless-graph-gray)]">→</span>
              <span className="text-white font-bold">VALIDATED CHANGE</span>
            </div>
          </div>

        </div>
      </section>

      {/* 4. THE CONTEXT LAYER SECTION (03 / THE CONTEXT LAYER) */}
      <section id="context-layer" ref={contextRef} className="w-full bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] py-24 px-4 sm:px-6 lg:px-8 border-t border-[var(--color-border)] select-none overflow-hidden">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          
          {/* Left Column: Headline and Supporting Copy */}
          <div className="lg:col-span-5 flex flex-col items-start space-y-6 text-left">
            {/* Index Label */}
            <span className="text-xs font-mono font-bold tracking-[0.2em] text-[var(--color-riftless-muted)] uppercase context-label">
              03 / THE CONTEXT LAYER
            </span>

            {/* Headline */}
            <h2 className="text-3xl sm:text-5xl md:text-6xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-paper)]">
              <span className="block context-line-1">
                CODE SHOWS
                <br />
                THE CHANGE.
              </span>
              <br />
              <span className="block context-line-2">
                <span className="text-[var(--color-riftless-graph-gray)]">DATAHUB SHOWS</span>
                <br />
                WHAT IT CAN BREAK.
              </span>
            </h2>

            {/* Small Label for Context Graph */}
            <span className="text-xs font-mono text-[var(--color-riftless-signal)] uppercase tracking-wider bg-slate-900/40 px-2.5 py-1 rounded context-badge">
              DATAHUB AS THE CONTEXT GRAPH
            </span>

            {/* Supporting Copy */}
            <div className="space-y-4 max-w-lg text-sm sm:text-base font-sans text-[var(--color-riftless-muted)] leading-relaxed context-desc">
              <p>
                RIFTLESS reads the metadata your pull request cannot see:
                schemas, column lineage, ownership, governance, quality signals,
                query usage, and production ML dependencies.
              </p>
              <p className="font-semibold text-white">
                Without context, an agent guesses. With DataHub, it acts with evidence.
              </p>
            </div>
          </div>

          {/* Right Column: Radial Context Graph SVG */}
          <div className="lg:col-span-7 flex items-center justify-center relative w-full h-[360px] sm:h-[420px]">
            <svg
              id="context-graph-svg"
              viewBox="0 0 520 380"
              className="w-full h-full max-w-lg lg:max-w-full select-none"
              aria-hidden="true"
            >
              {/* Lineage Connectors / Radial connections */}
              {/* Inactive connections (Restrained gray) */}
              <line className="context-conn-query" x1="260" y1="190" x2="260" y2="60" stroke="#4B5563" strokeWidth="1" />
              <line className="context-conn-governance" x1="260" y1="190" x2="100" y2="110" stroke="#4B5563" strokeWidth="1" />
              <line className="context-conn-ownership" x1="260" y1="190" x2="80" y2="190" stroke="#4B5563" strokeWidth="1" />
              <line className="context-conn-quality" x1="260" y1="190" x2="100" y2="270" stroke="#4B5563" strokeWidth="1" />

              {/* Active Connections (Signal Lime) */}
              <line className="context-conn-schema" x1="260" y1="190" x2="420" y2="110" stroke="var(--color-riftless-signal)" strokeWidth="1.5" strokeDasharray="3 2" />
              <line className="context-conn-lineage" x1="260" y1="190" x2="440" y2="190" stroke="var(--color-riftless-signal)" strokeWidth="1.5" strokeDasharray="3 2" />
              <line className="context-conn-ml" x1="260" y1="190" x2="420" y2="270" stroke="var(--color-riftless-signal)" strokeWidth="1.5" strokeDasharray="3 2" />

              {/* Surrounding Nodes (In background order) */}
              
              {/* 1. QUERY USAGE */}
              <g className="context-node-query" transform="translate(260, 60)">
                <rect x="-55" y="-14" width="110" height="28" rx="3" fill="#11181B" stroke="#4B5563" strokeWidth="1" />
                <text x="0" y="4" fill="#9CA3AF" fontSize="9.5" fontFamily="monospace" textAnchor="middle">QUERY USAGE</text>
              </g>

              {/* 2. GOVERNANCE */}
              <g className="context-node-governance" transform="translate(100, 110)">
                <rect x="-55" y="-14" width="110" height="28" rx="3" fill="#11181B" stroke="#4B5563" strokeWidth="1" />
                <text x="0" y="4" fill="#9CA3AF" fontSize="9.5" fontFamily="monospace" textAnchor="middle">GOVERNANCE</text>
              </g>

              {/* 3. OWNERSHIP */}
              <g className="context-node-ownership" transform="translate(80, 190)">
                <rect x="-55" y="-14" width="110" height="28" rx="3" fill="#11181B" stroke="#4B5563" strokeWidth="1" />
                <text x="0" y="4" fill="#9CA3AF" fontSize="9.5" fontFamily="monospace" textAnchor="middle">OWNERSHIP</text>
              </g>

              {/* 4. QUALITY */}
              <g className="context-node-quality" transform="translate(100, 270)">
                <rect x="-55" y="-14" width="110" height="28" rx="3" fill="#11181B" stroke="#4B5563" strokeWidth="1" />
                <text x="0" y="4" fill="#9CA3AF" fontSize="9.5" fontFamily="monospace" textAnchor="middle">QUALITY</text>
              </g>

              {/* 5. SCHEMA (Active!) */}
              <g className="context-node-schema" transform="translate(420, 110)">
                <rect x="-55" y="-14" width="110" height="28" rx="3" fill="#13241C" stroke="var(--color-riftless-signal)" strokeWidth="1" />
                <text x="0" y="4" fill="var(--color-riftless-signal)" fontSize="9.5" fontFamily="monospace" textAnchor="middle" fontWeight="bold">SCHEMA</text>
              </g>

              {/* 6. COLUMN LINEAGE (Active!) */}
              <g className="context-node-lineage" transform="translate(440, 190)">
                <rect x="-65" y="-14" width="130" height="28" rx="3" fill="#13241C" stroke="var(--color-riftless-signal)" strokeWidth="1" />
                <text x="0" y="4" fill="var(--color-riftless-signal)" fontSize="9.5" fontFamily="monospace" textAnchor="middle" fontWeight="bold">COLUMN LINEAGE</text>
              </g>

              {/* 7. ML DEPENDENCIES (Active!) */}
              <g className="context-node-ml" transform="translate(420, 270)">
                <rect x="-65" y="-14" width="130" height="28" rx="3" fill="#13241C" stroke="var(--color-riftless-signal)" strokeWidth="1" />
                <text x="0" y="4" fill="var(--color-riftless-signal)" fontSize="9.5" fontFamily="monospace" textAnchor="middle" fontWeight="bold">ML DEPENDENCIES</text>
              </g>

              {/* Central Node (PROPOSED CHANGE) */}
              <g className="context-node-center" transform="translate(260, 190)">
                <rect x="-75" y="-18" width="150" height="36" rx="18" fill="var(--color-riftless-ink)" stroke="var(--color-riftless-paper)" strokeWidth="1.5" />
                <text x="0" y="5" fill="var(--color-riftless-paper)" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">PROPOSED CHANGE</text>
              </g>

              {/* Output small badge bottom center */}
              <g className="context-output-badge" transform="translate(260, 350)">
                <rect x="-165" y="-12" width="330" height="24" rx="4" fill="var(--color-riftless-ink)" stroke="var(--color-border)" strokeWidth="1" />
                <text x="0" y="4" fill="var(--color-riftless-muted)" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
                  CONTEXT PACK <tspan fill="var(--color-riftless-signal)">→</tspan> EVIDENCE <tspan fill="var(--color-riftless-signal)">→</tspan> GROUNDED DECISION
                </text>
              </g>
            </svg>
          </div>

        </div>
      </section>

      {/* 5. REMEDIATION & VALIDATION SECTION (04 / THE REPAIR) */}
      <section id="repair" ref={repairRef} className="w-full bg-[var(--color-riftless-paper)] text-[var(--color-riftless-ink)] py-24 px-4 sm:px-6 lg:px-8 border-t border-[var(--color-border)] select-none overflow-hidden">
        <div className="max-w-7xl mx-auto space-y-16">
          
          {/* Section Header: Label, Headline, and Supporting Copy */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-6 flex flex-col items-start space-y-6">
              {/* Index Label */}
              <span className="text-xs font-mono font-bold tracking-[0.2em] text-[var(--color-riftless-graph-gray)] uppercase repair-label">
                04 / THE REPAIR
              </span>

              {/* Headline */}
              <h2 className="text-4xl sm:text-6xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-ink)]">
                <span className="block repair-title-1">FROM BREAKING CHANGE</span>
                <br />
                <span className="block repair-title-2 text-[var(--color-riftless-graph-gray)]">TO VERIFIED FIX.</span>
              </h2>
            </div>

            <div className="lg:col-span-6 lg:pt-10">
              <p className="text-lg sm:text-xl font-sans text-[var(--color-riftless-graph-gray)] max-w-xl leading-relaxed repair-desc">
                RIFTLESS does not stop at warning you.
                It generates a backward-compatible repair, then proves that the repair works.
              </p>
            </div>
          </div>

          {/* Flow Connection Header / Flowchart Labels */}
          <div className="flex items-center justify-center py-2 bg-slate-100 rounded border border-slate-200/60 max-w-xl mx-auto repair-flow-label">
            <div className="flex items-center gap-2 sm:gap-4 font-mono text-[10px] sm:text-xs uppercase tracking-widest text-[var(--color-riftless-graph-gray)]">
              <span className="text-[var(--color-riftless-critical)] font-bold">CHANGE</span>
              <span className="text-slate-400">━━━━▶</span>
              <span className="text-[var(--color-riftless-signal)] font-bold bg-slate-900 text-white px-2 py-0.5 rounded text-[9px] sm:text-[10px]">REPAIR</span>
              <span className="text-slate-400">━━━━▶</span>
              <span className="text-emerald-600 font-bold">VALIDATED</span>
            </div>
          </div>

          {/* Continuous Code/Diff Flow Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-stretch relative">
            
            {/* SISI KIRI: PROPOSED CHANGE */}
            <div className="lg:col-span-5 flex flex-col justify-between p-6 sm:p-8 bg-[#11181B] text-[var(--color-riftless-paper)] rounded border border-slate-800 relative shadow-sm repair-panel-change">
              <div className="space-y-6">
                {/* Top Headers */}
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[var(--color-riftless-critical)]" />
                    <span className="text-[11px] font-mono tracking-wider text-[var(--color-riftless-muted)] uppercase">
                      PROPOSED CHANGE
                    </span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-[var(--color-riftless-critical)] uppercase tracking-wider px-2.5 py-1 bg-red-950/40 border border-red-900/60 rounded repair-risk-badge">
                    RISK: BLOCKED
                  </span>
                </div>

                {/* Diff Code Snippet */}
                <div className="space-y-3 font-mono text-xs sm:text-sm bg-[#0B0F11] p-4 rounded border border-slate-900 overflow-x-auto">
                  <div className="text-slate-500 text-[10px] sm:text-xs">// staging/stg_users.sql</div>
                  <div className="text-slate-400">SELECT</div>
                  <div className="bg-red-950/50 text-red-400 px-2.5 py-1 rounded flex items-center gap-2 repair-diff-line">
                    <span className="font-bold select-none text-red-500">-</span>
                    <span>customer_id</span>
                  </div>
                  <div className="bg-emerald-950/10 text-emerald-500/50 px-2.5 py-1 rounded flex items-center gap-2 opacity-30 select-none">
                    <span className="font-bold">-</span>
                    <span>customer_key</span>
                  </div>
                  <div className="text-slate-400">FROM production.users;</div>
                </div>
              </div>

              {/* Bottom blast metadata info */}
              <div className="pt-6 mt-8 border-t border-slate-800/60 flex items-center justify-between text-xs font-mono repair-blast-info">
                <span className="text-[var(--color-riftless-muted)] uppercase">BLAST RADIUS</span>
                <span className="text-[var(--color-riftless-critical)] font-bold">EXAMPLE BLAST RADIUS</span>
              </div>

              {/* Connecting line to right block (visible on desktop) - two solid lines with a central connector dot */}
              <div className="absolute top-1/2 -right-8 w-8 h-[6px] -translate-y-1/2 hidden lg:flex items-center justify-between z-10 select-none pointer-events-none">
                <div className="w-[13px] h-[1.5px] bg-[var(--color-riftless-critical)] repair-connector-left" />
                <div className="w-[4px] h-[4px] rounded-full bg-slate-500 repair-connector-dot" />
                <div className="w-[13px] h-[1.5px] bg-[var(--color-riftless-signal)] repair-connector-right" />
              </div>
            </div>

            {/* SISI KANAN: GENERATED REMEDIATION & VALIDATION */}
            <div className="lg:col-span-7 flex flex-col justify-between p-6 sm:p-8 bg-[#11181B] text-[var(--color-riftless-paper)] rounded border border-slate-800 relative shadow-sm repair-panel-remediation">
              <div className="space-y-6">
                
                {/* Top Headers */}
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[var(--color-riftless-signal)] animate-pulse" />
                    <span className="text-[11px] font-mono tracking-wider text-[var(--color-riftless-signal)] uppercase font-bold">
                      GENERATED REMEDIATION
                    </span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-[var(--color-riftless-signal)] uppercase tracking-wider px-2.5 py-1 bg-emerald-950/40 border border-emerald-900/60 rounded repair-active-badge">
                    REPAIR ACTIVE
                  </span>
                </div>

                {/* Remediation layout block: code and artifacts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Generated Code */}
                  <div className="font-mono text-xs sm:text-sm space-y-3 bg-[#0B0F11] p-4 rounded border border-slate-900 overflow-x-auto flex flex-col justify-between">
                    <div>
                      <div className="text-[var(--color-riftless-signal)] font-semibold mb-2 text-[10px] tracking-wider uppercase">
                        // GENERATED REPAIR
                      </div>
                      <div className="text-slate-400">SELECT</div>
                      <div className="bg-emerald-950/50 text-[var(--color-riftless-signal)] px-2.5 py-1.5 rounded flex items-center gap-2 font-bold border border-emerald-900/50 repair-patch-line">
                        <span className="font-bold select-none text-[var(--color-riftless-signal)]">+</span>
                        <span>customer_key AS customer_id</span>
                      </div>
                      <div className="text-slate-400">FROM production.users;</div>
                    </div>
                    <div className="text-[9px] text-slate-500 pt-3 border-t border-slate-900/60 mt-3 uppercase tracking-wide">
                      *ALIASED FOR BACKWARD COMPATIBILITY
                    </div>
                  </div>

                  {/* Generated Artifacts list */}
                  <div className="bg-[#0B0F11] p-4 rounded border border-slate-900 flex flex-col justify-between">
                    <span className="block text-[10px] font-mono tracking-wider text-[var(--color-riftless-muted)] uppercase mb-3">
                      GENERATED ARTIFACTS
                    </span>
                    
                    <ul className="space-y-2 font-mono text-[11px] text-[var(--color-riftless-muted)]">
                      <li className="flex items-center gap-2 text-[var(--color-riftless-paper)] repair-artifact-item">
                        <span className="text-[var(--color-riftless-signal)] font-bold">✔</span>
                        <span>COMPATIBILITY SQL</span>
                      </li>
                      <li className="flex items-center gap-2 text-[var(--color-riftless-paper)] repair-artifact-item">
                        <span className="text-[var(--color-riftless-signal)] font-bold">✔</span>
                        <span>DBT TESTS</span>
                      </li>
                      <li className="flex items-center gap-2 text-[var(--color-riftless-paper)] repair-artifact-item">
                        <span className="text-[var(--color-riftless-signal)] font-bold">✔</span>
                        <span>ROLLBACK PLAN</span>
                      </li>
                      <li className="flex items-center gap-2 text-[var(--color-riftless-paper)] repair-artifact-item">
                        <span className="text-[var(--color-riftless-signal)] font-bold">✔</span>
                        <span>DEPRECATION DOCS</span>
                      </li>
                    </ul>

                    <div className="pt-3 mt-3 border-t border-slate-900/60 text-[9px] text-[var(--color-riftless-signal)] uppercase font-semibold">
                      COMPATIBILITY LAYER ACTIVE
                    </div>
                  </div>

                </div>

                {/* Validation Sequence Section */}
                <div className="pt-6 border-t border-slate-800/80">
                  <span className="block text-[11px] font-mono tracking-widest text-[var(--color-riftless-muted)] uppercase mb-4">
                    VALIDATION SEQUENCE
                  </span>

                  {/* Validation steps grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-[10px] sm:text-[11px]">
                    
                    <div className="p-3 bg-[#0B0F11] rounded border border-slate-900/80 flex items-center justify-between repair-val-1">
                      <span className="text-slate-400">SQL PARSE</span>
                      <span className="text-[var(--color-riftless-signal)] font-bold">PASSED</span>
                    </div>

                    <div className="p-3 bg-[#0B0F11] rounded border border-slate-900/80 flex items-center justify-between repair-val-2">
                      <span className="text-slate-400">DUCKDB EXECUTION</span>
                      <span className="text-[var(--color-riftless-signal)] font-bold">PASSED</span>
                    </div>

                    <div className="p-3 bg-[#0B0F11] rounded border border-slate-900/80 flex items-center justify-between repair-val-3">
                      <span className="text-slate-400">DBT COMPILE</span>
                      <span className="text-[var(--color-riftless-signal)] font-bold">PASSED</span>
                    </div>

                    <div className="p-3 bg-[#0B0F11] rounded border border-slate-900/80 flex items-center justify-between repair-val-4">
                      <span className="text-slate-400">DBT TEST</span>
                      <span className="text-[var(--color-riftless-signal)] font-bold">PASSED</span>
                    </div>

                  </div>
                </div>

              </div>
            </div>

          </div>

        </div>
      </section>

      {/* 6. DATAHUB WRITEBACK SECTION (05 / THE MEMORY) */}
      <section id="memory" ref={memoryRef} className="w-full bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] py-24 px-4 sm:px-6 lg:px-8 border-t border-slate-800/80 select-none overflow-hidden">
        <div className="max-w-7xl mx-auto space-y-16">
          
          {/* Section Header */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
            <div className="lg:col-span-5 flex flex-col items-start space-y-6">
              {/* Index Label */}
              <span className="text-xs font-mono font-bold tracking-[0.2em] text-[var(--color-riftless-muted)] uppercase memory-label">
                05 / THE MEMORY
              </span>

              {/* Headline */}
              <h2 className="text-3xl sm:text-5xl md:text-6xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-paper)]">
                <span className="block memory-title-line">THE FIX SHOULD NOT</span>
                <span className="block memory-title-line">DISAPPEAR INSIDE</span>
                <span className="block memory-title-line">A PULL REQUEST.</span>
              </h2>

              {/* Small workflow step statement */}
              <div className="text-[10px] sm:text-xs font-mono tracking-[0.2em] text-[var(--color-riftless-signal)] uppercase bg-slate-900/80 px-3 py-1.5 rounded inline-block border border-slate-800/60 memory-statement">
                READ CONTEXT. ACT. WRITE KNOWLEDGE BACK.
              </div>
            </div>

            <div className="lg:col-span-7 lg:pt-10 space-y-6">
              <p className="text-lg sm:text-xl font-sans text-[var(--color-riftless-muted)] max-w-xl leading-relaxed memory-desc">
                After every review, RIFTLESS writes the decision back to DataHub
                so the next engineer or agent inherits the context.
              </p>
              <p className="text-base font-sans text-white font-semibold memory-desc">
                The graph becomes smarter with every change.
              </p>
            </div>
          </div>

          {/* Sequential Flow Indicator Header */}
          <div className="memory-flow-label flex items-center justify-center py-2.5 bg-slate-900/60 rounded border border-slate-800/60 max-w-xl mx-auto">
            <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 font-mono text-[9px] sm:text-[11px] uppercase tracking-widest text-slate-500">
              <span>VALIDATED CHANGE</span>
              <span>━━━━▶</span>
              <span className="text-[var(--color-riftless-signal)] font-bold">DATAHUB WRITEBACK</span>
              <span>━━━━▶</span>
              <span className="text-white">SHARED ORGANIZATIONAL CONTEXT</span>
            </div>
          </div>

          {/* Two-Column Editorial Grid: Visual Metadata Graph on Right, Context Details on Left */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
            
            {/* Left Column: List/Explanations of Metadata Written Back */}
            <div className="lg:col-span-5 space-y-6 text-left">
              <span className="text-xs font-mono text-slate-400 uppercase tracking-widest block border-b border-slate-800 pb-2 memory-sync-header">
                ACTIVE METADATA SYNCING
              </span>

              <div className="space-y-4 font-mono text-xs sm:text-sm">
                <div className="flex items-start gap-3 p-3 bg-slate-900/40 rounded border border-slate-800/40 memory-list-item">
                  <span className="text-[var(--color-riftless-signal)] font-bold">●</span>
                  <div>
                    <span className="text-white font-bold block">RISK SCORE & TAGS</span>
                    <span className="text-slate-400 text-xs">Flag dataset vulnerability metrics and dependency depth.</span>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-slate-900/40 rounded border border-slate-800/40 memory-list-item">
                  <span className="text-[var(--color-riftless-signal)] font-bold">●</span>
                  <div>
                    <span className="text-white font-bold block">DECISION DOCUMENTS</span>
                    <span className="text-slate-400 text-xs">Link reviews, agent thought traces, and repair paths permanently.</span>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-slate-900/40 rounded border border-slate-800/40 memory-list-item">
                  <span className="text-slate-400 font-bold">●</span>
                  <div>
                    <span className="text-slate-400 font-bold block">DEPRECATION NOTES & OWNER ACTIONS</span>
                    <span className="text-slate-500 text-xs">Notify dataset owners and populate migration plans.</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Structured Metadata Graph SVG */}
            <div className="lg:col-span-7 flex items-center justify-center relative w-full h-[360px] sm:h-[420px]">
              <svg
                id="writeback-graph-svg"
                viewBox="0 0 520 380"
                className="w-full h-full max-w-lg lg:max-w-full select-none"
                aria-hidden="true"
              >
                {/* Thin Lineage Connectors to Central Asset */}
                {/* Active connectors (Signal Lime) */}
                <line className="memory-conn-risk" x1="260" y1="190" x2="110" y2="90" stroke="var(--color-riftless-signal)" strokeWidth="1.2" strokeDasharray="3 2" />
                <line className="memory-conn-decision" x1="260" y1="190" x2="110" y2="190" stroke="var(--color-riftless-signal)" strokeWidth="1.2" strokeDasharray="3 2" />
                <line className="memory-conn-deprecation" x1="260" y1="190" x2="110" y2="290" stroke="var(--color-riftless-signal)" strokeWidth="1.2" strokeDasharray="3 2" />
                
                <line className="memory-conn-validation" x1="260" y1="190" x2="410" y2="90" stroke="var(--color-riftless-signal)" strokeWidth="1.2" strokeDasharray="3 2" />
                
                {/* Inactive or regular info connectors (restrained gray) */}
                <line className="memory-conn-owner" x1="260" y1="190" x2="410" y2="190" stroke="#4B5563" strokeWidth="1" />
                <line className="memory-conn-incident" x1="260" y1="190" x2="410" y2="290" stroke="#4B5563" strokeWidth="1" />

                {/* Left Column Surrounding Nodes */}
                {/* 1. RISK TAG (Active) */}
                <g className="memory-node-risk" transform="translate(110, 90)">
                  <rect x="-60" y="-14" width="120" height="28" rx="3" fill="#13241C" stroke="var(--color-riftless-signal)" strokeWidth="1.2" />
                  <text x="0" y="4" fill="var(--color-riftless-signal)" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">RISK TAG</text>
                </g>

                {/* 2. DECISION DOCUMENT (Active) */}
                <g className="memory-node-decision" transform="translate(110, 190)">
                  <rect x="-65" y="-14" width="130" height="28" rx="3" fill="#13241C" stroke="var(--color-riftless-signal)" strokeWidth="1.2" />
                  <text x="0" y="4" fill="var(--color-riftless-signal)" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">DECISION DOCUMENT</text>
                </g>

                {/* 3. DEPRECATION NOTE (Active) */}
                <g className="memory-node-deprecation" transform="translate(110, 290)">
                  <rect x="-65" y="-14" width="130" height="28" rx="3" fill="#13241C" stroke="var(--color-riftless-signal)" strokeWidth="1.2" />
                  <text x="0" y="4" fill="var(--color-riftless-signal)" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">DEPRECATION NOTE</text>
                </g>

                {/* Right Column Surrounding Nodes */}
                {/* 4. VALIDATION RESULT (Active) */}
                <g className="memory-node-validation" transform="translate(410, 90)">
                  <rect x="-65" y="-14" width="130" height="28" rx="3" fill="#13241C" stroke="var(--color-riftless-signal)" strokeWidth="1.2" />
                  <text x="0" y="4" fill="var(--color-riftless-signal)" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">VALIDATION RESULT</text>
                </g>

                {/* 5. OWNER ACTION (Inactive) */}
                <g className="memory-node-owner" transform="translate(410, 190)">
                  <rect x="-60" y="-14" width="120" height="28" rx="3" fill="#1E293B" stroke="#4B5563" strokeWidth="1" />
                  <text x="0" y="4" fill="#9CA3AF" fontSize="9" fontFamily="monospace" textAnchor="middle">OWNER ACTION</text>
                </g>

                {/* 6. INCIDENT STATUS (Inactive) */}
                <g className="memory-node-incident" transform="translate(410, 290)">
                  <rect x="-60" y="-14" width="120" height="28" rx="3" fill="#1E293B" stroke="#4B5563" strokeWidth="1" />
                  <text x="0" y="4" fill="#9CA3AF" fontSize="9" fontFamily="monospace" textAnchor="middle">INCIDENT STATUS</text>
                </g>

                {/* Central Asset Node */}
                <g className="memory-node-center" transform="translate(260, 190)">
                  <rect x="-105" y="-18" width="210" height="36" rx="4" fill="#11181B" stroke="var(--color-riftless-paper)" strokeWidth="1.5" />
                  <text x="0" y="5" fill="var(--color-riftless-paper)" fontSize="10.5" fontFamily="monospace" textAnchor="middle" fontWeight="bold">analytics.orders.customer_id</text>
                </g>

                {/* Watermark/Output indication inside SVG */}
                <g className="memory-registry-success" transform="translate(260, 352)">
                  <text x="0" y="0" fill="var(--color-riftless-muted)" fontSize="9" fontFamily="monospace" textAnchor="middle" letterSpacing="0.05em">
                    DATAHUB METADATA REGISTRY — WRITEBACK PATHWAY [SUCCESS]
                  </text>
                </g>
              </svg>
            </div>

          </div>

          {/* Core Outcomes Grid / Small Output Details */}
          <div className="pt-12 border-t border-slate-800/60 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center font-mono text-[10px] sm:text-xs">
            <div className="p-4 bg-slate-900/50 rounded border border-slate-800/80 memory-output-record">
              <div className="text-[var(--color-riftless-signal)] font-bold">✔ RIFTLESS_REMEDIATED</div>
              <div className="text-slate-500 text-[9px] mt-1.5 uppercase">METADATA INJECTED</div>
            </div>
            
            <div className="p-4 bg-slate-900/50 rounded border border-slate-800/80 memory-output-record">
              <div className="text-[var(--color-riftless-signal)] font-bold">✔ RISK SCORE RECORDED</div>
              <div className="text-slate-500 text-[9px] mt-1.5 uppercase">DATAHUB GRAPH UPDATED</div>
            </div>

            <div className="p-4 bg-slate-900/50 rounded border border-slate-800/80 memory-output-record">
              <div className="text-[var(--color-riftless-signal)] font-bold">✔ DECISION PRESERVED</div>
              <div className="text-slate-500 text-[9px] mt-1.5 uppercase">PERMANENT REVIEW LOG</div>
            </div>

            <div className="p-4 bg-slate-900/50 rounded border border-slate-800/80 memory-output-record">
              <div className="text-[var(--color-riftless-signal)] font-bold">✔ CONTEXT AVAILABLE</div>
              <div className="text-slate-500 text-[9px] mt-1.5 uppercase">TO THE NEXT AGENT</div>
            </div>
          </div>

          {/* Simulating Notice */}
          <div className="text-center text-[9px] font-mono text-slate-600 uppercase tracking-widest pt-4 memory-workflow-label">
            // WORKFLOW EXAMPLE — SIMULATED METADATA WRITEBACK WORKFLOW
          </div>

        </div>
      </section>

      {/* 7. FINAL CTA & FOOTER (06 / READY TO SHIP) */}
      <section id="ready-to-ship" ref={readyToShipRef} className="w-full bg-[var(--color-riftless-signal)] text-[var(--color-riftless-ink)] py-24 px-4 sm:px-6 lg:px-8 select-none relative overflow-hidden">
        <div className="max-w-4xl mx-auto text-center space-y-10 relative z-10">
          
          {/* Label */}
          <span className="text-xs font-mono font-bold tracking-[0.25em] text-[var(--color-riftless-ink)]/80 uppercase block ship-label">
            06 / READY TO SHIP
          </span>

          {/* Headline */}
          <h2 className="text-4xl sm:text-6xl md:text-7xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-ink)]">
            <span className="block ship-title-line">KNOW THE BLAST RADIUS.</span>
            <span className="block ship-title-line">SHIP THE VERIFIED FIX.</span>
          </h2>

          {/* Supporting Copy */}
          <p className="text-lg sm:text-xl font-sans text-[var(--color-riftless-ink)]/90 max-w-2xl mx-auto leading-relaxed ship-desc">
            See how RIFTLESS turns a breaking data change
            into a grounded, validated, and documented decision.
          </p>

          {/* Simple Lineage Symbol Decoration */}
          <div className="flex justify-center items-center gap-3 py-4 text-[var(--color-riftless-ink)]/30">
            <svg viewBox="0 0 100 24" className="w-24 h-6" fill="none" stroke="currentColor" strokeWidth="2">
              <circle className="ship-node-1" cx="12" cy="12" r="4" fill="currentColor" />
              <line className="ship-conn-1" x1="16" y1="12" x2="48" y2="12" stroke="currentColor" strokeWidth="2" strokeDasharray="3 3" />
              <circle className="ship-node-2" cx="52" cy="12" r="4" fill="currentColor" />
              <line className="ship-conn-2" x1="56" y1="12" x2="84" y2="12" stroke="currentColor" strokeWidth="2" strokeDasharray="3 3" />
              <circle className="ship-node-3" cx="88" cy="12" r="4" fill="none" stroke="currentColor" strokeWidth="2" />
            </svg>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center w-full max-w-md mx-auto pt-4">
            <Link to="/demo" className="w-full sm:w-1/2 focus:outline-none group ship-cta-btn">
              <button
                id="cta-run-demo"
                className="w-full py-4 text-xs font-mono font-bold uppercase tracking-widest bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] hover:bg-slate-800 transition-all rounded-none border border-[var(--color-riftless-ink)] cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--color-riftless-ink)]"
              >
                RUN THE DEMO <span className="inline-block transition-transform duration-300 group-hover:translate-x-1.5 motion-reduce:transition-none">→</span>
              </button>
            </Link>
            <Link to="/app/overview" className="w-full sm:w-1/2 focus:outline-none group ship-cta-btn">
              <button
                id="cta-launch-console"
                className="w-full py-4 text-xs font-mono font-bold uppercase tracking-widest bg-transparent text-[var(--color-riftless-ink)] hover:bg-[var(--color-riftless-ink)] hover:text-[var(--color-riftless-paper)] transition-all rounded-none border border-[var(--color-riftless-ink)] cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--color-riftless-ink)]"
              >
                LAUNCH CONSOLE <span className="inline-block transition-transform duration-300 group-hover:translate-x-1.5 motion-reduce:transition-none">→</span>
              </button>
            </Link>
          </div>

          {/* Small Technical Line */}
          <p className="text-[10px] sm:text-xs font-mono tracking-wider text-[var(--color-riftless-ink)]/80 uppercase pt-6 ship-tech-line">
            DATAHUB CONTEXT / DEEPSEEK REMEDIATION / EXECUTABLE VALIDATION
          </p>

        </div>
      </section>

    </div>
  );
}
