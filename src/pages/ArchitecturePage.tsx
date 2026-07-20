/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { registerMotionPlugins } from '../lib/motion';

gsap.registerPlugin(ScrollTrigger);

export function ArchitecturePage() {
  const isReducedMotion = useReducedMotion();
  const architectureHeroRef = useRef<HTMLDivElement>(null);
  const flowSectionRef = useRef<HTMLDivElement>(null);
  const systemLayersRef = useRef<HTMLDivElement>(null);
  const trustBoundariesRef = useRef<HTMLDivElement>(null);
  const contextLoopRef = useRef<HTMLDivElement>(null);
  const runLifecycleRef = useRef<HTMLDivElement>(null);
  const contractModelRef = useRef<HTMLDivElement>(null);
  const deploymentTopologyRef = useRef<HTMLDivElement>(null);
  const failureRecoveryRef = useRef<HTMLDivElement>(null);
  const architectureCtaRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(architectureHeroRef);
      const mm = gsap.matchMedia(architectureHeroRef);

      // Set initial animated states to avoid layout flash
      gsap.set(q('.hero-label'), { autoAlpha: 0, y: 14 });
      gsap.set(q('.hero-headline-line'), { autoAlpha: 0, y: 24 });
      gsap.set(q('.hero-supporting'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.hero-target-banner'), { autoAlpha: 0 });
      gsap.set(q('.hero-divider'), { scaleX: 0, transformOrigin: 'left center' });

      // Desktop: >= 1024px
      mm.add('(min-width: 1024px)', () => {
        gsap.set(q('.hero-constraints-panel'), { autoAlpha: 0, x: 16 });

        const tl = gsap.timeline({
          defaults: { ease: 'power2.out' }
        });

        tl.to(q('.hero-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.hero-headline-line'), { autoAlpha: 1, y: 0, duration: 0.6, stagger: 0.08 }, '-=0.25')
          .to(q('.hero-supporting'), { autoAlpha: 1, y: 0, duration: 0.45 }, '-=0.3')
          .to(q('.hero-target-banner'), { autoAlpha: 1, duration: 0.4 }, '-=0.25')
          .to(q('.hero-constraints-panel'), { autoAlpha: 1, x: 0, duration: 0.55 }, '-=0.35')
          .to(q('.hero-divider'), { scaleX: 1, duration: 0.5, ease: 'power2.out' }, '-=0.4');
      });

      // Mobile: < 1024px
      mm.add('(max-width: 1023px)', () => {
        // 8px max translation on mobile as requested
        gsap.set(q('.hero-constraints-panel'), { autoAlpha: 0, y: 8 });
        gsap.set(q('.hero-label'), { autoAlpha: 0, y: 8 });
        gsap.set(q('.hero-headline-line'), { autoAlpha: 0, y: 8 });
        gsap.set(q('.hero-supporting'), { autoAlpha: 0, y: 8 });

        const tl = gsap.timeline({
          defaults: { ease: 'power2.out' }
        });

        tl.to(q('.hero-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.hero-headline-line'), { autoAlpha: 1, y: 0, duration: 0.5, stagger: 0.06 }, '-=0.2')
          .to(q('.hero-supporting'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.25')
          .to(q('.hero-target-banner'), { autoAlpha: 1, duration: 0.35 }, '-=0.2')
          .to(q('.hero-constraints-panel'), { autoAlpha: 1, y: 0, duration: 0.45 }, '-=0.3')
          .to(q('.hero-divider'), { scaleX: 1, duration: 0.4, ease: 'power2.out' }, '-=0.3');
      });
    }, architectureHeroRef);

    return () => {
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(flowSectionRef);
      const mm = gsap.matchMedia(flowSectionRef);

      // Initial states to avoid layout flash
      gsap.set(q('.flow-label'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.flow-headline'), { autoAlpha: 0, y: 18 });
      gsap.set(q('.flow-supporting'), { autoAlpha: 0, y: 10 });

      gsap.set(q('.flow-node'), { scale: 0, transformOrigin: 'center center' });
      gsap.set(q('.flow-stage-details'), { autoAlpha: 0 });

      // Desktop init
      mm.add('(min-width: 1024px)', () => {
        gsap.set(q('.flow-line-1'), { scaleX: 0, transformOrigin: 'left center' });
        gsap.set(q('.flow-line-2'), { scaleX: 0, transformOrigin: 'left center' });

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: flowSectionRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          }
        });

        // Header Animation
        tl.to(q('.flow-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.flow-headline'), { autoAlpha: 1, y: 0, duration: 0.5 }, '-=0.25')
          .to(q('.flow-supporting'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.25');

        // Rail Sequence (Stage by stage)
        stages.forEach((stage, idx) => {
          const line1 = q(`.flow-stage-${idx} .flow-line-1`);
          const line2 = q(`.flow-stage-${idx} .flow-line-2`);
          const node = q(`.flow-stage-${idx} .flow-node`);
          const details = q(`.flow-stage-${idx} .flow-stage-details`);

          const timeOffset = idx === 0 ? '-=0.15' : '-=0.08';

          if (line1.length) {
            tl.to(line1, { scaleX: 1, duration: 0.08, ease: 'none' }, timeOffset);
          }
          tl.to(node, { scale: 1, duration: 0.1, ease: 'power2.out' }, line1.length ? '+=0.02' : timeOffset);
          if (line2.length) {
            tl.to(line2, { scaleX: 1, duration: 0.08, ease: 'none' }, '+=0.02');
          }
          
          tl.to(details, { autoAlpha: 1, y: 0, duration: 0.18, ease: 'power2.out' }, '-=0.05');
        });
      });

      // Mobile init
      mm.add('(max-width: 1023px)', () => {
        gsap.set(q('.flow-line-1'), { scaleY: 0, transformOrigin: 'top center' });
        gsap.set(q('.flow-line-2'), { scaleY: 0, transformOrigin: 'top center' });
        gsap.set(q('.flow-stage-details'), { y: 6 });

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: flowSectionRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          }
        });

        // Header Animation
        tl.to(q('.flow-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.flow-headline'), { autoAlpha: 1, y: 0, duration: 0.45 }, '-=0.2')
          .to(q('.flow-supporting'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.2');

        stages.forEach((stage, idx) => {
          const line1 = q(`.flow-stage-${idx} .flow-line-1`);
          const line2 = q(`.flow-stage-${idx} .flow-line-2`);
          const node = q(`.flow-stage-${idx} .flow-node`);
          const details = q(`.flow-stage-${idx} .flow-stage-details`);

          const timeOffset = idx === 0 ? '-=0.1' : '-=0.06';

          if (line1.length) {
            tl.to(line1, { scaleY: 1, duration: 0.06, ease: 'none' }, timeOffset);
          }
          tl.to(node, { scale: 1, duration: 0.08, ease: 'power2.out' }, line1.length ? '+=0.01' : timeOffset);
          if (line2.length) {
            tl.to(line2, { scaleY: 1, duration: 0.06, ease: 'none' }, '+=0.01');
          }
          tl.to(details, { autoAlpha: 1, y: 0, duration: 0.15, ease: 'power2.out' }, '-=0.03');
        });
      });
    }, flowSectionRef);

    return () => {
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(systemLayersRef);
      const mm = gsap.matchMedia(systemLayersRef);

      // Initial states to avoid layout flash
      gsap.set(q('.layers-label'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.layers-headline-line'), { autoAlpha: 0, y: 20 });
      gsap.set(q('.layers-supporting'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.layers-target-model'), { autoAlpha: 0, y: 8 });

      gsap.set(q('.layers-rail-line'), { scaleY: 0, transformOrigin: 'top center' });
      gsap.set(q('.layers-rail-step-0'), { autoAlpha: 0, x: -8 });
      gsap.set(q('.layers-rail-step-1'), { autoAlpha: 0, x: -8 });
      gsap.set(q('.layers-rail-step-2'), { autoAlpha: 0, x: -8 });
      gsap.set(q('.layers-rail-step-3'), { autoAlpha: 0, x: -8 });

      gsap.set(q('.layers-mobile-step'), { autoAlpha: 0, x: -6 });

      gsap.set(q('.layers-stack-wrapper'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.layer-panel'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.layer-heading'), { autoAlpha: 0, x: -8 });
      gsap.set(q('.layer-desc'), { autoAlpha: 0 });
      gsap.set(q('.layer-tech'), { autoAlpha: 0 });
      gsap.set(q('.layer-tech-badge'), { autoAlpha: 0, scale: 0.9 });

      gsap.set(q('.layers-output-bar'), { autoAlpha: 0, y: 8 });

      // Desktop: >= 1024px
      mm.add('(min-width: 1024px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: systemLayersRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          }
        });

        // 1. Header
        tl.to(q('.layers-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.layers-headline-line'), { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')
          .to(q('.layers-supporting'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3')
          .to(q('.layers-target-model'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3');

        // 2. Control Rail & Layers Stack wrapper
        tl.to(q('.layers-stack-wrapper'), { autoAlpha: 1, y: 0, duration: 0.5 }, '-=0.2');

        // 3. Desktop Rail Timeline with layered side activations
        // Step 01
        tl.to(q('.layers-rail-line'), { scaleY: 0.15, duration: 0.1, ease: 'power2.out' })
          .to(q('.layers-rail-step-0'), { autoAlpha: 1, x: 0, duration: 0.25, ease: 'power2.out' }, '-=0.05')
          // Layer 01 panel activation
          .to(q('.layer-panel-1'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.15')
          .to(q('.layer-panel-1 .layer-heading'), { autoAlpha: 1, x: 0, duration: 0.2 }, '-=0.15')
          .to(q('.layer-panel-1 .layer-desc'), { autoAlpha: 1, duration: 0.2 }, '-=0.1')
          .to(q('.layer-panel-1 .layer-tech'), { autoAlpha: 1, duration: 0.15 }, '-=0.1')
          .to(q('.layer-panel-1 .layer-tech-badge'), { autoAlpha: 1, scale: 1, duration: 0.15, stagger: 0.03 }, '-=0.1');

        // Step 02
        tl.to(q('.layers-rail-line'), { scaleY: 0.5, duration: 0.15, ease: 'power2.out' })
          .to(q('.layers-rail-step-1'), { autoAlpha: 1, x: 0, duration: 0.25, ease: 'power2.out' }, '-=0.08')
          // Layer 02 panel activation
          .to(q('.layer-panel-2'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.15')
          .to(q('.layer-panel-2 .layer-heading'), { autoAlpha: 1, x: 0, duration: 0.2 }, '-=0.15')
          .to(q('.layer-panel-2 .layer-desc'), { autoAlpha: 1, duration: 0.2 }, '-=0.1')
          .to(q('.layer-panel-2 .layer-tech'), { autoAlpha: 1, duration: 0.15 }, '-=0.1')
          .to(q('.layer-panel-2 .layer-tech-badge'), { autoAlpha: 1, scale: 1, duration: 0.15, stagger: 0.03 }, '-=0.1');

        // Step 03 & 04 (runs to 100%)
        tl.to(q('.layers-rail-line'), { scaleY: 1, duration: 0.2, ease: 'power2.out' })
          .to(q('.layers-rail-step-2'), { autoAlpha: 1, x: 0, duration: 0.25, ease: 'power2.out' }, '-=0.12')
          .to(q('.layers-rail-step-3'), { autoAlpha: 1, x: 0, duration: 0.25, ease: 'power2.out' }, '-=0.08')
          // Layer 03 panel activation
          .to(q('.layer-panel-3'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.15')
          .to(q('.layer-panel-3 .layer-heading'), { autoAlpha: 1, x: 0, duration: 0.2 }, '-=0.15')
          .to(q('.layer-panel-3 .layer-desc'), { autoAlpha: 1, duration: 0.2 }, '-=0.1')
          .to(q('.layer-panel-3 .layer-tech'), { autoAlpha: 1, duration: 0.15 }, '-=0.1')
          .to(q('.layer-panel-3 .layer-tech-badge'), { autoAlpha: 1, scale: 1, duration: 0.15, stagger: 0.03 }, '-=0.1');

        // 4. Output Statement
        tl.to(q('.layers-output-bar'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.1');
      });

      // Mobile: < 1024px
      mm.add('(max-width: 1023px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: systemLayersRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          }
        });

        // 1. Header
        tl.to(q('.layers-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.layers-headline-line'), { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.06 }, '-=0.2')
          .to(q('.layers-supporting'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.2')
          .to(q('.layers-target-model'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.25');

        // 2. Mobile step sequence
        tl.to(q('.layers-mobile-step'), { autoAlpha: 1, x: 0, duration: 0.3, stagger: 0.05 }, '-=0.15');

        // 3. Layers Stack wrapper & panel items
        tl.to(q('.layers-stack-wrapper'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.1')
          .to(q('.layer-panel'), { autoAlpha: 1, y: 0, duration: 0.35, stagger: 0.1 }, '-=0.2')
          .to(q('.layer-heading, .layer-desc, .layer-tech'), { autoAlpha: 1, x: 0, duration: 0.25, stagger: 0.04 }, '-=0.3')
          .to(q('.layer-tech-badge'), { autoAlpha: 1, scale: 1, duration: 0.2, stagger: 0.02 }, '-=0.15');

        // 4. Output Statement
        tl.to(q('.layers-output-bar'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.1');
      });
    }, systemLayersRef);

    return () => {
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(trustBoundariesRef);
      const mm = gsap.matchMedia(trustBoundariesRef);

      // Initial states to avoid layout flash
      gsap.set(q('.trust-label'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.trust-headline-line'), { autoAlpha: 0, y: 20 });
      gsap.set(q('.trust-supporting'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.trust-target-model'), { autoAlpha: 0, y: 8 });

      gsap.set(q('.trust-trajectory-container'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.trajectory-step'), { autoAlpha: 0, x: -8 });
      gsap.set(q('.trajectory-arrow'), { autoAlpha: 0, scaleX: 0.5 });

      gsap.set(q('.trust-zones-container'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.zone-1'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.zone-2'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.zone-3'), { autoAlpha: 0, y: 8 });

      gsap.set(q('.guardrail-card'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.trust-blocked-path'), { autoAlpha: 0, y: 8 });

      // Desktop: >= 1024px
      mm.add('(min-width: 1024px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: trustBoundariesRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          }
        });

        // 1. Header
        tl.to(q('.trust-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.trust-headline-line'), { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')
          .to(q('.trust-supporting'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3')
          .to(q('.trust-target-model'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3');

        // 2. Trajectory Block
        tl.to(q('.trust-trajectory-container'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.1')
          .to(q('.trajectory-step, .trajectory-arrow'), { autoAlpha: 1, x: 0, scaleX: 1, duration: 0.25, stagger: 0.05, ease: 'power2.out' }, '-=0.2');

        // 3. Three-zone sequence
        tl.to(q('.trust-zones-container'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.1')
          // Zone 1
          .to(q('.zone-1'), { autoAlpha: 1, y: 0, duration: 0.3, ease: 'power2.out' }, '-=0.2')
          // Zone 2 (Policy Gate)
          .to(q('.zone-2'), { autoAlpha: 1, y: 0, duration: 0.3, ease: 'power2.out' }, '-=0.15')
          // Zone 3 (Evidence Sandbox)
          .to(q('.zone-3'), { autoAlpha: 1, y: 0, duration: 0.3, ease: 'power2.out' }, '-=0.15');

        // 4. Guardrail sequence
        tl.to(q('.guardrail-card'), { autoAlpha: 1, y: 0, duration: 0.35, stagger: 0.1, ease: 'power2.out' }, '-=0.1');

        // 5. Blocked path (threat vector guard) appears last
        tl.to(q('.trust-blocked-path'), { autoAlpha: 1, y: 0, duration: 0.35, ease: 'power2.out' }, '-=0.15');
      });

      // Mobile: < 1024px
      mm.add('(max-width: 1023px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: trustBoundariesRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          }
        });

        // 1. Header (Mobile sequence is faster, max translation 6-8px)
        tl.to(q('.trust-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.trust-headline-line'), { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.06 }, '-=0.2')
          .to(q('.trust-supporting'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.2')
          .to(q('.trust-target-model'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.25');

        // 2. Trajectory Block (Mobile: max translation 6-8px)
        tl.to(q('.trust-trajectory-container'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.1')
          .to(q('.trajectory-step, .trajectory-arrow'), { autoAlpha: 1, x: 0, scaleX: 1, duration: 0.2, stagger: 0.03, ease: 'power2.out' }, '-=0.15');

        // 3. Three-zone sequence
        tl.to(q('.trust-zones-container'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.1')
          .to(q('.zone-1'), { autoAlpha: 1, y: 0, duration: 0.25, ease: 'power2.out' }, '-=0.15')
          .to(q('.zone-2'), { autoAlpha: 1, y: 0, duration: 0.25, ease: 'power2.out' }, '-=0.15')
          .to(q('.zone-3'), { autoAlpha: 1, y: 0, duration: 0.25, ease: 'power2.out' }, '-=0.15');

        // 4. Guardrail sequence
        tl.to(q('.guardrail-card'), { autoAlpha: 1, y: 0, duration: 0.3, stagger: 0.08, ease: 'power2.out' }, '-=0.15');

        // 5. Blocked path
        tl.to(q('.trust-blocked-path'), { autoAlpha: 1, y: 0, duration: 0.3, ease: 'power2.out' }, '-=0.1');
      });
    }, trustBoundariesRef);

    return () => {
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    let active = true;
    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(contextLoopRef);
      const mm = gsap.matchMedia(contextLoopRef);

      // Initial states to avoid layout flash
      gsap.set(q('.loop-label'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.loop-headline-line'), { autoAlpha: 0, y: 20 });
      gsap.set(q('.loop-supporting'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.loop-target-model'), { autoAlpha: 0, y: 10 });

      gsap.set(q('.loop-diagram-container'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.loop-trajectory-container'), { autoAlpha: 0 });
      gsap.set(q('.loop-read-path'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.loop-writeback-path'), { autoAlpha: 0, y: 6 });

      gsap.set(q('.part-a'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.part-a-title'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.part-a-item'), { autoAlpha: 0, scale: 0.95 });
      gsap.set(q('.part-a-client'), { autoAlpha: 0, y: 6 });

      gsap.set(q('.part-b'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.part-b-title'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.part-b-stage'), { autoAlpha: 0, x: -8 });
      gsap.set(q('.part-b-footer'), { autoAlpha: 0, scale: 0.95 });

      gsap.set(q('.part-c'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.part-c-title'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.part-c-item'), { autoAlpha: 0, scale: 0.95 });
      gsap.set(q('.part-c-client'), { autoAlpha: 0, y: 6 });

      gsap.set(q('.return-loop-graphic'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.desktop-return-label'), { autoAlpha: 0 });
      gsap.set(q('.desktop-return-rail'), { scaleX: 0, transformOrigin: 'right center' });
      gsap.set(q('.mobile-return-rail'), { autoAlpha: 0, y: 4 });
      gsap.set(q('.loop-summary-labels'), { autoAlpha: 0, y: 4 });

      gsap.set(q('.loop-statement-footer'), { autoAlpha: 0, y: 8 });

      // Desktop: >= 1024px
      mm.add('(min-width: 1024px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: contextLoopRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal
        tl.to(q('.loop-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.loop-headline-line'), { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')
          .to(q('.loop-supporting'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3')
          .to(q('.loop-target-model'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3');

        // 2. Closed-Loop Diagram Container & Top Trajectory Banner
        tl.to(q('.loop-diagram-container'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.15')
          .to(q('.loop-trajectory-container'), { autoAlpha: 1, duration: 0.3 }, '-=0.25')
          .to([q('.loop-read-path'), q('.loop-writeback-path')], { autoAlpha: 1, y: 0, duration: 0.3, stagger: 0.08 }, '-=0.15');

        // 3. Columns Sequence (A -> B -> C)
        // Part A (Read Context)
        tl.to(q('.part-a'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.15')
          .to(q('.part-a-title'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.2')
          .to(q('.part-a-item'), { autoAlpha: 1, scale: 1, duration: 0.2, stagger: 0.04 }, '-=0.15')
          .to(q('.part-a-client'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.1');

        // Part B (Decide & Prove)
        tl.to(q('.part-b'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.15')
          .to(q('.part-b-title'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.2')
          .to(q('.part-b-stage'), { autoAlpha: 1, x: 0, duration: 0.25, stagger: 0.06 }, '-=0.15')
          .to(q('.part-b-footer'), { autoAlpha: 1, scale: 1, duration: 0.25 }, '-=0.1');

        // Part C (Write Knowledge Back)
        tl.to(q('.part-c'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.15')
          .to(q('.part-c-title'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.2')
          .to(q('.part-c-item'), { autoAlpha: 1, scale: 1, duration: 0.2, stagger: 0.04 }, '-=0.15')
          .to(q('.part-c-client'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.1');

        // 4. Return Loop Rail Sequence
        tl.to(q('.return-loop-graphic'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.1')
          .to(q('.desktop-return-label'), { autoAlpha: 1, duration: 0.25 }, '-=0.15')
          .to(q('.desktop-return-rail'), { scaleX: 1, duration: 0.45, ease: 'power2.out' }, '-=0.1')
          .to(q('.loop-summary-labels'), { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.15');

        // 5. Final Statement Footer
        tl.to(q('.loop-statement-footer'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.25');
      });

      // Mobile: < 1024px
      mm.add('(max-width: 1023px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: contextLoopRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header (Translation max 6-8px on mobile)
        tl.to(q('.loop-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.loop-headline-line'), { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.06 }, '-=0.2')
          .to(q('.loop-supporting'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.2')
          .to(q('.loop-target-model'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.25');

        // 2. Diagram Container
        tl.to(q('.loop-diagram-container'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.1')
          .to(q('.loop-trajectory-container'), { autoAlpha: 1, duration: 0.25 }, '-=0.2')
          .to([q('.loop-read-path'), q('.loop-writeback-path')], { autoAlpha: 1, y: 0, duration: 0.25, stagger: 0.05 }, '-=0.1');

        // 3. Columns Sequence (Part A, B, C)
        tl.to(q('.part-a'), { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.1')
          .to(q('.part-a-title'), { autoAlpha: 1, y: 0, duration: 0.2 }, '-=0.15')
          .to(q('.part-a-item'), { autoAlpha: 1, scale: 1, duration: 0.15, stagger: 0.03 }, '-=0.1')
          .to(q('.part-a-client'), { autoAlpha: 1, y: 0, duration: 0.2 }, '-=0.08');

        tl.to(q('.part-b'), { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.1')
          .to(q('.part-b-title'), { autoAlpha: 1, y: 0, duration: 0.2 }, '-=0.15')
          .to(q('.part-b-stage'), { autoAlpha: 1, x: 0, duration: 0.2, stagger: 0.04 }, '-=0.1')
          .to(q('.part-b-footer'), { autoAlpha: 1, scale: 1, duration: 0.2 }, '-=0.08');

        tl.to(q('.part-c'), { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.1')
          .to(q('.part-c-title'), { autoAlpha: 1, y: 0, duration: 0.2 }, '-=0.15')
          .to(q('.part-c-item'), { autoAlpha: 1, scale: 1, duration: 0.15, stagger: 0.03 }, '-=0.1')
          .to(q('.part-c-client'), { autoAlpha: 1, y: 0, duration: 0.2 }, '-=0.08');

        // 4. Return Loop (Mobile Simplified)
        tl.to(q('.return-loop-graphic'), { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.08')
          .to(q('.mobile-return-rail'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.15')
          .to(q('.loop-summary-labels'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.1');

        // 5. Final Loop Statement Footer
        tl.to(q('.loop-statement-footer'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.15');
      });

      document.fonts?.ready?.then(() => {
        if (active) {
          ScrollTrigger.refresh();
        }
      });
    }, contextLoopRef);

    return () => {
      active = false;
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    let active = true;
    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(runLifecycleRef);
      const mm = gsap.matchMedia(runLifecycleRef);

      // Initial states to avoid layout flash
      gsap.set(q('.run-lifecycle-label'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.run-lifecycle-headline-line'), { autoAlpha: 0, y: 20 });
      gsap.set(q('.run-lifecycle-supporting'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.run-lifecycle-target-model'), { autoAlpha: 0, y: 10 });

      gsap.set(q('.lifecycle-rail-desktop'), { scaleX: 0, transformOrigin: 'left center' });
      gsap.set(q('.lifecycle-marker'), { autoAlpha: 0, scale: 0.8 });
      gsap.set(q('.lifecycle-line-mobile'), { scaleY: 0, transformOrigin: 'top center' });
      gsap.set(q('.lifecycle-info'), { autoAlpha: 0, y: 8 });

      gsap.set(q('.risk-branch-section'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.risk-branch-allow'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.risk-branch-warn'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.risk-branch-block'), { autoAlpha: 0, y: 6 });

      gsap.set(q('.failure-path-section'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.failure-path-box'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.failure-statement'), { autoAlpha: 0, y: 6 });

      gsap.set(q('.artifact-trail-section'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.artifact-marker-item'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.artifact-separator'), { autoAlpha: 0 });
      gsap.set(q('.artifact-badge'), { autoAlpha: 0, scale: 0.95 });

      // Desktop: >= 1024px
      mm.add('(min-width: 1024px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: runLifecycleRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal
        tl.to(q('.run-lifecycle-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.run-lifecycle-headline-line'), { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')
          .to(q('.run-lifecycle-supporting'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3')
          .to(q('.run-lifecycle-target-model'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3');

        // 2. Main Lifecycle Sequence (Horizontal Rail and Steps)
        // Main rail forms from left to right (scaleX: 0 -> 1)
        tl.to(q('.lifecycle-rail-desktop'), { scaleX: 1, duration: 0.8, ease: 'none' }, '-=0.1');

        // Stagger steps markers and info text as rail forms
        tl.to(q('.lifecycle-marker'), { autoAlpha: 1, scale: 1, duration: 0.2, stagger: 0.08 }, '-=0.7')
          .to(q('.lifecycle-info'), { autoAlpha: 1, y: 0, duration: 0.25, stagger: 0.08 }, '-=0.6');

        // 3. Risk Decision Branches (ALLOW -> WARN -> BLOCK)
        // Appears after RISK DECIDED
        tl.to(q('.risk-branch-section'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.1')
          .to(q('.risk-branch-allow'), { autoAlpha: 1, y: 0, duration: 0.25 })
          .to(q('.risk-branch-warn'), { autoAlpha: 1, y: 0, duration: 0.25 })
          .to(q('.risk-branch-block'), { autoAlpha: 1, y: 0, duration: 0.25 });

        // 4. Validation Failure Path (appears after state VALIDATING / step 5)
        tl.to(q('.failure-path-section'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.5')
          .to(q('.failure-path-box'), { autoAlpha: 1, y: 0, duration: 0.25 })
          .to(q('.failure-statement'), { autoAlpha: 1, y: 0, duration: 0.3 });

        // 5. Artifact Trail (appears last)
        tl.to(q('.artifact-trail-section'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to([q('.artifact-marker-item'), q('.artifact-separator')], { autoAlpha: 1, y: 0, duration: 0.15, stagger: 0.03 })
          .to(q('.artifact-badge'), { autoAlpha: 1, scale: 1, duration: 0.25 }, '-=0.1');
      });

      // Mobile: < 1024px
      mm.add('(max-width: 1023px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: runLifecycleRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal (max 6-8px y translation)
        tl.to(q('.run-lifecycle-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.run-lifecycle-headline-line'), { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.06 }, '-=0.2')
          .to(q('.run-lifecycle-supporting'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.2')
          .to(q('.run-lifecycle-target-model'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.25');

        // 2. Main Lifecycle Sequence (Vertical Spine & Faster Sequence, max 6-8px translation)
        tl.to(q('.lifecycle-marker'), { autoAlpha: 1, scale: 1, duration: 0.15, stagger: 0.05 }, '-=0.1')
          .to(q('.lifecycle-line-mobile'), { scaleY: 1, duration: 0.4, ease: 'none', stagger: 0.05 }, '-=0.35')
          .to(q('.lifecycle-info'), { autoAlpha: 1, y: 0, duration: 0.18, stagger: 0.05 }, '-=0.35');

        // 3. Risk Decision Branches (ALLOW -> WARN -> BLOCK)
        tl.to(q('.risk-branch-section'), { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.1')
          .to(q('.risk-branch-allow'), { autoAlpha: 1, y: 0, duration: 0.2 })
          .to(q('.risk-branch-warn'), { autoAlpha: 1, y: 0, duration: 0.2 })
          .to(q('.risk-branch-block'), { autoAlpha: 1, y: 0, duration: 0.2 });

        // 4. Validation Failure Path
        tl.to(q('.failure-path-section'), { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.3')
          .to(q('.failure-path-box'), { autoAlpha: 1, y: 0, duration: 0.2 })
          .to(q('.failure-statement'), { autoAlpha: 1, y: 0, duration: 0.25 });

        // 5. Artifact Trail
        tl.to(q('.artifact-trail-section'), { autoAlpha: 1, y: 0, duration: 0.3 })
          .to([q('.artifact-marker-item'), q('.artifact-separator')], { autoAlpha: 1, y: 0, duration: 0.1, stagger: 0.02 })
          .to(q('.artifact-badge'), { autoAlpha: 1, scale: 1, duration: 0.2 }, '-=0.08');
      });

      document.fonts?.ready?.then(() => {
        if (active) {
          ScrollTrigger.refresh();
        }
      });
    }, runLifecycleRef);

    return () => {
      active = false;
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    let active = true;
    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(contractModelRef);
      const mm = gsap.matchMedia(contractModelRef);

      // Initial states to avoid layout flash
      gsap.set(q('.contract-model-label'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.contract-model-headline-line'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.contract-model-supporting'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.contract-model-target-model'), { autoAlpha: 0, y: 6 });

      // Desktop rails
      gsap.set(q('.contract-rail-desktop'), { scaleX: 0, transformOrigin: 'left center' });
      gsap.set(q('.contract-rail-desktop-success'), { scaleX: 0, transformOrigin: 'left center' });

      // Mobile spines
      gsap.set(q('.contract-spine-mobile'), { scaleY: 0, transformOrigin: 'top center' });
      gsap.set(q('.contract-spine-mobile-success'), { scaleY: 0, transformOrigin: 'top center' });

      // For the contract columns
      gsap.set(q('.contract-marker'), { autoAlpha: 0, scale: 0.8 });
      gsap.set(q('.contract-ownership'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.contract-heading'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.contract-fields-list'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.contract-field-item'), { autoAlpha: 0 });
      gsap.set(q('.contract-flow-arrow'), { autoAlpha: 0 });

      // Redaction boundary
      gsap.set(q('.redaction-boundary-row'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.redaction-boundary-box'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.redaction-secrets-label'), { autoAlpha: 0, y: 4 });
      gsap.set(q('.redaction-context-label'), { autoAlpha: 0, y: 4 });
      gsap.set(q('.redaction-target-boundary'), { autoAlpha: 0, y: 4 });
      gsap.set(q('.redaction-cross'), { autoAlpha: 0, scale: 0.8 });
      gsap.set(q('.redaction-connector'), { autoAlpha: 0, scale: 0.8 });

      // Invariant statement
      gsap.set(q('.invariants-row'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.invariants-item'), { autoAlpha: 0, y: 6 });

      // Desktop: >= 1024px
      mm.add('(min-width: 1024px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: contractModelRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal
        tl.to(q('.contract-model-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.contract-model-headline-line'), { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')
          .to(q('.contract-model-supporting'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3')
          .to(q('.contract-model-target-model'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3');

        // 2. Main rail forms from left to right
        tl.to(q('.contract-rail-desktop'), { scaleX: 1, duration: 0.8, ease: 'none' }, 'pipeline-start');

        // 3. Loop through 6 contract blocks
        const blocks = q('.contract-block');
        blocks.forEach((block, i) => {
          const timeOffset = `pipeline-start+=${i * 0.12}`;
          const marker = block.querySelector('.contract-marker');
          const ownership = block.querySelector('.contract-ownership');
          const heading = block.querySelector('.contract-heading');
          const fieldsList = block.querySelector('.contract-fields-list');
          const fieldItems = block.querySelectorAll('.contract-field-item');
          const arrow = block.querySelector('.contract-flow-arrow');

          tl.to(marker, { autoAlpha: 1, scale: 1, duration: 0.15 }, timeOffset)
            .to(ownership, { autoAlpha: 1, y: 0, duration: 0.15 }, timeOffset)
            .to(heading, { autoAlpha: 1, y: 0, duration: 0.15 }, timeOffset)
            .to(fieldsList, { autoAlpha: 1, y: 0, duration: 0.15 }, timeOffset)
            .to(fieldItems, { autoAlpha: 1, duration: 0.08, stagger: 0.01 }, timeOffset)
            .to(arrow, { autoAlpha: 1, duration: 0.1 }, timeOffset);

          // Success Evidence Rail trigger at Block 5 (index 4)
          if (i === 4) {
            tl.to(q('.contract-rail-desktop-success'), { scaleX: 1, duration: 0.25, ease: 'none' }, `pipeline-start+=${4 * 0.12}`);
          }
        });

        // 4. Redaction Boundary
        tl.to(q('.redaction-boundary-row'), { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.1')
          .to(q('.redaction-boundary-box'), { autoAlpha: 1, y: 0, duration: 0.25 })
          .to([q('.redaction-secrets-label'), q('.redaction-context-label'), q('.redaction-target-boundary')], { autoAlpha: 1, y: 0, duration: 0.2, stagger: 0.05 })
          .to([q('.redaction-connector'), q('.redaction-cross')], { autoAlpha: 1, y: 0, scale: 1, duration: 0.2, stagger: 0.05 });

        // 5. Invariant Statement appears last
        tl.to(q('.invariants-row'), { autoAlpha: 1, y: 0, duration: 0.25 })
          .to(q('.invariants-item'), { autoAlpha: 1, y: 0, duration: 0.2, stagger: 0.04 }, '-=0.1');
      });

      // Mobile: < 1024px
      mm.add('(max-width: 1023px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: contractModelRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal (max 6-8px y translation)
        tl.to(q('.contract-model-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.contract-model-headline-line'), { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.06 }, '-=0.2')
          .to(q('.contract-model-supporting'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.2')
          .to(q('.contract-model-target-model'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.25');

        // 2. Spine forms top to bottom
        tl.to(q('.contract-spine-mobile'), { scaleY: 1, duration: 0.5, ease: 'none' }, 'pipeline-start');

        // 3. Loop through 6 contract blocks
        const blocks = q('.contract-block');
        blocks.forEach((block, i) => {
          const timeOffset = `pipeline-start+=${i * 0.08}`;
          const marker = block.querySelector('.contract-marker');
          const ownership = block.querySelector('.contract-ownership');
          const heading = block.querySelector('.contract-heading');
          const fieldsList = block.querySelector('.contract-fields-list');
          const fieldItems = block.querySelectorAll('.contract-field-item');
          const arrow = block.querySelector('.contract-flow-arrow');

          tl.to(marker, { autoAlpha: 1, scale: 1, duration: 0.12 }, timeOffset)
            .to(ownership, { autoAlpha: 1, y: 0, duration: 0.12 }, timeOffset)
            .to(heading, { autoAlpha: 1, y: 0, duration: 0.12 }, timeOffset)
            .to(fieldsList, { autoAlpha: 1, y: 0, duration: 0.12 }, timeOffset)
            .to(fieldItems, { autoAlpha: 1, duration: 0.05, stagger: 0.01 }, timeOffset)
            .to(arrow, { autoAlpha: 1, duration: 0.08 }, timeOffset);

          // Success Evidence Spine trigger at Block 5 (index 4)
          if (i === 4) {
            tl.to(q('.contract-spine-mobile-success'), { scaleY: 1, duration: 0.15, ease: 'none' }, `pipeline-start+=${4 * 0.08}`);
          }
        });

        // 4. Redaction Boundary (max 6-8px y translation)
        tl.to(q('.redaction-boundary-row'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.1')
          .to(q('.redaction-boundary-box'), { autoAlpha: 1, y: 0, duration: 0.2 })
          .to([q('.redaction-secrets-label'), q('.redaction-context-label'), q('.redaction-target-boundary')], { autoAlpha: 1, y: 0, duration: 0.15, stagger: 0.03 })
          .to([q('.redaction-connector'), q('.redaction-cross')], { autoAlpha: 1, y: 0, scale: 1, duration: 0.15, stagger: 0.03 });

        // 5. Invariant Statement (max 6-8px translation)
        tl.to(q('.invariants-row'), { autoAlpha: 1, y: 0, duration: 0.2 })
          .to(q('.invariants-item'), { autoAlpha: 1, y: 0, duration: 0.15, stagger: 0.03 }, '-=0.08');
      });

      document.fonts?.ready?.then(() => {
        if (active) {
          ScrollTrigger.refresh();
        }
      });
    }, contractModelRef);

    return () => {
      active = false;
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    let active = true;
    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(deploymentTopologyRef);
      const mm = gsap.matchMedia(deploymentTopologyRef);

      // Initial states to avoid layout flash
      gsap.set(q('.topo-label'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.topo-headline-line'), { autoAlpha: 0, y: 20 });
      gsap.set(q('.topo-supporting'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.topo-target-model'), { autoAlpha: 0, y: 10 });

      // Rail / Spine
      gsap.set(q('.topo-rail-desktop'), { scaleX: 0, transformOrigin: 'left center' });
      gsap.set(q('.topo-spine-mobile'), { scaleY: 0, transformOrigin: 'top center' });

      // Columns
      gsap.set(q('.topo-col'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.topo-col-header'), { autoAlpha: 0, y: -4 });
      gsap.set(q('.topo-col-body'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.topo-col-dot'), { autoAlpha: 0, scale: 0.8 });
      gsap.set(q('.topo-col-comp-item'), { autoAlpha: 0, y: 4 });
      gsap.set(q('.topo-col-resp'), { autoAlpha: 0, y: 6 });

      // Paths Flow
      gsap.set(q('.topo-paths-row'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.topo-path-card'), { autoAlpha: 0, y: 8 });

      // Secrets Panel
      gsap.set(q('.topo-security-envelope'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.topo-secrets-left'), { autoAlpha: 0, x: -8 });
      gsap.set(q('.topo-secrets-right'), { autoAlpha: 0, x: 8 });
      gsap.set(q('.topo-secrets-blocked-connector'), { autoAlpha: 0, scaleY: 0, transformOrigin: 'center center' });
      gsap.set(q('.topo-secrets-blocked'), { autoAlpha: 0, scaleY: 0 });
      gsap.set(q('.topo-secrets-cross'), { autoAlpha: 0, scale: 0.5 });

      // Desktop Layout (>= 1024px)
      mm.add('(min-width: 1024px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: deploymentTopologyRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal
        tl.to(q('.topo-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.topo-headline-line'), { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')
          .to([q('.topo-supporting'), q('.topo-target-model')], { autoAlpha: 1, y: 0, duration: 0.4, stagger: 0.05 }, '-=0.3');

        // 2. Desktop Rail forms from left to right
        tl.to(q('.topo-rail-desktop'), { scaleX: 1, duration: 0.8, ease: 'none' }, 'grid-start');

        // 3. Topology boundaries (columns) appear sequentially as the rail expands
        const columns = q('.topo-col');
        columns.forEach((col, idx) => {
          const timeOffset = `grid-start+=${idx * 0.18}`;
          const header = col.querySelector('.topo-col-header');
          const body = col.querySelector('.topo-col-body');
          const dot = col.querySelector('.topo-col-dot');
          const compItems = col.querySelectorAll('.topo-col-comp-item');
          const resp = col.querySelector('.topo-col-resp');

          tl.to(col, { autoAlpha: 1, y: 0, duration: 0.35 }, timeOffset)
            .to(header, { autoAlpha: 1, y: 0, duration: 0.2 }, timeOffset)
            .to(body, { autoAlpha: 1, y: 0, duration: 0.25 }, timeOffset)
            .to(dot, { autoAlpha: 1, scale: 1, duration: 0.15 }, timeOffset)
            .to(compItems, { autoAlpha: 1, y: 0, duration: 0.15, stagger: 0.03 }, `-=${0.1}`)
            .to(resp, { autoAlpha: 1, y: 0, duration: 0.25 }, `-=${0.1}`);
        });

        // 4. Data-flow path sequence
        tl.to(q('.topo-paths-row'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.15');
        
        const cards = q('.topo-path-card');
        cards.forEach((card, idx) => {
          tl.to(card, { autoAlpha: 1, y: 0, duration: 0.22 }, `-=${idx === 0 ? 0.1 : 0.14}`);
        });

        // 5. Secrets boundary after topology/paths
        tl.to(q('.topo-security-envelope'), { autoAlpha: 1, y: 0, duration: 0.3 })
          .to([q('.topo-secrets-left'), q('.topo-secrets-right')], { autoAlpha: 1, x: 0, duration: 0.25, stagger: 0.05 })
          .to([q('.topo-secrets-blocked-connector'), q('.topo-secrets-blocked')], { autoAlpha: 1, scaleY: 1, duration: 0.2 })
          .to(q('.topo-secrets-cross'), { autoAlpha: 1, scale: 1, duration: 0.15, stagger: 0.05 }, '-=0.05');
      });

      // Mobile Layout (< 1024px)
      mm.add('(max-width: 1023px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: deploymentTopologyRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal (max 6-8px y translation)
        tl.to(q('.topo-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.topo-headline-line'), { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.06 }, '-=0.2')
          .to([q('.topo-supporting'), q('.topo-target-model')], { autoAlpha: 1, y: 0, duration: 0.35, stagger: 0.04 }, '-=0.25');

        // 2. Spine forms top to bottom
        tl.to(q('.topo-spine-mobile'), { scaleY: 1, duration: 0.5, ease: 'none' }, 'grid-start');

        // 3. Topology boundaries (columns) appear faster sequentially
        const columns = q('.topo-col');
        columns.forEach((col, idx) => {
          const timeOffset = `grid-start+=${idx * 0.12}`;
          const header = col.querySelector('.topo-col-header');
          const body = col.querySelector('.topo-col-body');
          const dot = col.querySelector('.topo-col-dot');
          const compItems = col.querySelectorAll('.topo-col-comp-item');
          const resp = col.querySelector('.topo-col-resp');

          // Limit translation strictly to max 6-8px on mobile
          tl.to(col, { autoAlpha: 1, y: 0, duration: 0.25 }, timeOffset)
            .to(header, { autoAlpha: 1, y: 0, duration: 0.15 }, timeOffset)
            .to(body, { autoAlpha: 1, y: 0, duration: 0.2 }, timeOffset)
            .to(dot, { autoAlpha: 1, scale: 1, duration: 0.1 }, timeOffset)
            .to(compItems, { autoAlpha: 1, y: 0, duration: 0.1, stagger: 0.02 }, `-=${0.08}`)
            .to(resp, { autoAlpha: 1, y: 0, duration: 0.15 }, `-=${0.08}`);
        });

        // 4. Data-flow path sequence (translation max 6-8px)
        tl.to(q('.topo-paths-row'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.1');
        
        const cards = q('.topo-path-card');
        cards.forEach((card, idx) => {
          tl.to(card, { autoAlpha: 1, y: 0, duration: 0.18 }, `-=${idx === 0 ? 0.05 : 0.12}`);
        });

        // 5. Secrets boundary after topology/paths
        tl.to(q('.topo-security-envelope'), { autoAlpha: 1, y: 0, duration: 0.22 })
          .to([q('.topo-secrets-left'), q('.topo-secrets-right')], { autoAlpha: 1, x: 0, duration: 0.18, stagger: 0.03 })
          .to([q('.topo-secrets-blocked-connector'), q('.topo-secrets-blocked')], { autoAlpha: 1, scaleY: 1, duration: 0.15 })
          .to(q('.topo-secrets-cross'), { autoAlpha: 1, scale: 1, duration: 0.12, stagger: 0.03 }, '-=0.03');
      });

      document.fonts?.ready?.then(() => {
        if (active) {
          ScrollTrigger.refresh();
        }
      });
    }, deploymentTopologyRef);

    return () => {
      active = false;
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    let active = true;
    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(failureRecoveryRef);
      const mm = gsap.matchMedia(failureRecoveryRef);

      // Initial states to prevent layout flash
      gsap.set(q('.fail-label'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.fail-headline-line'), { autoAlpha: 0, y: 20 });
      gsap.set(q('.fail-supporting'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.fail-target-model'), { autoAlpha: 0, y: 10 });

      // Trajectory Rail
      gsap.set(q('.fail-rail-desktop'), { scaleX: 0, transformOrigin: 'left center' });
      gsap.set(q('.fail-spine-mobile'), { scaleY: 0, transformOrigin: 'top center' });
      gsap.set(q('.fail-trajectory-card'), { autoAlpha: 0, y: 8 });

      // Matrix
      gsap.set(q('.fail-matrix-row'), { autoAlpha: 0, y: 8 });

      // Branches & External Services
      gsap.set(q('.fail-branch-card'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.fail-ext-card'), { autoAlpha: 0, y: 8 });

      // Evidence Trail
      gsap.set(q('.fail-evidence-line-desktop'), { scaleX: 0, transformOrigin: 'left center' });
      gsap.set(q('.fail-evidence-line-mobile'), { scaleY: 0, transformOrigin: 'top center' });
      gsap.set(q('.fail-evidence-item'), { autoAlpha: 0, y: 6 });
      gsap.set(q('.fail-evidence-slash'), { autoAlpha: 0 });

      // Guardrail Invariant
      gsap.set(q('.fail-invariant-envelope'), { autoAlpha: 0, y: 8 });

      // Desktop Layout (>= 1024px)
      mm.add('(min-width: 1024px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: failureRecoveryRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal
        tl.to(q('.fail-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.fail-headline-line'), { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')
          .to([q('.fail-supporting'), q('.fail-target-model')], { autoAlpha: 1, y: 0, duration: 0.4, stagger: 0.05 }, '-=0.3');

        // 2. Trajectory Rail desktop (scale left-to-right) and sequential card markers
        tl.to(q('.fail-rail-desktop'), { scaleX: 1, duration: 0.6, ease: 'none' }, 'rail-start');
        
        const cards = q('.fail-trajectory-card');
        cards.forEach((card, idx) => {
          const timeOffset = `rail-start+=${idx * 0.12}`;
          tl.to(card, { autoAlpha: 1, y: 0, duration: 0.22 }, timeOffset);
        });

        // 3. Failure Response Matrix
        tl.to(q('.fail-matrix-row'), { autoAlpha: 1, y: 0, duration: 0.25, stagger: 0.06 }, '-=0.05');

        // 4. Recovery Branches: Safe Retry (Signal Lime) -> Human Review (Amber) -> Terminal Close (Red)
        tl.to(q('.fail-branch-safe'), { autoAlpha: 1, y: 0, duration: 0.22 }, '-=0.08')
          .to(q('.fail-branch-human'), { autoAlpha: 1, y: 0, duration: 0.22 }, '-=0.12')
          .to(q('.fail-branch-terminal'), { autoAlpha: 1, y: 0, duration: 0.22 }, '-=0.12');

        // 5. External service sequence (grouped stagger cepat)
        tl.to(q('.fail-ext-card'), { autoAlpha: 1, y: 0, duration: 0.18, stagger: 0.05 }, '-=0.15');

        // 6. Evidence Trail
        tl.to(q('.fail-evidence-line-desktop'), { scaleX: 1, duration: 0.4, ease: 'none' }, 'evidence-start');
        
        const evidenceItems = q('.fail-evidence-item');
        const evidenceSlashes = q('.fail-evidence-slash');
        evidenceItems.forEach((item, idx) => {
          const timeOffset = `evidence-start+=${idx * 0.06}`;
          tl.to(item, { autoAlpha: 1, y: 0, duration: 0.15 }, timeOffset);
          if (evidenceSlashes[idx]) {
            tl.to(evidenceSlashes[idx], { autoAlpha: 1, duration: 0.1 }, timeOffset);
          }
        });

        // 7. Invariant Guardrail
        tl.to(q('.fail-invariant-envelope'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.05');
      });

      // Mobile Layout (< 1024px)
      mm.add('(max-width: 1023px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: failureRecoveryRef.current,
            start: 'top 82%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal (translation max 6-8px on mobile)
        tl.to(q('.fail-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.fail-headline-line'), { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.06 }, '-=0.2')
          .to([q('.fail-supporting'), q('.fail-target-model')], { autoAlpha: 1, y: 0, duration: 0.35, stagger: 0.04 }, '-=0.25');

        // 2. Spine forms top to bottom
        tl.to(q('.fail-spine-mobile'), { scaleY: 1, duration: 0.4, ease: 'none' }, 'rail-start');
        
        const cards = q('.fail-trajectory-card');
        cards.forEach((card, idx) => {
          const timeOffset = `rail-start+=${idx * 0.08}`;
          tl.to(card, { autoAlpha: 1, y: 0, duration: 0.18 }, timeOffset);
        });

        // 3. Failure Response Matrix
        tl.to(q('.fail-matrix-row'), { autoAlpha: 1, y: 0, duration: 0.18, stagger: 0.04 }, '-=0.05');

        // 4. Recovery Branches
        tl.to(q('.fail-branch-safe'), { autoAlpha: 1, y: 0, duration: 0.18 }, '-=0.05')
          .to(q('.fail-branch-human'), { autoAlpha: 1, y: 0, duration: 0.18 }, '-=0.1')
          .to(q('.fail-branch-terminal'), { autoAlpha: 1, y: 0, duration: 0.18 }, '-=0.1');

        // 5. External service sequence
        tl.to(q('.fail-ext-card'), { autoAlpha: 1, y: 0, duration: 0.15, stagger: 0.04 }, '-=0.1');

        // 6. Evidence Trail mobile
        tl.to(q('.fail-evidence-line-mobile'), { scaleY: 1, duration: 0.3, ease: 'none' }, 'evidence-start');
        
        const evidenceItems = q('.fail-evidence-item');
        const evidenceSlashes = q('.fail-evidence-slash');
        evidenceItems.forEach((item, idx) => {
          const timeOffset = `evidence-start+=${idx * 0.04}`;
          tl.to(item, { autoAlpha: 1, y: 0, duration: 0.12 }, timeOffset);
          if (evidenceSlashes[idx]) {
            tl.to(evidenceSlashes[idx], { autoAlpha: 1, duration: 0.08 }, timeOffset);
          }
        });

        // 7. Invariant Guardrail
        tl.to(q('.fail-invariant-envelope'), { autoAlpha: 1, y: 0, duration: 0.25 }, '-=0.05');
      });

      document.fonts?.ready?.then(() => {
        if (active) {
          ScrollTrigger.refresh();
        }
      });
    }, failureRecoveryRef);

    return () => {
      active = false;
      ctx.revert();
    };
  }, [isReducedMotion]);

  useLayoutEffect(() => {
    if (isReducedMotion) return;

    registerMotionPlugins();

    let active = true;
    const ctx = gsap.context(() => {
      const q = gsap.utils.selector(architectureCtaRef);
      const mm = gsap.matchMedia(architectureCtaRef);

      // Initial states to prevent layout flash
      gsap.set(q('.cta-label'), { autoAlpha: 0, y: 12 });
      gsap.set(q('.cta-headline-line'), { autoAlpha: 0, y: 20 });
      gsap.set(q('.cta-supporting'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.cta-flow-node'), { autoAlpha: 0, y: 8 });
      gsap.set(q('.cta-flow-arrow'), { autoAlpha: 0 });
      gsap.set(q('.cta-button'), { autoAlpha: 0, y: 10 });
      gsap.set(q('.cta-disclaimer'), { autoAlpha: 0 });

      // Desktop Layout (>= 1024px)
      mm.add('(min-width: 1024px)', () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: architectureCtaRef.current,
            start: 'top 84%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal
        tl.to(q('.cta-label'), { autoAlpha: 1, y: 0, duration: 0.4 })
          .to(q('.cta-headline-line'), { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.08 }, '-=0.25')
          .to(q('.cta-supporting'), { autoAlpha: 1, y: 0, duration: 0.4 }, '-=0.3');

        // 2. Summary Flow sequential reveal (Snappy)
        const nodes = q('.cta-flow-node');
        const arrows = q('.cta-flow-arrow');
        nodes.forEach((node, idx) => {
          tl.to(node, { autoAlpha: 1, y: 0, duration: 0.12 }, `-=${idx === 0 ? 0.1 : 0.06}`);
          if (idx < nodes.length - 1) {
            const arrowDesktop = arrows[2 * idx];
            const arrowMobile = arrows[2 * idx + 1];
            tl.to([arrowDesktop, arrowMobile], { autoAlpha: 1, duration: 0.08 }, '-=0.04');
          }
        });

        // 3. CTA buttons
        tl.to(q('.cta-button'), { autoAlpha: 1, y: 0, duration: 0.4, stagger: 0.06 }, '-=0.05');

        // 4. Target disclaimer
        tl.to(q('.cta-disclaimer'), { autoAlpha: 1, duration: 0.3 }, '-=0.1');
      });

      // Mobile Layout (< 1024px)
      mm.add('(max-width: 1023px)', () => {
        // Limit translation to max 6-8px on mobile
        gsap.set(q('.cta-label'), { y: 8 });
        gsap.set(q('.cta-headline-line'), { y: 8 });
        gsap.set(q('.cta-supporting'), { y: 6 });
        gsap.set(q('.cta-flow-node'), { y: 6 });
        gsap.set(q('.cta-button'), { y: 6 });

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: architectureCtaRef.current,
            start: 'top 84%',
            toggleActions: 'play none none none',
            once: true
          },
          defaults: { ease: 'power2.out' }
        });

        // 1. Header Reveal
        tl.to(q('.cta-label'), { autoAlpha: 1, y: 0, duration: 0.35 })
          .to(q('.cta-headline-line'), { autoAlpha: 1, y: 0, duration: 0.45, stagger: 0.06 }, '-=0.2')
          .to(q('.cta-supporting'), { autoAlpha: 1, y: 0, duration: 0.35 }, '-=0.25');

        // 2. Summary Flow sequential reveal (Snappy, max 6-8px)
        const nodes = q('.cta-flow-node');
        const arrows = q('.cta-flow-arrow');
        nodes.forEach((node, idx) => {
          tl.to(node, { autoAlpha: 1, y: 0, duration: 0.1 }, `-=${idx === 0 ? 0.08 : 0.05}`);
          if (idx < nodes.length - 1) {
            const arrowDesktop = arrows[2 * idx];
            const arrowMobile = arrows[2 * idx + 1];
            tl.to([arrowDesktop, arrowMobile], { autoAlpha: 1, duration: 0.06 }, '-=0.03');
          }
        });

        // 3. CTA buttons
        tl.to(q('.cta-button'), { autoAlpha: 1, y: 0, duration: 0.35, stagger: 0.05 }, '-=0.04');

        // 4. Target disclaimer
        tl.to(q('.cta-disclaimer'), { autoAlpha: 1, duration: 0.25 }, '-=0.08');
      });

      document.fonts?.ready?.then(() => {
        if (active) {
          ScrollTrigger.refresh();
        }
      });
    }, architectureCtaRef);

    return () => {
      active = false;
      ctx.revert();
    };
  }, [isReducedMotion]);

  const stages = [
    {
      id: 'change-input',
      num: '01',
      title: 'CHANGE INPUT',
      tech: 'GitHub / SQL / dbt Manifest',
      desc: 'Proposed schema adjustments, migration files, or dbt manifest modifications submitted via Pull Request.',
    },
    {
      id: 'context-assembly',
      num: '02',
      title: 'CONTEXT ASSEMBLY',
      tech: 'DataHub GraphQL',
      desc: 'Resolves upstream lineage dependencies, ownership, and tags from the central data catalog.',
    },
    {
      id: 'risk-engine',
      num: '03',
      title: 'RISK ENGINE',
      tech: 'Deterministic Rules',
      desc: 'Evaluates prospective schema changes against deterministic rules to calculate impact and violations.',
    },
    {
      id: 'remediation',
      num: '04',
      title: 'REMEDIATION',
      tech: 'DeepSeek API',
      desc: 'Generates backward-compatible migration statements, dry-run remediation, or patch scripts.',
    },
    {
      id: 'validation',
      num: '05',
      title: 'VALIDATION',
      tech: 'SQLGlot / DuckDB / dbt',
      desc: 'Parses semantic structure using SQLGlot AST to dry-run transformations locally.',
    },
    {
      id: 'writeback',
      num: '06',
      title: 'WRITEBACK',
      tech: 'DataHub Metadata',
      desc: 'Commits validated decision files, runtime logs, and schema tags back to central DataHub.',
    }
  ];

  return (
    <div className="flex-grow bg-[var(--color-riftless-paper)] text-[var(--color-riftless-ink)] selection:bg-[var(--color-riftless-ink)] selection:text-[var(--color-riftless-paper)]">
      
      {/* 1. HERO SECTION (Asymmetrical grid) */}
      <section ref={architectureHeroRef} className="w-full py-16 sm:py-24 px-4 sm:px-6 lg:px-8 border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          
          {/* Left Column: Context Labels and Headline */}
          <div className="lg:col-span-8 space-y-6">
            <span className="hero-label text-xs font-mono font-bold tracking-[0.25em] text-[var(--color-riftless-graph-gray)] uppercase block">
              ARCHITECTURE / SYSTEM OVERVIEW
            </span>

            <h1 className="text-4xl sm:text-6xl md:text-7xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-ink)] overflow-hidden">
              <span className="hero-headline-line block">A CONTEXT-AWARE</span>
              <span className="hero-headline-line block">CONTROL PLANE FOR</span>
              <span className="hero-headline-line block">DATA CHANGES.</span>
            </h1>

            <p className="hero-supporting text-lg sm:text-xl font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-3xl">
              RIFTLESS combines metadata context, deterministic risk analysis,
              AI-assisted remediation, executable validation, and DataHub writeback
              into one continuous change-review system.
            </p>

            {/* Simple Line Reveal Decoration */}
            <div className="hero-divider h-[1px] bg-slate-200/80 w-full origin-left" />

            {/* Target System Architecture Alert/Status Flag */}
            <div className="hero-target-banner space-y-2 pt-2">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200/80 rounded-none">
                <span className="w-2 h-2 bg-[var(--color-riftless-signal)]" />
                <span className="text-[10px] font-mono tracking-wider uppercase font-bold text-[var(--color-riftless-ink)]">
                  TARGET SYSTEM ARCHITECTURE
                </span>
              </div>
              <p className="text-xs font-mono text-[var(--color-riftless-graph-gray)] max-w-2xl">
                // This describes the planned system architecture, detailing our pipeline blueprint rather than live production capabilities.
              </p>
            </div>
          </div>

          {/* Right Column: Specification Block */}
          <div className="hero-constraints-panel lg:col-span-4 p-6 bg-white border border-slate-200/80 rounded-none space-y-5 font-mono text-xs text-[var(--color-riftless-graph-gray)]">
            <div className="text-[11px] uppercase tracking-wider font-bold border-b border-slate-200 pb-2 text-[var(--color-riftless-ink)]">
              SYSTEM CONSTRAINTS
            </div>
            
            <div className="space-y-3.5">
              <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                <span>STAGE REGISTRY</span>
                <span className="text-[var(--color-riftless-ink)] font-bold">PLANNED</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                <span>REMEDIATION ENGINE</span>
                <span className="text-[var(--color-riftless-ink)] font-bold">DEEPSEEK API</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                <span>PARSER BASE</span>
                <span className="text-[var(--color-riftless-ink)] font-bold">SQLGLOT / AST</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                <span>WRITEBACK TARGET</span>
                <span className="text-[var(--color-riftless-ink)] font-bold">DATAHUB GRAPH</span>
              </div>
            </div>

            <p className="text-[10px] text-[var(--color-riftless-graph-gray)] leading-relaxed italic">
              * Riftless acts as an automated governance layer that intercepts schemas, assesses risk against catalog metadata, and compiles clean backfill patches.
            </p>
          </div>

        </div>
      </section>

      {/* 2. CONTINUOUS SYSTEM DIAGRAM */}
      <section ref={flowSectionRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-white/40">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="flex flex-col space-y-2">
            <span className="flow-label text-[10px] font-mono tracking-widest text-[var(--color-riftless-graph-gray)] uppercase block">
              // DATACHANGE PIPELINE
            </span>
            <h2 className="flow-headline text-xl sm:text-2xl font-display font-extrabold uppercase tracking-tight text-[var(--color-riftless-ink)]">
              Continuous System Flow
            </h2>
            <p className="flow-supporting text-sm font-sans text-[var(--color-riftless-graph-gray)] max-w-xl">
              From an incoming change trigger to the metadata registry writeback: the complete technical lifecycle path of a verified schema migration.
            </p>
          </div>

          {/* Continuous Flow Layout (Unified Shared Container) */}
          <div className="border border-slate-200 bg-white rounded-none flex flex-col lg:flex-row lg:items-stretch overflow-hidden">
            {stages.map((stage, idx) => {
              // Node Active states (Stage 5 and 6 are active signal lime)
              const isActiveNode = idx === 4 || idx === 5;
              
              // Connector Line 1 (Left / Top) colors
              let line1Bg = "bg-slate-200";
              let line1Visible = true;
              if (idx === 0) {
                line1Visible = false;
              } else if (idx === 4 || idx === 5) {
                line1Bg = "bg-[var(--color-riftless-signal)]";
              }

              // Connector Line 2 (Right / Bottom) colors
              let line2Bg = "bg-slate-200";
              let line2Visible = true;
              if (idx === 5) {
                line2Visible = false;
              } else if (idx === 3 || idx === 4) {
                line2Bg = "bg-[var(--color-riftless-signal)]";
              }

              return (
                <div 
                  key={stage.id} 
                  className={`flow-stage-${idx} flex flex-col lg:flex-1 p-5 relative border-b lg:border-b-0 lg:border-r border-slate-100 last:border-b-0 last:border-r-0 hover:bg-slate-50/50 transition-colors`}
                >
                  
                  {/* Integrated Responsive Connector Track */}
                  <div className="relative h-10 lg:h-12 flex items-center justify-start lg:justify-center w-full mb-3 lg:mb-4">
                    {/* Line 1 (Left on desktop, Top on mobile) */}
                    {line1Visible && (
                      <div 
                        className={`flow-line-1 absolute ${line1Bg} 
                          lg:left-0 lg:right-1/2 lg:h-[2px] lg:top-1/2 lg:-translate-y-1/2
                          left-[14px] top-0 bottom-1/2 w-[2px]`} 
                      />
                    )}

                    {/* Line 2 (Right on desktop, Bottom on mobile) */}
                    {line2Visible && (
                      <div 
                        className={`flow-line-2 absolute ${line2Bg} 
                          lg:left-1/2 lg:right-0 lg:h-[2px] lg:top-1/2 lg:-translate-y-1/2
                          left-[14px] top-1/2 bottom-0 w-[2px]`} 
                      />
                    )}

                    {/* Center Node dot/circle */}
                    <div 
                      className={`flow-node relative z-10 w-7 h-7 rounded-full border-2 flex items-center justify-center text-[10px] font-mono font-bold transition-colors lg:mx-auto
                        ${isActiveNode 
                          ? "border-[var(--color-riftless-ink)] bg-[var(--color-riftless-signal)] text-[var(--color-riftless-ink)]" 
                          : "border-slate-200 bg-white text-slate-400"
                        }`}
                    >
                      {stage.num}
                    </div>

                    {/* Compact Label for Mobile next to connector */}
                    <div className="lg:hidden ml-4 flex flex-col justify-center">
                      <span className="text-[11px] font-mono text-slate-400 uppercase tracking-widest block leading-none mb-1">
                        STAGE {stage.num}
                      </span>
                      {idx === 4 && (
                        <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--color-riftless-signal)] font-bold block leading-none">
                          // TARGET VALIDATION
                        </span>
                      )}
                      {idx === 5 && (
                        <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--color-riftless-signal)] font-bold block leading-none">
                          // METADATA COMMIT
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Stage Details */}
                  <div className="flow-stage-details flex-1 flex flex-col justify-between space-y-3 lg:text-center pl-10 lg:pl-0">
                    <div className="space-y-2">
                      
                      {/* Desktop Only Stage Metadata */}
                      <div className="hidden lg:flex flex-col items-center space-y-1">
                        <span className="text-[11px] font-mono text-slate-400 uppercase tracking-widest">
                          STAGE {stage.num}
                        </span>
                        {idx === 4 && (
                          <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--color-riftless-signal)] font-bold">
                            // TARGET VALIDATION
                          </span>
                        )}
                        {idx === 5 && (
                          <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--color-riftless-signal)] font-bold">
                            // METADATA COMMIT
                          </span>
                        )}
                      </div>

                      {/* Heading */}
                      <h3 className="text-sm font-display font-extrabold text-[var(--color-riftless-ink)] uppercase tracking-tight">
                        {stage.title}
                      </h3>

                      {/* Technical Ownership Label (Strictly Monospace) */}
                      <div className="font-mono text-[11px] lg:text-xs text-[var(--color-riftless-graph-gray)] uppercase tracking-wider bg-slate-50 border border-slate-100 p-1.5 leading-tight lg:mx-auto lg:w-full">
                        <span className="text-[10px] text-slate-400 block mb-0.5">// ENGINE:</span>
                        {stage.tech}
                      </div>

                    </div>

                    {/* Description: crisp 2 lines */}
                    <p className="text-xs sm:text-sm font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed lg:px-2">
                      {stage.desc}
                    </p>

                  </div>

                </div>
              );
            })}
          </div>

          {/* Sub-note */}
          <div className="text-center pt-4">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">
              // THE SUCCESS PATHWAY LEADS TO DETERMINISTIC VERIFICATION [SQLGLOT] AND CENTRAL METADATA COMMITS [DATAHUB].
            </span>
          </div>

        </div>
      </section>

      {/* 3. SYSTEM LAYERS SECTION (Dark Technical Documentation) */}
      <section ref={systemLayersRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)]">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12 items-start border-b border-slate-800 pb-10">
            <div className="lg:col-span-8 space-y-4">
              <span className="layers-label text-xs font-mono font-bold tracking-[0.25em] text-slate-400 uppercase block">
                02 / SYSTEM LAYERS
              </span>

              <h2 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-white overflow-hidden">
                <span className="layers-headline-line block">ONE CONTROL PLANE.</span>
                <span className="layers-headline-line block">THREE EXECUTION LAYERS.</span>
              </h2>

              <p className="layers-supporting text-sm sm:text-base font-sans text-slate-400 leading-relaxed max-w-2xl">
                Each layer has a distinct responsibility:
                orchestration coordinates the review,
                intelligence decides what should happen,
                and execution proves the result.
              </p>
            </div>

            <div className="layers-target-model lg:col-span-4 lg:text-right space-y-2 lg:pt-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-none">
                <span className="w-2 h-2 bg-[var(--color-riftless-signal)]" />
                <span className="text-[11px] lg:text-xs font-mono tracking-wider uppercase font-bold text-white">
                  TARGET IMPLEMENTATION MODEL
                </span>
              </div>
              <p className="text-[11px] sm:text-xs font-mono text-slate-500">
                // Specification blueprint under active engineering. Not all integrations are live.
              </p>
            </div>
          </div>

          {/* System Layout: Left Rail + Right Layers */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-stretch">
            
            {/* Left Column: Vertical Control Rail (Desktop Only, becomes top list on Mobile) */}
            <div className="lg:col-span-3 flex flex-col justify-between">
              
              {/* Desktop Rail */}
              <div className="layers-rail-desktop hidden lg:flex flex-col relative pl-6 h-full border-l border-slate-800 py-4 justify-between">
                {/* Active connecting line overlay */}
                <div className="layers-rail-line absolute top-4 left-[-1px] bottom-1/4 w-[2px] bg-[var(--color-riftless-signal)]" />
                
                {/* CHANGE */}
                <div className="layers-rail-step-0 relative space-y-1">
                  <div className="layers-rail-dot absolute left-[-29px] top-1.5 w-2.5 h-2.5 rounded-none bg-[var(--color-riftless-signal)] border border-[var(--color-riftless-ink)]" />
                  <span className="text-[11px] lg:text-xs font-mono text-slate-400 font-bold uppercase tracking-widest block">// STEP 01</span>
                  <h4 className="text-sm font-display font-bold text-white tracking-tight uppercase">CHANGE</h4>
                  <p className="text-xs lg:text-[13px] text-slate-400 leading-snug">Incoming schema triggers analysis</p>
                </div>

                {/* DECIDE */}
                <div className="layers-rail-step-1 relative space-y-1">
                  <div className="layers-rail-dot absolute left-[-29px] top-1.5 w-2.5 h-2.5 rounded-none bg-[var(--color-riftless-signal)] border border-[var(--color-riftless-ink)]" />
                  <span className="text-[11px] lg:text-xs font-mono text-slate-400 font-bold uppercase tracking-widest block">// STEP 02</span>
                  <h4 className="text-sm font-display font-bold text-white tracking-tight uppercase">DECIDE</h4>
                  <p className="text-xs lg:text-[13px] text-slate-400 leading-snug">Evaluate risks and generate fix</p>
                </div>

                {/* PROVE */}
                <div className="layers-rail-step-2 relative space-y-1">
                  <div className="layers-rail-dot absolute left-[-29px] top-1.5 w-2.5 h-2.5 rounded-none bg-[var(--color-riftless-signal)] border border-[var(--color-riftless-ink)]" />
                  <span className="text-[11px] lg:text-xs font-mono text-slate-400 font-bold uppercase tracking-widest block">// STEP 03</span>
                  <h4 className="text-sm font-display font-bold text-white tracking-tight uppercase">PROVE</h4>
                  <p className="text-xs lg:text-[13px] text-slate-400 leading-snug">AST check and local dry-run</p>
                </div>

                {/* PRESERVE */}
                <div className="layers-rail-step-3 relative space-y-1">
                  {/* Lime-colored dot for final success preservation */}
                  <div className="layers-rail-dot absolute left-[-29px] top-1.5 w-2.5 h-2.5 rounded-none bg-[var(--color-riftless-signal)] border border-[var(--color-riftless-ink)]" />
                  <span className="text-[11px] lg:text-xs font-mono text-[var(--color-riftless-signal)] font-bold uppercase tracking-widest block">// STEP 04</span>
                  <h4 className="text-sm font-display font-bold text-[var(--color-riftless-signal)] tracking-tight uppercase">PRESERVE</h4>
                  <p className="text-xs lg:text-[13px] text-slate-300 leading-snug">Commit to central DataHub registry</p>
                </div>
              </div>

              {/* Mobile Rail Sequence */}
              <div className="layers-rail-mobile lg:hidden flex flex-wrap gap-2 pb-6 border-b border-slate-800">
                <div className="layers-mobile-step flex items-center gap-1 px-2.5 py-1 bg-slate-900 border border-slate-800 text-[11px] font-mono">
                  <span className="w-1.5 h-1.5 bg-slate-400" />
                  <span className="text-slate-300">CHANGE</span>
                </div>
                <div className="layers-mobile-step flex items-center gap-1 px-2.5 py-1 bg-slate-900 border border-slate-800 text-[11px] font-mono">
                  <span className="w-1.5 h-1.5 bg-slate-400" />
                  <span className="text-slate-300">DECIDE</span>
                </div>
                <div className="layers-mobile-step flex items-center gap-1 px-2.5 py-1 bg-slate-900 border border-slate-800 text-[11px] font-mono">
                  <span className="w-1.5 h-1.5 bg-slate-400" />
                  <span className="text-slate-300">PROVE</span>
                </div>
                <div className="layers-mobile-step flex items-center gap-1 px-2.5 py-1 bg-slate-900 border border-slate-800 text-[11px] font-mono">
                  <span className="w-1.5 h-1.5 bg-[var(--color-riftless-signal)]" />
                  <span className="text-[var(--color-riftless-signal)] font-bold">PRESERVE</span>
                </div>
              </div>

            </div>

            {/* Right Column: Three Stacked Layers inside One Continuous Boundary */}
            <div className="layers-stack-wrapper lg:col-span-9 flex flex-col border border-slate-800 bg-slate-950/40 rounded-none overflow-hidden">
              
              {/* LAYER 01 */}
              <div className="layer-panel layer-panel-1 p-6 md:p-8 border-b border-slate-800 space-y-4 hover:bg-slate-900/10 transition-colors">
                <div className="layer-heading flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="space-y-1">
                    <span className="text-[10px] lg:text-[11px] font-mono text-slate-500 uppercase tracking-widest block">// COMPONENT LAYER 01</span>
                    <h3 className="text-base font-display font-extrabold text-white tracking-tight uppercase">
                      INGESTION & ORCHESTRATION
                    </h3>
                  </div>
                  <div className="text-[11px] lg:text-xs font-mono text-slate-400 uppercase tracking-widest">
                    [ TRIGGER & FLOW ]
                  </div>
                </div>

                <p className="layer-desc text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
                  Receives a proposed change and coordinates the complete review lifecycle. Manages the parsing execution context and artifacts before passing parameters to decision rules.
                </p>

                {/* Tech Components */}
                <div className="layer-tech pt-2">
                  <span className="text-[10px] lg:text-[11px] font-mono text-slate-500 uppercase tracking-widest block mb-2">// TECHNICAL STACK COMPONENTS</span>
                  <div className="flex flex-wrap gap-1.5">
                    {['GitHub Webhook', 'FastAPI', 'Change Request Parser', 'Run State', 'Artifact Registry'].map((comp) => (
                      <span key={comp} className="layer-tech-badge px-2.5 py-1 bg-slate-900/80 border border-slate-800 text-[11px] sm:text-xs font-mono text-slate-300">
                        {comp}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* LAYER 02 */}
              <div className="layer-panel layer-panel-2 p-6 md:p-8 border-b border-slate-800 space-y-4 hover:bg-slate-900/10 transition-colors">
                <div className="layer-heading flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="space-y-1">
                    <span className="text-[10px] lg:text-[11px] font-mono text-slate-500 uppercase tracking-widest block">// COMPONENT LAYER 02</span>
                    <h3 className="text-base font-display font-extrabold text-white tracking-tight uppercase">
                      CONTEXT & DECISION
                    </h3>
                  </div>
                  <div className="text-[11px] lg:text-xs font-mono text-slate-400 uppercase tracking-widest">
                    [ KNOWLEDGE & RULES ]
                  </div>
                </div>

                <p className="layer-desc text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
                  Builds grounded context, calculates risk, and selects an allowed remediation path. Queried metadata is joined with the prospective diff to run validation and draft a compatible schema.
                </p>

                {/* Tech Components */}
                <div className="layer-tech pt-2">
                  <span className="text-[10px] lg:text-[11px] font-mono text-slate-500 uppercase tracking-widest block mb-2">// TECHNICAL STACK COMPONENTS</span>
                  <div className="flex flex-wrap gap-1.5">
                    {['DataHub GraphQL Client', 'Context Pack Builder', 'Deterministic Risk Engine', 'DeepSeek Remediation Planner', 'Policy Rules'].map((comp) => (
                      <span key={comp} className="layer-tech-badge px-2.5 py-1 bg-slate-900/80 border border-slate-800 text-[11px] sm:text-xs font-mono text-slate-300">
                        {comp}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* LAYER 03 */}
              <div className="layer-panel layer-panel-3 p-6 md:p-8 space-y-4 bg-slate-900/10 hover:bg-slate-900/20 transition-colors relative">
                
                {/* Active Indicator Line overlay to the right */}
                <div className="absolute right-0 top-0 bottom-0 w-[3px] bg-[var(--color-riftless-signal)]" />

                <div className="layer-heading flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="space-y-1">
                    <span className="text-[10px] lg:text-[11px] font-mono text-[var(--color-riftless-signal)] uppercase tracking-widest block font-bold">// COMPONENT LAYER 03 [VERIFIED PATH]</span>
                    <h3 className="text-base font-display font-extrabold text-white tracking-tight uppercase flex items-center gap-2">
                      EXECUTION & EVIDENCE
                      <span className="w-1.5 h-1.5 bg-[var(--color-riftless-signal)] rounded-full" />
                    </h3>
                  </div>
                  <div className="text-[11px] lg:text-xs font-mono text-[var(--color-riftless-signal)] uppercase tracking-widest font-bold">
                    [ VERIFIED OUTCOME ]
                  </div>
                </div>

                <p className="layer-desc text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
                  Executes the repair, records validation evidence, and preserves the decision. Confirms parsing compatibility, compiles execution artifacts, and outputs writeback payloads to update the catalog.
                </p>

                {/* Tech Components with Signal Lime Accent on the final writeback */}
                <div className="layer-tech pt-2">
                  <span className="text-[10px] lg:text-[11px] font-mono text-slate-500 uppercase tracking-widest block mb-2">// TECHNICAL STACK COMPONENTS</span>
                  <div className="flex flex-wrap gap-1.5">
                    {['SQLGlot', 'DuckDB', 'dbt Compile', 'dbt Test'].map((comp) => (
                      <span key={comp} className="layer-tech-badge px-2.5 py-1 bg-slate-900/80 border border-slate-800 text-[11px] sm:text-xs font-mono text-slate-300">
                        {comp}
                      </span>
                    ))}
                    {/* Signal lime for final DataHub Writeback */}
                    <span 
                      style={{ backgroundColor: 'rgba(168, 205, 22, 0.1)', borderColor: 'var(--color-riftless-signal)' }}
                      className="layer-tech-badge px-2.5 py-1 border text-[11px] lg:text-xs font-mono text-[var(--color-riftless-signal)] font-bold uppercase"
                    >
                      DataHub Writeback →
                    </span>
                  </div>
                </div>
              </div>

            </div>

          </div>

          {/* 5. OUTPUT STATEMENT BAR */}
          <div className="layers-output-bar border border-slate-800 bg-slate-950 p-4 md:p-6 text-center rounded-none space-y-2">
            <span className="text-[10px] lg:text-[11px] font-mono text-slate-500 uppercase tracking-widest block">// INTEGRITY TRANSITION CHAIN</span>
            <div className="flex flex-col sm:flex-row sm:items-center justify-center gap-2 md:gap-4 font-mono text-xs sm:text-sm text-slate-300">
              <span className="text-slate-400 font-bold uppercase">PROPOSED CHANGE</span>
              <span className="hidden sm:inline text-slate-600">→</span>
              <span className="text-slate-400 font-bold uppercase">GROUNDED DECISION</span>
              <span className="hidden sm:inline text-slate-600">→</span>
              <span className="text-slate-400 font-bold uppercase">EXECUTABLE EVIDENCE</span>
              <span className="hidden sm:inline text-slate-600 text-[var(--color-riftless-signal)]">→</span>
              <span className="text-[var(--color-riftless-signal)] font-bold uppercase tracking-wider">SHARED CONTEXT</span>
            </div>
          </div>

        </div>
      </section>

      {/* 4. TRUST BOUNDARIES SECTION (Warm Paper Technical Specs) */}
      <section ref={trustBoundariesRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-[var(--color-riftless-paper)] text-[var(--color-riftless-ink)] border-t border-[var(--color-border)]">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12 items-start border-b border-[var(--color-riftless-ink)]/20 pb-10">
            <div className="lg:col-span-8 space-y-4">
              <span className="trust-label text-xs lg:text-sm font-mono font-bold tracking-[0.25em] text-[var(--color-riftless-graph-gray)] uppercase block">
                03 / TRUST BOUNDARIES
              </span>

              <h2 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-ink)] overflow-hidden">
                <span className="trust-headline-line block">AI CAN PROPOSE.</span>
                <span className="trust-headline-line block">ONLY EVIDENCE</span>
                <span className="trust-headline-line block">CAN AUTHORIZE.</span>
              </h2>

              <p className="trust-supporting text-sm sm:text-base font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl">
                DeepSeek may recommend a repair, but deterministic policies,
                isolated execution, and executable validation decide whether
                that repair is allowed to proceed.
              </p>
            </div>

            <div className="trust-target-model lg:col-span-4 lg:text-right space-y-2 lg:pt-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[var(--color-riftless-ink)] border border-[var(--color-riftless-ink)] rounded-none">
                <span className="w-2 h-2 bg-slate-400" />
                <span className="text-[11px] lg:text-xs font-mono tracking-wider uppercase font-bold text-white">
                  TARGET SAFETY MODEL
                </span>
              </div>
              <p className="text-[11px] sm:text-xs font-mono text-[var(--color-riftless-graph-gray)]">
                // Specification blueprint under active engineering. Local simulation mode used for safety.
              </p>
            </div>
          </div>

          {/* Continuous Boundary Block */}
          <div className="border border-[var(--color-riftless-ink)] bg-white/40 rounded-none overflow-hidden">
            
            {/* Top Flow Pipeline */}
            <div className="trust-trajectory-container border-b border-[var(--color-riftless-ink)] bg-[var(--color-riftless-ink)] text-white px-4 py-4 md:px-6">
              <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
                <div className="flex flex-col sm:flex-row sm:items-center gap-x-3 gap-y-1">
                  <span className="text-[11px] font-mono text-slate-400 uppercase tracking-widest block font-bold">
                    // MAIN SYSTEM INTEGRITY TRAJECTORY
                  </span>
                  <span className="text-[10px] font-mono text-[var(--color-riftless-signal)] uppercase tracking-wider font-bold">
                    [ EXAMPLE AUTHORIZED PATH ]
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5 font-mono text-[11px] lg:text-xs text-slate-300">
                  <span className="trajectory-step">CHANGE + CONTEXT</span>
                  <span className="trajectory-arrow text-slate-600">→</span>
                  <span className="trajectory-step">PROPOSED REMEDIATION</span>
                  <span className="trajectory-arrow text-slate-600">→</span>
                  <span className="trajectory-step text-[var(--color-riftless-signal)] font-bold">POLICY GATE</span>
                  <span className="trajectory-arrow text-slate-600">→</span>
                  <span className="trajectory-step text-[var(--color-riftless-signal)] font-bold">ISOLATED VALIDATION</span>
                  <span className="trajectory-arrow text-slate-600">→</span>
                  <span className="trajectory-step text-[var(--color-riftless-signal)] font-bold">TARGET AUTHORIZED WRITEBACK</span>
                </div>
              </div>
            </div>

            {/* 3 Zones Grid (Responsive: vertical on mobile, horizontal on desktop) */}
            <div className="trust-zones-container grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-[var(--color-riftless-ink)]">
              
              {/* ZONE 01: EXTERNAL SYSTEMS */}
              <div className="zone-1 p-6 md:p-8 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-[11px] lg:text-xs font-mono text-slate-400 font-bold uppercase tracking-widest">
                      ZONE 01
                    </span>
                    <span className="text-[11px] font-mono text-slate-500 uppercase">
                      [ UNTRUSTED ]
                    </span>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-lg lg:text-xl font-display font-black text-[var(--color-riftless-ink)] tracking-tight uppercase">
                      EXTERNAL SYSTEMS
                    </h3>
                    <p className="text-xs sm:text-[13px] text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Provides change inputs, metadata context, and remediation proposals.
                    </p>
                  </div>

                  {/* Components */}
                  <div className="space-y-1.5 pt-2">
                    {['GitHub Webhook', 'DataHub Schema', 'DeepSeek API'].map((item) => (
                      <div key={item} className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 font-mono text-xs text-[var(--color-riftless-ink)]">
                        <span className="font-medium">{item}</span>
                        <span className="text-[10px] text-slate-400">UNTRUSTED</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Blocked Direct Write Path */}
                <div className="trust-blocked-path pt-4 border-t border-slate-100 space-y-3">
                  <div className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">// THREAT VECTOR GUARD</div>
                  
                  <div className="flex flex-col gap-2 p-3 bg-slate-50/50 border border-slate-200">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-slate-700">AI PROPOSAL</span>
                      <span className="text-xs font-bold text-[var(--color-riftless-critical)] font-mono flex items-center gap-1">
                        <span className="text-sm font-black">×</span> BLOCKED
                      </span>
                    </div>
                    {/* Short visual blocked path line with × */}
                    <div className="flex items-center gap-2 font-mono text-[10px] text-slate-400 py-1 border-t border-slate-100/50">
                      <span>PROPOSAL</span>
                      <div className="flex-1 h-[2px] bg-slate-300 relative">
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="bg-white px-1.5 text-[var(--color-riftless-critical)] font-black text-xs leading-none">
                            ×
                          </span>
                        </div>
                      </div>
                      <span className="text-slate-500">PRODUCTION WRITE</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* ZONE 02: RIFTLESS CONTROL PLANE */}
              <div className="zone-2 p-6 md:p-8 flex flex-col justify-between space-y-6 bg-slate-50/30">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-200/60 pb-2">
                    <span className="text-[11px] lg:text-xs font-mono text-slate-400 font-bold uppercase tracking-widest">
                      ZONE 02
                    </span>
                    <span className="text-[11px] font-mono text-[var(--color-riftless-ink)] uppercase font-semibold">
                      [ CONTROL PLANE ]
                    </span>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-lg lg:text-xl font-display font-black text-[var(--color-riftless-ink)] tracking-tight uppercase">
                      RIFTLESS CONTROL PLANE
                    </h3>
                    <p className="text-xs sm:text-[13px] text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Owns orchestration and makes the deterministic allow, warn, or block decision.
                    </p>
                  </div>

                  {/* Components Grid */}
                  <div className="grid grid-cols-2 gap-1.5 pt-2">
                    {['Change Parser', 'Context Pack', 'Risk Engine', 'Run State'].map((item) => (
                      <div key={item} className="p-2.5 bg-white border border-slate-200 font-mono text-[11px] text-[var(--color-riftless-ink)]">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Policy Gate Check */}
                <div className="pt-4 border-t border-slate-200 space-y-2">
                  <div className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">// DECISION CORE</div>
                  <div className="flex items-center justify-between p-3 bg-white border border-[var(--color-riftless-ink)] font-mono text-xs">
                    <div className="flex items-center gap-1.5 font-bold">
                      <span className="w-1.5 h-1.5 bg-[var(--color-riftless-signal)]" />
                      <span>POLICY GATE</span>
                    </div>
                    <span className="text-[var(--color-riftless-signal)] font-extrabold uppercase tracking-wide">
                      EXAMPLE PASS →
                    </span>
                  </div>
                </div>
              </div>

              {/* ZONE 03: ISOLATED EXECUTION */}
              <div className="zone-3 p-6 md:p-8 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-[11px] lg:text-xs font-mono text-slate-400 font-bold uppercase tracking-widest">
                      ZONE 03
                    </span>
                    <span 
                      style={{ color: 'var(--color-riftless-signal)', borderColor: 'var(--color-riftless-signal)' }}
                      className="text-[10px] font-mono uppercase font-bold px-2 py-0.5 border"
                    >
                      SECURE SANDBOX
                    </span>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-lg lg:text-xl font-display font-black text-[var(--color-riftless-ink)] tracking-tight uppercase">
                      ISOLATED EXECUTION
                    </h3>
                    <p className="text-xs sm:text-[13px] text-[var(--color-riftless-graph-gray)] leading-relaxed">
                      Executes untrusted repairs locally and produces validation evidence.
                    </p>
                  </div>

                  {/* Components */}
                  <div className="space-y-1.5 pt-2">
                    {['SQLGlot Parse', 'DuckDB Dry Run', 'dbt Compile', 'dbt Test', 'Artifact Evidence'].map((item) => (
                      <div key={item} className="flex items-center justify-between p-2 bg-slate-50 border border-slate-200 font-mono text-[11px] text-[var(--color-riftless-ink)]">
                        <span>{item}</span>
                        <span className="text-[10px] font-bold text-[var(--color-riftless-signal)] uppercase">
                          ✓ VALID
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Validated Evidence */}
                <div className="pt-4 border-t border-slate-100 space-y-2">
                  <div className="text-[10px] font-mono text-slate-400 uppercase tracking-widest flex items-center justify-between">
                    <span>// TRUST VALIDATION</span>
                    <span className="text-[var(--color-riftless-signal)] font-bold">// EXAMPLE AUTHORIZED PATH</span>
                  </div>
                  <div className="flex flex-col gap-1.5 p-2.5 bg-slate-50 border border-[var(--color-riftless-signal)] font-mono text-[11px]">
                    <div className="flex items-center justify-between text-slate-500">
                      <span>EVIDENCE STATE:</span>
                      <span className="text-[var(--color-riftless-signal)] font-bold">TARGET VALIDATED EVIDENCE</span>
                    </div>
                    <div className="flex items-center justify-between border-t border-slate-200/60 pt-1 text-[var(--color-riftless-ink)]">
                      <span className="font-bold">WRITEBACK TARGET:</span>
                      <span className="text-[var(--color-riftless-signal)] font-bold uppercase">TARGET AUTHORIZED WRITEBACK</span>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>

          {/* Guardrails Statement Footer Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-[var(--color-riftless-ink)]/10">
            <div className="guardrail-card border border-slate-200 bg-white/60 p-4 space-y-1.5">
              <span className="text-[10px] font-mono text-slate-400 block">// PROPOSAL LAYER</span>
              <h4 className="text-xs lg:text-sm font-mono font-bold text-[var(--color-riftless-ink)] uppercase">
                DEEPSEEK PROPOSES
              </h4>
              <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                Generates the remediation plan and writes code changes in isolation.
              </p>
            </div>
            <div className="guardrail-card border border-[var(--color-riftless-ink)] bg-white/60 p-4 space-y-1.5">
              <span className="text-[10px] font-mono text-[var(--color-riftless-signal)] font-bold block">// AUTHORIZATION LAYER</span>
              <h4 className="text-xs lg:text-sm font-mono font-bold text-[var(--color-riftless-ink)] uppercase">
                DETERMINISTIC RULES AUTHORIZE
              </h4>
              <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                Applies strict policy engines to ensure the plan satisfies business requirements.
              </p>
            </div>
            <div className="guardrail-card border p-4 space-y-1.5 bg-white/60" style={{ borderColor: 'var(--color-riftless-signal)' }}>
              <span className="text-[10px] font-mono text-[var(--color-riftless-signal)] font-bold block">// PROOF LAYER</span>
              <h4 className="text-xs lg:text-sm font-mono font-bold text-[var(--color-riftless-ink)] uppercase">
                EXECUTABLE TESTS PROVE
              </h4>
              <p className="text-xs text-[var(--color-riftless-graph-gray)] leading-relaxed">
                Runs isolated database simulations (SQLGlot/DuckDB) to verify execution safety.
              </p>
            </div>
          </div>

        </div>
      </section>

      {/* 5. CONTEXT LOOP SECTION (Riftless Ink Technical Specs) */}
      <section ref={contextLoopRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-[var(--color-riftless-ink)] text-white border-t border-slate-800">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12 items-start border-b border-slate-800 pb-10">
            <div className="lg:col-span-8 space-y-4">
              <span className="loop-label text-xs lg:text-sm font-mono font-bold tracking-[0.25em] text-slate-400 uppercase block">
                04 / CONTEXT LOOP
              </span>

              <h2 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-white overflow-hidden">
                <span className="loop-headline-line block">READ THE GRAPH.</span>
                <span className="loop-headline-line block">ACT WITH CONTEXT.</span>
                <span className="loop-headline-line block">WRITE THE DECISION BACK.</span>
              </h2>

              <p className="loop-supporting text-sm sm:text-base font-sans text-slate-400 leading-relaxed max-w-2xl">
                RIFTLESS treats DataHub as shared organizational memory.
                It reads metadata before making a decision, then writes evidence,
                ownership actions, and lifecycle context back after validation.
              </p>
            </div>

            <div className="loop-target-model lg:col-span-4 lg:text-right space-y-2 lg:pt-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-none">
                <span className="w-2 h-2 bg-[var(--color-riftless-signal)]" />
                <span className="text-[11px] lg:text-xs font-mono tracking-wider uppercase font-bold text-white">
                  TARGET DATAHUB INTEGRATION MODEL
                </span>
              </div>
              <p className="text-[11px] sm:text-xs font-mono text-slate-500">
                // Specification blueprint under active engineering. Not a live client-side connection.
              </p>
            </div>
          </div>

          {/* Continuous Loop Diagram Container */}
          <div className="loop-diagram-container border border-slate-800 bg-slate-950/60 rounded-none overflow-hidden">
            
            {/* Top Trajectory Banner */}
            <div className="loop-trajectory-container border-b border-slate-800 bg-slate-900/40 px-4 py-4 md:px-6">
              <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
                <span className="text-[11px] font-mono text-slate-500 uppercase tracking-widest block font-bold">
                  // CLOSED-LOOP LIFECYCLE PATHS
                </span>
                
                {/* Horizontal flow direction labels for desktop & mobile */}
                <div className="flex flex-col md:flex-row gap-4 md:gap-8 font-mono text-[11px] lg:text-xs">
                  {/* READ PATH */}
                  <div className="loop-read-path flex items-center gap-2 text-slate-400">
                    <span className="font-bold text-slate-500 uppercase">READ PATH:</span>
                    <span>DATAHUB GRAPH</span>
                    <span className="text-slate-600">→</span>
                    <span>CONTEXT PACK</span>
                    <span className="text-slate-600">→</span>
                    <span className="text-white font-semibold">GROUNDED DECISION</span>
                  </div>

                  {/* WRITEBACK PATH */}
                  <div className="loop-writeback-path flex items-center gap-2 text-[var(--color-riftless-signal)]">
                    <span className="font-bold text-slate-500 uppercase">WRITEBACK PATH:</span>
                    <span>VALIDATED EVIDENCE</span>
                    <span className="text-slate-400">→</span>
                    <span>DECISION RECORD</span>
                    <span className="text-slate-400">→</span>
                    <span className="font-extrabold">DATAHUB GRAPH</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Loop System Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-slate-800">
              
              {/* PART A: READ CONTEXT (Left) */}
              <div className="part-a p-6 md:p-8 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                    <span className="text-[11px] lg:text-xs font-mono text-slate-500 font-bold uppercase tracking-widest">
                      PART A // INPUT
                    </span>
                    <span className="text-[11px] font-mono text-slate-400 uppercase">
                      [ READ CONTEXT ]
                    </span>
                  </div>

                  <div className="part-a-title space-y-2">
                    <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">SOURCE TARGET</div>
                    <h3 className="text-lg lg:text-xl font-display font-black text-white tracking-tight uppercase">
                      DATAHUB METADATA GRAPH
                    </h3>
                  </div>

                  <p className="text-xs sm:text-[13px] text-slate-400 leading-relaxed">
                    Prior to executing any repair, Riftless queries the organizational catalog to ground decision rules with complete downstream knowledge.
                  </p>

                  {/* Context Inputs Items List */}
                  <div className="space-y-1.5 pt-2">
                    <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">// INGESTED CONTEXT CHANNELS</div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {[
                        'Schema',
                        'Column Lineage',
                        'Query Usage',
                        'Ownership',
                        'Governance Tags',
                        'Quality Signals',
                        'ML Dependencies'
                      ].map((item) => (
                        <div key={item} className="part-a-item p-2 bg-slate-900/60 border border-slate-800 font-mono text-[11px] text-slate-300 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 bg-slate-500" />
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Interface specification */}
                <div className="part-a-client pt-4 border-t border-slate-900 space-y-1">
                  <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest block">// READ CLIENT</span>
                  <div className="p-2.5 bg-slate-900 border border-slate-800 font-mono text-xs text-slate-300 flex items-center justify-between">
                    <span>DataHub GraphQL Client</span>
                    <span className="text-[10px] text-slate-500">GraphQL API</span>
                  </div>
                </div>
              </div>

              {/* PART B: DECIDE & PROVE (Middle - Central Process Node) */}
              <div className="part-b p-6 md:p-8 flex flex-col justify-between space-y-6 bg-slate-900/20">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                    <span className="text-[11px] lg:text-xs font-mono text-slate-500 font-bold uppercase tracking-widest">
                      PART B // PROCESS
                    </span>
                    <span className="text-[11px] font-mono text-[var(--color-riftless-signal)] uppercase font-semibold">
                      [ CENTRAL ENGINE ]
                    </span>
                  </div>

                  <div className="part-b-title space-y-2">
                    <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">ORCHESTRATOR CORE</div>
                    <h3 className="text-lg lg:text-xl font-display font-black text-white tracking-tight uppercase">
                      RIFTLESS REVIEW RUN
                    </h3>
                  </div>

                  <p className="text-xs sm:text-[13px] text-slate-400 leading-relaxed">
                    Evaluates incoming telemetry and metadata inside a deterministic policy sandbox. Compiles dry-run schemas and validates AST rules.
                  </p>

                  {/* Central Process Stages */}
                  <div className="space-y-1.5 pt-2">
                    <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">// INTERNAL FLOW STATE</div>
                    <div className="space-y-1.5">
                      {[
                        { num: '01', name: 'Context Pack Builder' },
                        { num: '02', name: 'Deterministic Risk Engine' },
                        { num: '03', name: 'DeepSeek Remediation Planner' },
                        { num: '04', name: 'SQLGlot / DuckDB / dbt Validation' }
                      ].map((item) => (
                        <div key={item.num} className="part-b-stage p-2.5 bg-slate-900 border border-slate-800 font-mono text-xs text-white flex items-center justify-between">
                          <span className="text-slate-500 font-bold">STATE {item.num}</span>
                          <span className="font-semibold">{item.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Return/Loop Connection Graphic (Desktop arrow to writeback, returning loop back to Read Context conceptually) */}
                <div className="part-b-footer pt-4 border-t border-slate-900 text-center">
                  <div className="inline-flex items-center gap-1.5 font-mono text-[10px] text-[var(--color-riftless-signal)] uppercase font-bold tracking-wide">
                    <span>VALIDATED EVIDENCE</span>
                    <span>→</span>
                    <span>TARGET WRITEBACK</span>
                  </div>
                </div>
              </div>

              {/* PART C: WRITE KNOWLEDGE BACK (Right) */}
              <div className="part-c p-6 md:p-8 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                    <span className="text-[11px] lg:text-xs font-mono text-slate-500 font-bold uppercase tracking-widest">
                      PART C // OUTPUT
                    </span>
                    <span 
                      style={{ color: 'var(--color-riftless-signal)', borderColor: 'var(--color-riftless-signal)' }}
                      className="text-[10px] font-mono uppercase font-bold px-2 py-0.5 border"
                    >
                      TARGET WRITEBACK PATH
                    </span>
                  </div>

                  <div className="part-c-title space-y-2">
                    <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">TARGET DESTINATION</div>
                    <h3 className="text-lg lg:text-xl font-display font-black text-white tracking-tight uppercase">
                      WRITE KNOWLEDGE BACK
                    </h3>
                  </div>

                  <p className="text-xs sm:text-[13px] text-slate-400 leading-relaxed">
                    Preserves structural changes, execution results, and metadata ownership states back into DataHub to update the organizational knowledge graph.
                  </p>

                  {/* Writeback Records List */}
                  <div className="space-y-1.5 pt-2">
                    <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">// MUTATED ENTRIES</div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {[
                        'Risk Tag',
                        'Decision Document',
                        'Deprecation Note',
                        'Owner Action',
                        'Validation Result',
                        'Incident Status'
                      ].map((item) => (
                        <div key={item} className="part-c-item p-2 bg-slate-900 border border-[var(--color-riftless-signal)]/30 font-mono text-[11px] text-[var(--color-riftless-signal)] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 bg-[var(--color-riftless-signal)]" />
                          <span className="font-semibold">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Interface specification */}
                <div className="part-c-client pt-4 border-t border-slate-900 space-y-1">
                  <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest block">// WRITE CLIENT</span>
                  <div className="p-2.5 bg-slate-900 border border-[var(--color-riftless-signal)]/40 font-mono text-xs text-[var(--color-riftless-signal)] flex items-center justify-between">
                    <span>DataHub Metadata Writeback</span>
                    <span className="text-[10px] text-slate-400">REST Schema API</span>
                  </div>
                </div>
              </div>

            </div>

            {/* Continuous Return Loop Graphic (Visualizes return path back to DataHub) */}
            <div className="return-loop-graphic border-t border-slate-800 bg-slate-950/85 px-6 py-6 md:px-8">
              {/* Desktop closed-loop visual rail (hidden on mobile, shown on lg/xl) */}
              <div className="desktop-return-label hidden lg:flex items-center justify-between font-mono text-[10px] text-slate-500 relative pb-2">
                <span className="text-slate-400 uppercase font-bold tracking-widest">// PART A ENTRY (READ)</span>
                <span className="text-slate-600 tracking-[0.2em]">================================================== RETURN LOOP PATH ==================================================</span>
                <span className="text-[var(--color-riftless-signal)] font-bold uppercase tracking-widest">// PART C WRITEBACK (EXIT)</span>
              </div>
              
              {/* Graphic Flow Rail */}
              <div className="desktop-return-rail hidden lg:flex items-center h-5 relative mb-4">
                {/* Gray Left side of path (inside DataHub Graph context) */}
                <div className="w-[35%] h-[2px] bg-slate-700 relative flex items-center">
                  <span className="absolute left-0 text-slate-400 text-xs">◀</span>
                  <div className="w-2 h-2 rounded-full bg-slate-500 absolute left-4" />
                  <span className="absolute left-8 font-mono text-[9px] text-slate-400">RE-ENTERS METADATA GRAPH</span>
                </div>
                
                {/* Mid transition */}
                <div className="w-[15%] h-[2px] bg-slate-800" />
                
                {/* Lime/Signal Right side of path (authorized writeback out) */}
                <div className="w-[50%] h-[2px] bg-[var(--color-riftless-signal)]/60 relative flex items-center justify-end">
                  <span className="absolute right-8 font-mono text-[9px] text-[var(--color-riftless-signal)]">AUTHORIZED WRITEBACK TRANSMISSION</span>
                  <div className="w-2 h-2 rounded-full bg-[var(--color-riftless-signal)] absolute right-4" />
                  <span className="absolute right-0 text-[var(--color-riftless-signal)] text-xs">◀</span>
                </div>
              </div>

              {/* Mobile simplified loop indicator (shown on mobile, hidden on lg/xl) */}
              <div className="mobile-return-rail lg:hidden flex flex-col items-center justify-center gap-1 pb-4 text-center">
                <div className="text-[9px] font-mono text-[var(--color-riftless-signal)] uppercase tracking-widest">// TARGET CLOSED-LOOP FLOW</div>
                <div className="flex items-center gap-2 font-mono text-xs text-slate-400">
                  <span>PART C (WRITE)</span>
                  <span className="text-[var(--color-riftless-signal)]">⤶</span>
                  <span className="text-slate-500">VERTICAL RETURN CONNECTOR</span>
                  <span className="text-slate-400">⤷</span>
                  <span>PART A (READ)</span>
                </div>
              </div>

              {/* Text labels summary */}
              <div className="loop-summary-labels flex flex-col sm:flex-row items-center justify-center gap-3 font-mono text-xs text-slate-400 border-t border-slate-900/60 pt-4">
                <span className="text-[var(--color-riftless-signal)] font-bold">●</span>
                <span className="uppercase text-slate-400 font-bold">TARGET KNOWLEDGE LOOP:</span>
                <span className="text-slate-300">PRESERVED RECORD</span>
                <span className="text-[var(--color-riftless-signal)]">⇉</span>
                <span className="text-slate-300">RE-GROUNDS SUBSEQUENT REVIEW RUNS</span>
                <span className="hidden sm:inline text-slate-600">//</span>
                <span className="text-[var(--color-riftless-signal)] font-bold">CONTEXT PRESERVED FOR FUTURE REVIEWS</span>
              </div>
            </div>

          </div>

          {/* Loop Statement Footer Section */}
          <div className="loop-statement-footer pt-8 border-t border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest block">
                // TARGET ORGANIZATIONAL MEMORY LOOP
              </span>
              <h3 className="text-lg lg:text-xl font-display font-bold text-white uppercase tracking-tight leading-tight">
                THE NEXT REVIEW INHERITS
                <br />
                WHAT THE PREVIOUS REVIEW LEARNED.
              </h3>
            </div>
            
            <p className="text-xs font-mono text-slate-500 max-w-md leading-relaxed md:text-right">
              Every resolved issue, schema change, and rule validation updates the global organizational catalog. As the data graph grows, Riftless deepens its grounded context continuously.
            </p>
          </div>

        </div>
      </section>

      {/* 6. RUN LIFECYCLE SECTION */}
      <section ref={runLifecycleRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-[var(--color-riftless-paper)] text-[var(--color-riftless-ink)] border-t border-[var(--color-border)]">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12 items-start border-b border-[var(--color-riftless-ink)]/20 pb-10">
            <div className="lg:col-span-8 space-y-4">
              <span className="run-lifecycle-label text-xs lg:text-sm font-mono font-bold tracking-[0.25em] text-[var(--color-riftless-graph-gray)] uppercase block">
                05 / RUN LIFECYCLE
              </span>

              <h2 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-ink)] overflow-hidden">
                <span className="run-lifecycle-headline-line block">EVERY CHANGE BECOMES</span>
                <span className="run-lifecycle-headline-line block">AN AUDITABLE RUN.</span>
              </h2>

              <p className="run-lifecycle-supporting text-sm sm:text-base font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl">
                RIFTLESS preserves every decision, artifact, validation result,
                and lifecycle transition inside one traceable review run.
              </p>
            </div>

            <div className="run-lifecycle-target-model lg:col-span-4 lg:text-right space-y-2 lg:pt-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[var(--color-riftless-ink)] border border-[var(--color-riftless-ink)] rounded-none">
                <span className="w-2 h-2 bg-slate-400" />
                <span className="text-[11px] lg:text-xs font-mono tracking-wider uppercase font-bold text-white">
                  TARGET RUN STATE MODEL
                </span>
              </div>
              <p className="text-[11px] sm:text-xs font-mono text-[var(--color-riftless-graph-gray)]">
                // Run state blueprint under active design. Persistence layer mock-free and non-executing in client view.
              </p>
            </div>
          </div>

          {/* Shared Lifecycle Boundary Box */}
          <div className="border border-[var(--color-riftless-ink)] bg-white/40 rounded-none overflow-hidden p-6 md:p-8 space-y-10">
            
            {/* Visual State-Machine Rail */}
            <div className="space-y-6">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-widest">// LIFECYCLE TRACK RAIL</div>
              
              {/* State Machine Container */}
              <div className="relative">
                
                {/* Main Horizontal Rail (Desktop only) */}
                <div className="lifecycle-rail-desktop absolute top-[35px] left-[4%] right-[4%] h-[2px] bg-slate-200 z-0 hidden lg:block" />
                
                {/* Timeline Nodes Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-7 gap-6 lg:gap-4 relative z-10">
                  
                  {/* Step 1: RECEIVED */}
                  <div className="lifecycle-step flex flex-row lg:flex-col items-start gap-4 lg:gap-3">
                    <div className="flex flex-col items-center">
                      <div className="lifecycle-marker w-16 h-16 rounded-none border border-[var(--color-riftless-ink)] bg-white flex items-center justify-center font-mono text-sm font-bold shadow-sm">
                        01
                      </div>
                      {/* Mobile vertical line helper */}
                      <div className="lifecycle-line-mobile w-[2px] h-12 bg-slate-200 lg:hidden" />
                    </div>
                    <div className="lifecycle-info space-y-1 pt-1 lg:pt-0">
                      <h4 className="text-xs lg:text-[13px] font-mono font-extrabold text-[var(--color-riftless-ink)] uppercase">
                        RECEIVED
                      </h4>
                      <p className="text-[11px] text-slate-500 font-mono leading-tight">
                        GitHub Event / Manual Input
                      </p>
                    </div>
                  </div>

                  {/* Step 2: CONTEXT ASSEMBLED */}
                  <div className="lifecycle-step flex flex-row lg:flex-col items-start gap-4 lg:gap-3">
                    <div className="flex flex-col items-center">
                      <div className="lifecycle-marker w-16 h-16 rounded-none border border-[var(--color-riftless-ink)] bg-white flex items-center justify-center font-mono text-sm font-bold shadow-sm">
                        02
                      </div>
                      {/* Mobile vertical line helper */}
                      <div className="lifecycle-line-mobile w-[2px] h-12 bg-slate-200 lg:hidden" />
                    </div>
                    <div className="lifecycle-info space-y-1 pt-1 lg:pt-0">
                      <h4 className="text-xs lg:text-[13px] font-mono font-extrabold text-[var(--color-riftless-ink)] uppercase">
                        CONTEXT ASSEMBLED
                      </h4>
                      <p className="text-[11px] text-slate-500 font-mono leading-tight">
                        DataHub Context Pack
                      </p>
                    </div>
                  </div>

                  {/* Step 3: RISK DECIDED */}
                  <div className="lifecycle-step flex flex-row lg:flex-col items-start gap-4 lg:gap-3">
                    <div className="flex flex-col items-center">
                      <div className="lifecycle-marker w-16 h-16 rounded-none border-2 border-[var(--color-riftless-ink)] bg-slate-50 flex items-center justify-center font-mono text-sm font-black shadow-sm relative">
                        03
                        {/* Small decorative flag */}
                        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[var(--color-riftless-signal)]" />
                      </div>
                      {/* Mobile vertical line helper */}
                      <div className="lifecycle-line-mobile w-[2px] h-12 bg-slate-200 lg:hidden" />
                    </div>
                    <div className="lifecycle-info space-y-1 pt-1 lg:pt-0">
                      <h4 className="text-xs lg:text-[13px] font-mono font-extrabold text-[var(--color-riftless-ink)] uppercase">
                        RISK DECIDED
                      </h4>
                      <p className="text-[11px] text-slate-500 font-mono leading-tight">
                        Deterministic Risk Engine
                      </p>
                    </div>
                  </div>

                  {/* Step 4: REMEDIATION PLANNED */}
                  <div className="lifecycle-step flex flex-row lg:flex-col items-start gap-4 lg:gap-3">
                    <div className="flex flex-col items-center">
                      <div className="lifecycle-marker w-16 h-16 rounded-none border border-[var(--color-riftless-ink)] bg-white flex items-center justify-center font-mono text-sm font-bold shadow-sm">
                        04
                      </div>
                      {/* Mobile vertical line helper */}
                      <div className="lifecycle-line-mobile w-[2px] h-12 bg-slate-200 lg:hidden" />
                    </div>
                    <div className="lifecycle-info space-y-1 pt-1 lg:pt-0">
                      <h4 className="text-xs lg:text-[13px] font-mono font-extrabold text-[var(--color-riftless-ink)] uppercase">
                        REMEDIATION PLANNED
                      </h4>
                      <p className="text-[11px] text-slate-500 font-mono leading-tight">
                        DeepSeek Proposal
                      </p>
                    </div>
                  </div>

                  {/* Step 5: VALIDATING */}
                  <div className="lifecycle-step flex flex-row lg:flex-col items-start gap-4 lg:gap-3">
                    <div className="flex flex-col items-center">
                      <div className="lifecycle-marker w-16 h-16 rounded-none border border-[var(--color-riftless-ink)] bg-white flex items-center justify-center font-mono text-sm font-bold shadow-sm">
                        05
                      </div>
                      {/* Mobile vertical line helper */}
                      <div className="lifecycle-line-mobile w-[2px] h-12 bg-slate-200 lg:hidden" />
                    </div>
                    <div className="lifecycle-info space-y-1 pt-1 lg:pt-0">
                      <h4 className="text-xs lg:text-[13px] font-mono font-extrabold text-[var(--color-riftless-ink)] uppercase">
                        VALIDATING
                      </h4>
                      <p className="text-[11px] text-slate-500 font-mono leading-tight">
                        SQLGlot / DuckDB / dbt
                      </p>
                    </div>
                  </div>

                  {/* Step 6: VALIDATED */}
                  <div className="lifecycle-step flex flex-row lg:flex-col items-start gap-4 lg:gap-3">
                    <div className="flex flex-col items-center">
                      <div className="lifecycle-marker w-16 h-16 rounded-none border-2 border-[var(--color-riftless-signal)] bg-white flex items-center justify-center font-mono text-sm font-extrabold text-[var(--color-riftless-signal)] shadow-sm">
                        06
                      </div>
                      {/* Mobile vertical line helper */}
                      <div className="lifecycle-line-mobile w-[2px] h-12 bg-slate-200 lg:hidden" />
                    </div>
                    <div className="lifecycle-info space-y-1 pt-1 lg:pt-0">
                      <h4 className="text-xs lg:text-[13px] font-mono font-extrabold text-[var(--color-riftless-signal)] uppercase">
                        VALIDATED
                      </h4>
                      <p className="text-[11px] text-slate-500 font-mono leading-tight">
                        Evidence Bundle
                      </p>
                    </div>
                  </div>

                  {/* Step 7: WRITTEN BACK */}
                  <div className="lifecycle-step flex flex-row lg:flex-col items-start gap-4 lg:gap-3">
                    <div className="flex flex-col items-center">
                      <div className="lifecycle-marker w-16 h-16 rounded-none bg-[var(--color-riftless-ink)] text-white flex items-center justify-center font-mono text-sm font-black shadow-sm">
                        07
                      </div>
                    </div>
                    <div className="lifecycle-info space-y-1 pt-1 lg:pt-0">
                      <h4 className="text-xs lg:text-[13px] font-mono font-extrabold text-[var(--color-riftless-ink)] uppercase">
                        WRITTEN BACK
                      </h4>
                      <p className="text-[11px] text-slate-500 font-mono leading-tight">
                        DataHub Metadata Commit
                      </p>
                    </div>
                  </div>

                </div>

              </div>
            </div>

            {/* Controlled Branches & Failure Paths Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pt-6 border-t border-[var(--color-riftless-ink)]/10">
              
              {/* RISK DECIDED Controlled Branches */}
              <div className="risk-branch-section space-y-4">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">// BRANCH FROM STATE 03: RISK DECIDED</span>
                </div>

                <div className="border border-[var(--color-riftless-ink)] bg-white/70 p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-slate-700">DETERMINISTIC EVALUATION PATHS</span>
                    <span className="text-[10px] font-mono text-slate-400">[ CONTINUOUS GATEWAY ]</span>
                  </div>

                  <div className="space-y-3 font-mono text-xs">
                    
                    {/* ALLOW Path */}
                    <div className="risk-branch-allow flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 bg-slate-50 border-l-4 border-[var(--color-riftless-signal)]">
                      <div className="flex items-center gap-2">
                        <span className="text-[var(--color-riftless-signal)] font-black">●</span>
                        <span className="font-extrabold text-[var(--color-riftless-signal)]">ALLOW</span>
                        <span className="text-slate-400">→</span>
                        <span className="text-[var(--color-riftless-ink)] font-semibold">REMEDIATION PLANNED</span>
                      </div>
                      <span className="text-[10px] text-[var(--color-riftless-signal)] font-bold uppercase tracking-wider">
                        TARGET ALLOW PATH
                      </span>
                    </div>

                    {/* WARN Path */}
                    <div className="risk-branch-warn flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 bg-slate-50 border-l-4 border-amber-500">
                      <div className="flex items-center gap-2">
                        <span className="text-amber-500 font-black">▲</span>
                        <span className="font-extrabold text-amber-600">WARN</span>
                        <span className="text-slate-400">→</span>
                        <span className="text-slate-700 font-medium">HUMAN REVIEW</span>
                      </div>
                      <span className="text-[10px] text-amber-600 font-bold uppercase tracking-wider">
                        TARGET HUMAN REVIEW
                      </span>
                    </div>

                    {/* BLOCK Path */}
                    <div className="risk-branch-block flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 bg-slate-50 border-l-4 border-[var(--color-riftless-critical)]">
                      <div className="flex items-center gap-2">
                        <span className="text-[var(--color-riftless-critical)] font-black">×</span>
                        <span className="font-extrabold text-[var(--color-riftless-critical)]">BLOCK</span>
                        <span className="text-slate-400">→</span>
                        <span className="text-slate-500 font-medium">RUN CLOSED</span>
                      </div>
                      <span className="text-[10px] text-[var(--color-riftless-critical)] font-bold uppercase tracking-wider">
                        TARGET CLOSED STATE
                      </span>
                    </div>

                  </div>
                </div>
              </div>

              {/* VALIDATING Failure Path */}
              <div className="failure-path-section space-y-4">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">// FAILURE FROM STATE 05: VALIDATING</span>
                </div>

                <div className="failure-path-box border border-dashed border-[var(--color-riftless-critical)]/40 bg-white/70 p-5 flex flex-col justify-between space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-slate-700">UNEXPECTED TEST REGRESSION</span>
                      <span className="text-xs font-bold text-[var(--color-riftless-critical)] font-mono">
                        × REGRESSION BLOCK
                      </span>
                    </div>

                    {/* Block Path */}
                    <div className="p-3 bg-red-50/50 border border-[var(--color-riftless-critical)]/20 font-mono text-xs space-y-2">
                      <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 text-[var(--color-riftless-critical)] font-extrabold">
                        <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">EXAMPLE FAILURE PATH:</span>
                        <div className="flex items-center gap-1.5">
                          <span>VALIDATION FAILED</span>
                          <span>→</span>
                          <span>ARTIFACTS PRESERVED</span>
                          <span>→</span>
                          <span>RUN CLOSED</span>
                        </div>
                      </div>
                      <p className="text-[11px] text-slate-500 leading-relaxed font-mono font-normal">
                        If SQLGlot fails to parse or DuckDB reveals a validation mismatch, writeback is blocked immediately.
                      </p>
                    </div>
                  </div>

                  <div className="failure-statement pt-2 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <span className="text-[11px] font-mono font-bold text-[var(--color-riftless-critical)] uppercase tracking-wider">
                      FAILED EXECUTION DOES NOT ERASE EVIDENCE.
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      [ AUDIT TRAIL RETAINED ]
                    </span>
                  </div>
                </div>
              </div>

            </div>

            {/* Artifact Trail Visualization */}
            <div className="artifact-trail-section pt-6 border-t border-[var(--color-riftless-ink)]/10 space-y-4">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-widest">// RUN ARTIFACT TRAIL (EVIDENCE CHAIN)</div>
              
              <div className="artifact-banner bg-slate-50 border border-slate-200/80 px-4 py-6 md:px-6">
                <div className="artifact-row flex flex-col lg:flex-row lg:items-center justify-between gap-4 font-mono text-xs">
                  <span className="artifact-header text-[10px] text-slate-400 font-bold uppercase tracking-wider block lg:mb-0 mb-1">
                    PRODUCED ARTIFACT FLOW:
                  </span>
                  
                  {/* The trace line representing continuous lifecycle sequence of artifacts */}
                  <div className="artifact-trace-container flex-1 flex flex-wrap items-center gap-x-2 gap-y-1.5 text-slate-500">
                    <span className="artifact-marker-item text-[var(--color-riftless-ink)] font-bold">INPUT DIFF</span>
                    <span className="artifact-separator">—</span>
                    <span className="artifact-marker-item text-[var(--color-riftless-ink)] font-bold">CONTEXT PACK</span>
                    <span className="artifact-separator">—</span>
                    <span className="artifact-marker-item text-[var(--color-riftless-ink)] font-bold">RISK DECISION</span>
                    <span className="artifact-separator">—</span>
                    <span className="artifact-marker-item text-[var(--color-riftless-ink)] font-bold">GENERATED PATCH</span>
                    <span className="artifact-separator">—</span>
                    <span className="artifact-marker-item text-[var(--color-riftless-ink)] font-bold">VALIDATION LOG</span>
                    <span className="artifact-separator">—</span>
                    <span className="artifact-marker-item text-[var(--color-riftless-signal)] font-bold uppercase">WRITEBACK RECORD</span>
                  </div>

                  <span className="artifact-badge text-[10px] bg-slate-200/60 text-slate-600 px-2.5 py-1 font-bold uppercase">
                    TARGET TRACEABLE CHAIN
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* F2.6 — Architecture Data & Artifact Contracts */}
      <section ref={contractModelRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-[var(--color-riftless-ink)] text-slate-200 border-t border-slate-800">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12 items-start border-b border-slate-800 pb-10">
            <div className="lg:col-span-8 space-y-4">
              <span className="contract-model-label text-xs lg:text-sm font-mono font-bold tracking-[0.25em] text-slate-500 uppercase block">
                06 / CONTRACT MODEL
              </span>

              <h2 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-white overflow-hidden">
                <span className="contract-model-headline-line block">EVERY STAGE SPEAKS</span>
                <span className="contract-model-headline-line block">IN TYPED ARTIFACTS.</span>
              </h2>

              <p className="contract-model-supporting text-sm sm:text-base font-sans text-slate-400 leading-relaxed max-w-2xl">
                RIFTLESS passes explicit, inspectable contracts between context,
                decision, remediation, validation, and writeback stages.
              </p>
            </div>

            <div className="contract-model-target-model lg:col-span-4 lg:text-right space-y-2 lg:pt-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-none">
                <span className="w-2 h-2 bg-[var(--color-riftless-signal)]" />
                <span className="text-[11px] lg:text-xs font-mono tracking-wider uppercase font-bold text-slate-300">
                  TARGET DATA CONTRACT MODEL
                </span>
              </div>
              <p className="text-[11px] sm:text-xs font-mono text-slate-500">
                // Conceptual specifications defining compile-time data integrity. Schema backend not live.
              </p>
            </div>
          </div>

          {/* Shared Technical Boundary Box */}
          <div className="border border-slate-800 bg-slate-950/40 rounded-none p-6 md:p-8 space-y-10">
            
            {/* Artifact Pipeline Header / Track */}
            <div className="flex items-center justify-between font-mono text-[10px] text-slate-500 uppercase tracking-widest pb-2 border-b border-slate-900/60">
              <span>// PIPELINE CONTRACT STREAM</span>
              <span className="hidden sm:inline">DIRECTIONAL ARTIFACT FLOW</span>
            </div>

            {/* Pipeline Stream Rail Graphic & Cards Grid */}
            <div className="relative border border-slate-800 bg-slate-950/20 overflow-hidden rounded-none">
              
              {/* Continuous Connected Contract Rail - Desktop visual guide line */}
              <div className="contract-rail-desktop absolute top-[80px] left-[8%] right-[8%] h-[1px] bg-slate-800/80 z-0 hidden lg:block" />
              
              {/* Signal Lime connector path on desktop (from middle of col 4 to end of col 6) */}
              <div className="contract-rail-desktop-success absolute top-[80px] left-[58%] right-[8%] h-[1px] bg-[var(--color-riftless-signal)] z-10 hidden lg:block" />

              {/* Continuous Vertical Spine - Mobile only */}
              <div className="contract-spine-mobile absolute top-10 bottom-10 left-[27px] w-[1px] bg-slate-800/60 z-0 lg:hidden" />
              {/* Signal Lime vertical spine overlay for mobile (from col 5 and 6) */}
              <div className="contract-spine-mobile-success absolute top-[68%] bottom-10 left-[27px] w-[1px] bg-[var(--color-riftless-signal)] z-10 lg:hidden" />

              {/* Pipeline Grid (6 columns) */}
              <div className="grid grid-cols-1 lg:grid-cols-6 divide-y lg:divide-y-0 lg:divide-x divide-slate-800/80 relative z-20">
                
                {/* 1. CHANGE REQUEST */}
                <div className="contract-block relative pl-12 lg:pl-6 pt-5 pb-5 lg:pt-6 lg:pb-6 pr-5 flex flex-col justify-between h-full min-h-[220px] lg:min-h-[260px] space-y-4">
                  {/* Rail Node Dot absolute positioning */}
                  <div className="contract-marker absolute left-[21px] top-[25px] lg:left-6 lg:top-[74px] z-20">
                    <div className="w-3 h-3 rounded-full border-2 border-slate-700 bg-slate-950" />
                  </div>
                  
                  <div className="space-y-4">
                    {/* Ownership Label */}
                    <div className="contract-ownership flex items-center justify-between">
                      <span className="text-[9px] font-mono font-bold tracking-widest text-slate-500 uppercase">
                        INGESTION
                      </span>
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-600 hidden lg:block" />
                    </div>

                    {/* Elegant spacing gap for the desktop rail */}
                    <div className="hidden lg:block h-8" />

                    {/* Contract Title */}
                    <div className="contract-heading">
                      <h4 className="text-xs font-mono font-extrabold text-white uppercase tracking-tight">
                        CHANGE REQUEST
                      </h4>
                      <div className="h-[1px] w-full bg-slate-800/60 mt-1.5" />
                    </div>
                    {/* Monospace Fields */}
                    <ul className="contract-fields-list font-mono text-[11px] text-slate-400 space-y-1">
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> source</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> repository</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> ref</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> changed_files</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> sql_diff</li>
                    </ul>
                  </div>
                  {/* Flow Arrow (Mobile helper vs Desktop helper) */}
                  <div className="contract-flow-arrow pt-2 flex justify-end font-mono text-[10px] text-slate-600">
                    <span className="lg:hidden">↓ NEXT</span>
                    <span className="hidden lg:inline">→</span>
                  </div>
                </div>

                {/* 2. CONTEXT PACK */}
                <div className="contract-block relative pl-12 lg:pl-6 pt-5 pb-5 lg:pt-6 lg:pb-6 pr-5 flex flex-col justify-between h-full min-h-[220px] lg:min-h-[260px] space-y-4">
                  {/* Rail Node Dot */}
                  <div className="contract-marker absolute left-[21px] top-[25px] lg:left-6 lg:top-[74px] z-20">
                    <div className="w-3 h-3 rounded-full border-2 border-slate-700 bg-slate-950" />
                  </div>

                  <div className="space-y-4">
                    {/* Ownership Label */}
                    <div className="contract-ownership flex items-center justify-between">
                      <span className="text-[9px] font-mono font-bold tracking-widest text-slate-500 uppercase">
                        CONTEXT
                      </span>
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-600 hidden lg:block" />
                    </div>

                    <div className="hidden lg:block h-8" />

                    {/* Contract Title */}
                    <div className="contract-heading">
                      <h4 className="text-xs font-mono font-extrabold text-white uppercase tracking-tight">
                        CONTEXT PACK
                      </h4>
                      <div className="h-[1px] w-full bg-slate-800/60 mt-1.5" />
                    </div>
                    {/* Monospace Fields */}
                    <ul className="contract-fields-list font-mono text-[11px] text-slate-400 space-y-1">
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> schema</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> column_lineage</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> query_usage</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> ownership</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> governance</li>
                    </ul>
                  </div>
                  {/* Flow Arrow */}
                  <div className="contract-flow-arrow pt-2 flex justify-end font-mono text-[10px] text-slate-600">
                    <span className="lg:hidden">↓ NEXT</span>
                    <span className="hidden lg:inline">→</span>
                  </div>
                </div>

                {/* 3. RISK DECISION */}
                <div className="contract-block relative pl-12 lg:pl-6 pt-5 pb-5 lg:pt-6 lg:pb-6 pr-5 flex flex-col justify-between h-full min-h-[220px] lg:min-h-[260px] space-y-4">
                  {/* Rail Node Dot */}
                  <div className="contract-marker absolute left-[21px] top-[25px] lg:left-6 lg:top-[74px] z-20">
                    <div className="w-3 h-3 rounded-full border-2 border-slate-700 bg-slate-950" />
                  </div>

                  <div className="space-y-4">
                    {/* Ownership Label */}
                    <div className="contract-ownership flex items-center justify-between">
                      <span className="text-[9px] font-mono font-bold tracking-widest text-slate-500 uppercase">
                        DETERMINISTIC
                      </span>
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-600 hidden lg:block" />
                    </div>

                    <div className="hidden lg:block h-8" />

                    {/* Contract Title */}
                    <div className="contract-heading">
                      <h4 className="text-xs font-mono font-extrabold text-white uppercase tracking-tight">
                        RISK DECISION
                      </h4>
                      <div className="h-[1px] w-full bg-slate-800/60 mt-1.5" />
                    </div>
                    {/* Monospace Fields */}
                    <ul className="contract-fields-list font-mono text-[11px] text-slate-400 space-y-1">
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> level</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> reasons</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> impacted_assets</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> policy_result</li>
                    </ul>
                  </div>
                  {/* Flow Arrow */}
                  <div className="contract-flow-arrow pt-2 flex justify-end font-mono text-[10px] text-slate-600">
                    <span className="lg:hidden">↓ NEXT</span>
                    <span className="hidden lg:inline">→</span>
                  </div>
                </div>

                {/* 4. REMEDIATION PLAN */}
                <div className="contract-block relative pl-12 lg:pl-6 pt-5 pb-5 lg:pt-6 lg:pb-6 pr-5 flex flex-col justify-between h-full min-h-[220px] lg:min-h-[260px] space-y-4">
                  {/* Rail Node Dot */}
                  <div className="contract-marker absolute left-[21px] top-[25px] lg:left-6 lg:top-[74px] z-20">
                    <div className="w-3 h-3 rounded-full border-2 border-slate-700 bg-slate-950" />
                  </div>

                  <div className="space-y-4">
                    {/* Ownership Label */}
                    <div className="contract-ownership flex items-center justify-between">
                      <span className="text-[9px] font-mono font-bold tracking-widest text-slate-500 uppercase">
                        AI-ASSISTED
                      </span>
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-600 hidden lg:block" />
                    </div>

                    <div className="hidden lg:block h-8" />

                    {/* Contract Title */}
                    <div className="contract-heading">
                      <h4 className="text-xs font-mono font-extrabold text-white uppercase tracking-tight">
                        REMEDIATION PLAN
                      </h4>
                      <div className="h-[1px] w-full bg-slate-800/60 mt-1.5" />
                    </div>
                    {/* Monospace Fields */}
                    <ul className="contract-fields-list font-mono text-[11px] text-slate-400 space-y-1">
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> patch</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> compatibility_strategy</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> rollback_plan</li>
                      <li className="contract-field-item"><span className="text-slate-600">▪</span> deprecation_notes</li>
                    </ul>
                  </div>
                  {/* Flow Arrow */}
                  <div className="contract-flow-arrow pt-2 flex justify-end font-mono text-[10px] text-[var(--color-riftless-signal)] font-bold">
                    <span className="lg:hidden">↓ AUTHORIZED FLOW</span>
                    <span className="hidden lg:inline">→</span>
                  </div>
                </div>

                {/* 5. VALIDATION BUNDLE (Signal Lime highlight & border color) */}
                <div className="contract-block relative pl-12 lg:pl-6 pt-5 pb-5 lg:pt-6 lg:pb-6 pr-5 flex flex-col justify-between h-full min-h-[220px] lg:min-h-[260px] space-y-4 bg-[var(--color-riftless-signal)]/[0.02] shadow-[inset_0_0_15px_rgba(168,205,22,0.02)]">
                  {/* Rail Node Dot - Signal Lime */}
                  <div className="contract-marker absolute left-[21px] top-[25px] lg:left-6 lg:top-[74px] z-20">
                    <div className="w-3 h-3 rounded-full border-2 border-[var(--color-riftless-signal)] bg-[var(--color-riftless-signal)] shadow-[0_0_8px_rgba(168,205,22,0.5)]" />
                  </div>

                  <div className="space-y-4">
                    {/* Ownership Label */}
                    <div className="contract-ownership flex items-center justify-between">
                      <span className="text-[9px] font-mono font-bold tracking-widest text-[var(--color-riftless-signal)] uppercase">
                        EXECUTION
                      </span>
                      <span className="w-2 h-2 rounded-full bg-[var(--color-riftless-signal)] hidden lg:block" />
                    </div>

                    <div className="hidden lg:block h-8" />

                    {/* Contract Title */}
                    <div className="contract-heading">
                      <h4 className="text-xs font-mono font-extrabold text-[var(--color-riftless-signal)] uppercase tracking-tight">
                        VALIDATION BUNDLE
                      </h4>
                      <div className="h-[1px] w-full bg-[var(--color-riftless-signal)]/30 mt-1.5" />
                    </div>
                    {/* Monospace Fields */}
                    <ul className="contract-fields-list font-mono text-[11px] text-slate-300 space-y-1">
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> parse_result</li>
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> execution_result</li>
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> compile_result</li>
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> test_result</li>
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> artifact_refs</li>
                    </ul>
                  </div>
                  {/* Flow Arrow */}
                  <div className="contract-flow-arrow pt-2 flex justify-end font-mono text-[10px] text-[var(--color-riftless-signal)] font-bold">
                    <span className="lg:hidden">↓ AUTHORIZED FLOW</span>
                    <span className="hidden lg:inline">→</span>
                  </div>
                </div>

                {/* 6. WRITEBACK RECORD (Signal Lime highlight & border color) */}
                <div className="contract-block relative pl-12 lg:pl-6 pt-5 pb-5 lg:pt-6 lg:pb-6 pr-5 flex flex-col justify-between h-full min-h-[220px] lg:min-h-[260px] space-y-4 bg-[var(--color-riftless-signal)]/[0.02] shadow-[inset_0_0_15px_rgba(168,205,22,0.02)]">
                  {/* Rail Node Dot - Signal Lime */}
                  <div className="contract-marker absolute left-[21px] top-[25px] lg:left-6 lg:top-[74px] z-20">
                    <div className="w-3 h-3 rounded-full border-2 border-[var(--color-riftless-signal)] bg-[var(--color-riftless-signal)] shadow-[0_0_8px_rgba(168,205,22,0.5)]" />
                  </div>

                  <div className="space-y-4">
                    {/* Ownership Label */}
                    <div className="contract-ownership flex items-center justify-between">
                      <span className="text-[9px] font-mono font-bold tracking-widest text-[var(--color-riftless-signal)] uppercase">
                        METADATA
                      </span>
                      <span className="w-2 h-2 rounded-full bg-[var(--color-riftless-signal)] hidden lg:block" />
                    </div>

                    <div className="hidden lg:block h-8" />

                    {/* Contract Title */}
                    <div className="contract-heading">
                      <h4 className="text-xs font-mono font-extrabold text-[var(--color-riftless-signal)] uppercase tracking-tight">
                        WRITEBACK RECORD
                      </h4>
                      <div className="h-[1px] w-full bg-[var(--color-riftless-signal)]/30 mt-1.5" />
                    </div>
                    {/* Monospace Fields */}
                    <ul className="contract-fields-list font-mono text-[11px] text-slate-300 space-y-1">
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> risk_tag</li>
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> decision_document</li>
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> owner_action</li>
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> validation_result</li>
                      <li className="contract-field-item"><span className="text-[var(--color-riftless-signal)]">✔</span> incident_status</li>
                    </ul>
                  </div>
                  {/* Final Indicator */}
                  <div className="contract-flow-arrow pt-2 flex justify-end font-mono text-[10px] text-[var(--color-riftless-signal)] font-extrabold uppercase">
                    COMMIT
                  </div>
                </div>

              </div>

            </div>

            {/* Middle Row: SECRETS Guardrail Redaction Boundary */}
            <div className="redaction-boundary-row pt-6 border-t border-slate-900 flex justify-center">
              <div className="redaction-boundary-box w-full max-w-xl border border-slate-800 bg-slate-950/80 px-4 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                
                {/* Redaction Guardrail */}
                <div className="redaction-element flex items-center gap-3 font-mono text-xs text-slate-400">
                  <span className="redaction-secrets-label text-[10px] font-bold bg-slate-800 px-2 py-0.5 uppercase tracking-wider">SECRETS</span>
                  <span className="redaction-cross text-[var(--color-riftless-critical)] font-black text-sm">×</span>
                  <span className="redaction-connector text-[var(--color-riftless-critical)] font-bold font-mono">—⊘—</span>
                  <span className="redaction-context-label text-slate-300">MODEL CONTEXT</span>
                </div>

                <div className="redaction-target-boundary redaction-element flex items-center gap-2 font-mono text-[11px]">
                  <span className="text-slate-500 uppercase tracking-wider font-bold">TARGET REDACTION BOUNDARY:</span>
                  <span className="text-[var(--color-riftless-critical)] font-extrabold">FORCE REDACTED</span>
                </div>

              </div>
            </div>

            {/* Bottom Row: Invariant Statement */}
            <div className="invariants-row pt-6 border-t border-slate-900/60">
              <div className="py-4 bg-slate-950 border border-slate-900 text-center">
                <div className="flex flex-col md:flex-row items-center justify-center gap-2 md:gap-6 font-mono text-xs tracking-wider text-slate-400">
                  <div className="invariants-item flex items-center gap-2">
                    <span className="text-[var(--color-riftless-signal)]">■</span>
                    <span className="font-extrabold text-slate-200">INPUTS IMMUTABLE</span>
                  </div>
                  <span className="invariants-item text-slate-800 hidden md:inline">/</span>
                  <div className="invariants-item flex items-center gap-2">
                    <span className="text-[var(--color-riftless-signal)]">■</span>
                    <span className="font-extrabold text-slate-200">DECISIONS EXPLAINABLE</span>
                  </div>
                  <span className="invariants-item text-slate-800 hidden md:inline">/</span>
                  <div className="invariants-item flex items-center gap-2">
                    <span className="text-[var(--color-riftless-signal)]">■</span>
                    <span className="font-extrabold text-slate-200">EVIDENCE ADDRESSABLE</span>
                  </div>
                  <span className="invariants-item text-slate-800 hidden md:inline">/</span>
                  <div className="invariants-item flex items-center gap-2">
                    <span className="text-[var(--color-riftless-signal)]">■</span>
                    <span className="font-extrabold text-slate-200">WRITEBACK VERSIONED</span>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* F2.7 — Architecture Deployment Topology */}
      <section ref={deploymentTopologyRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-[var(--color-riftless-paper)] text-[var(--color-riftless-ink)] border-t border-slate-300">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12 items-start border-b border-slate-300 pb-10">
            <div className="lg:col-span-8 space-y-4">
              <span className="topo-label text-xs lg:text-sm font-mono font-bold tracking-[0.25em] text-[var(--color-riftless-graph-gray)] uppercase block">
                07 / DEPLOYMENT TOPOLOGY
              </span>
              
              <h2 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-ink)] overflow-hidden">
                <span className="topo-headline-line block">ONE REVIEW RUN.</span>
                <span className="topo-headline-line block">CLEAR EXECUTION</span>
                <span className="topo-headline-line block">BOUNDARIES.</span>
              </h2>

              <p className="topo-supporting text-sm sm:text-base font-sans text-[var(--color-riftless-graph-gray)] leading-relaxed max-w-2xl">
                RIFTLESS separates orchestration, external context, AI-assisted planning, and isolated validation into explicit deployment boundaries.
              </p>
            </div>

            <div className="topo-target-model lg:col-span-4 lg:text-right space-y-2 lg:pt-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-300 rounded-none">
                <span className="w-2 h-2 bg-[var(--color-riftless-signal)]" />
                <span className="text-[11px] lg:text-xs font-mono tracking-wider uppercase font-bold text-[var(--color-riftless-ink)]">
                  TARGET DEPLOYMENT MODEL
                </span>
              </div>
              <p className="text-[11px] sm:text-xs font-mono text-[var(--color-riftless-graph-gray)]">
                // Conceptual deployment topology specifications. Infrastructure not live or deployed.
              </p>
            </div>
          </div>

          {/* Shared Topology Canvas */}
          <div className="border border-slate-300 bg-white rounded-none p-6 md:p-8 space-y-10">
            
            {/* Diagram Header */}
            <div className="flex items-center justify-between font-mono text-[10px] text-[var(--color-riftless-graph-gray)] uppercase tracking-widest pb-2 border-b border-slate-100">
              <span>// SYSTEM TOPOLOGY GRAPH</span>
              <span className="hidden sm:inline">DATA ISOLATION BOUNDARIES</span>
            </div>

            {/* Topology Grid: Single unified border container with interior dividers */}
            <div className="relative border border-slate-300 rounded-none bg-slate-50/50 grid grid-cols-1 lg:grid-cols-4 divide-y lg:divide-y-0 lg:divide-x divide-slate-300 overflow-hidden">
              
              {/* Continuous connector paths spanning across the container background */}
              {/* Desktop horizontal dashed line */}
              <div className="topo-rail-desktop hidden lg:block absolute top-[180px] left-8 right-8 h-[2px] border-t-2 border-dashed border-slate-300/80 z-0" />
              {/* Mobile vertical dashed spine down the left side */}
              <div className="topo-spine-mobile lg:hidden absolute left-[32px] top-6 bottom-6 w-[2px] border-l-2 border-dashed border-slate-300/80 z-0" />

              {/* A. CHANGE SOURCE */}
              <div className="topo-col relative z-10 pt-16 px-6 pb-6 flex flex-col justify-between min-h-[380px] bg-slate-50/30">
                
                {/* Header boundary label */}
                <div className="topo-col-header absolute top-0 left-0 right-0 bg-slate-100 text-slate-500 text-[10px] font-mono tracking-widest py-2 px-4 uppercase font-bold text-center border-b border-slate-200">
                  01 / CHANGE SOURCE
                </div>

                <div className="topo-col-body space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                      INGESTION RANGE
                    </span>
                    <span className="topo-col-dot w-2.5 h-2.5 rounded-full bg-slate-300 relative z-20" />
                  </div>

                  <div className="space-y-3">
                    <div className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                      // COMPONENTS:
                    </div>
                    <ul className="space-y-2 relative z-20">
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ GitHub App / Webhook
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ Pull Request
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ SQL / dbt Changes
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="topo-col-resp pt-4 border-t border-slate-200 mt-6 bg-inherit relative z-20">
                  <div className="text-[11px] font-mono text-slate-500 uppercase tracking-tight font-bold mb-1">
                    RESPONSIBILITY:
                  </div>
                  <p className="text-[13px] font-sans text-slate-700 leading-snug">
                    Submits the proposed change and repository context.
                  </p>
                </div>
              </div>

              {/* B. RIFTLESS CONTROL PLANE (CONTROL PLANE BOUNDARY) */}
              <div className="topo-col relative z-10 pt-16 px-6 pb-6 flex flex-col justify-between min-h-[380px] bg-white">
                
                {/* Header boundary label */}
                <div className="topo-col-header absolute top-0 left-0 right-0 bg-slate-900 text-white text-[10px] font-mono tracking-widest py-2 px-4 uppercase font-bold text-center border-b border-slate-950">
                  02 / CONTROL PLANE BOUNDARY
                </div>

                <div className="topo-col-body space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-[var(--color-riftless-graph-gray)] uppercase tracking-wider">
                      ORCHESTRATION
                    </span>
                    <span className="topo-col-dot w-2.5 h-2.5 rounded-full bg-slate-400 relative z-20" />
                  </div>

                  <div className="space-y-3">
                    <div className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                      // COMPONENTS:
                    </div>
                    <ul className="space-y-2 relative z-20">
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ FastAPI Orchestrator <span className="text-[10px] text-slate-400 font-normal block mt-0.5">// API Service</span>
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ Change Parser
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ Run State <span className="text-[10px] text-slate-400 font-normal block mt-0.5">// Run State Store</span>
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ Policy Engine
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ Artifact Registry <span className="text-[10px] text-slate-400 font-normal block mt-0.5">// Artifact Store</span>
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="topo-col-resp pt-4 border-t border-slate-200 mt-6 bg-inherit relative z-20">
                  <div className="text-[11px] font-mono text-slate-500 uppercase tracking-tight font-bold mb-1">
                    RESPONSIBILITY:
                  </div>
                  <p className="text-[13px] font-sans text-slate-700 leading-snug">
                    Coordinates the review and owns deterministic decisions.
                  </p>
                </div>
              </div>

              {/* C. ISOLATED VALIDATION WORKER (ISOLATED EXECUTION BOUNDARY) */}
              <div className="topo-col relative z-10 pt-16 px-6 pb-6 flex flex-col justify-between min-h-[380px] bg-slate-50/10">
                
                {/* Header boundary label */}
                <div className="topo-col-header absolute top-0 left-0 right-0 bg-slate-700 text-white text-[10px] font-mono tracking-widest py-2 px-4 uppercase font-bold text-center border-b border-slate-800">
                  03 / ISOLATED EXECUTION BOUNDARY
                </div>

                <div className="topo-col-body space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                      SANITIZED RUN
                    </span>
                    <span className="topo-col-dot w-2.5 h-2.5 rounded-full bg-[var(--color-riftless-signal)] shadow-[0_0_8px_rgba(168,205,22,0.6)] relative z-20 animate-pulse" />
                  </div>

                  <div className="space-y-3">
                    <div className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                      // COMPONENTS:
                    </div>
                    <ul className="space-y-2 relative z-20">
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ SQLGlot
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ DuckDB
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ dbt Compile
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ dbt Test
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ Evidence Builder <span className="text-[10px] text-slate-400 font-normal block mt-0.5">// Validation Worker</span>
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="topo-col-resp pt-4 border-t border-slate-200 mt-6 bg-inherit relative z-20">
                  <div className="text-[11px] font-mono text-slate-500 uppercase tracking-tight font-bold mb-1">
                    RESPONSIBILITY:
                  </div>
                  <p className="text-[13px] font-sans text-slate-700 leading-snug">
                    Executes generated repairs without direct production writes.
                  </p>
                </div>
              </div>

              {/* D. EXTERNAL SERVICES (EXTERNAL SERVICE BOUNDARY) */}
              <div className="topo-col relative z-10 pt-16 px-6 pb-6 flex flex-col justify-between min-h-[380px] bg-slate-50/40">
                
                {/* Header boundary label */}
                <div className="topo-col-header absolute top-0 left-0 right-0 bg-slate-500 text-white text-[10px] font-mono tracking-widest py-2 px-4 uppercase font-bold text-center border-b border-slate-600">
                  04 / EXTERNAL SERVICE BOUNDARY
                </div>

                <div className="topo-col-body space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                      SYSTEM EXTERNAL
                    </span>
                    <span className="topo-col-dot w-2.5 h-2.5 rounded-full bg-slate-300 relative z-20" />
                  </div>

                  <div className="space-y-3">
                    <div className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                      // COMPONENTS:
                    </div>
                    <ul className="space-y-2 relative z-20">
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ DataHub GraphQL
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ DataHub Metadata Writeback
                      </li>
                      <li className="topo-col-comp-item bg-white border border-slate-200 px-3 py-2 font-mono text-[12px] font-bold text-[var(--color-riftless-ink)] shadow-xs">
                        ▪ DeepSeek API
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="topo-col-resp pt-4 border-t border-slate-200 mt-6 bg-inherit relative z-20">
                  <div className="text-[11px] font-mono text-slate-500 uppercase tracking-tight font-bold mb-1">
                    RESPONSIBILITY:
                  </div>
                  <p className="text-[13px] font-sans text-slate-700 leading-snug">
                    Provides metadata context, remediation planning, and target metadata persistence.
                  </p>
                </div>
              </div>

            </div>

            {/* Unified Data Paths Flow */}
            <div className="topo-paths-row pt-6 border-t border-slate-100">
              <div className="text-xs font-mono font-bold text-[var(--color-riftless-graph-gray)] uppercase tracking-wider mb-4">
                // TARGET DATA FLOW PATHS & INTEGRITY TRACK
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                
                {/* Path 1 */}
                <div className="topo-path-card bg-slate-50 p-4 border border-slate-200">
                  <div className="text-[10px] font-mono text-slate-400 font-bold uppercase mb-2">01. INGESTION PATH</div>
                  <div className="space-y-1 font-mono text-xs">
                    <div className="font-bold text-[var(--color-riftless-ink)]">GitHub App / Webhook</div>
                    <div className="text-slate-400 text-[10px]">↓ propose change</div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">FastAPI Orchestrator</div>
                  </div>
                </div>

                {/* Path 2 */}
                <div className="topo-path-card bg-slate-50 p-4 border border-slate-200">
                  <div className="text-[10px] font-mono text-slate-400 font-bold uppercase mb-2">02. METADATA CONTEXT</div>
                  <div className="space-y-1 font-mono text-xs">
                    <div className="font-bold text-[var(--color-riftless-ink)]">FastAPI Orchestrator</div>
                    <div className="text-slate-400 text-[10px]">↓ GraphQL Query</div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">DataHub GraphQL</div>
                    <div className="text-slate-400 text-[10px]">↓ Context Pack</div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">FastAPI Orchestrator</div>
                  </div>
                </div>

                {/* Path 3 */}
                <div className="topo-path-card bg-slate-50 p-4 border border-slate-200">
                  <div className="text-[10px] font-mono text-slate-400 font-bold uppercase mb-2">03. PLANNING SYNTHESIS</div>
                  <div className="space-y-1 font-mono text-xs">
                    <div className="font-bold text-[var(--color-riftless-ink)]">Redacted Context Pack</div>
                    <div className="text-slate-400 text-[10px]">↓ safe prompt stream</div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">DeepSeek API</div>
                    <div className="text-slate-400 text-[10px]">↓ Repair Plan</div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">Remediation Proposal</div>
                  </div>
                </div>

                {/* Path 4 (Signal Lime successful execution exit) */}
                <div className="topo-path-card bg-slate-50 p-4 border border-slate-200 relative overflow-hidden">
                  <div className="text-[10px] font-mono text-slate-400 font-bold uppercase mb-2">04. ISOLATED RUN</div>
                  <div className="space-y-1 font-mono text-xs">
                    <div className="font-bold text-[var(--color-riftless-ink)]">Remediation Proposal</div>
                    <div className="text-slate-400 text-[10px]">↓ execute validation</div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">Isolated Validation Worker</div>
                    <div className="text-slate-400 text-[10px]">↓ build verified evidence</div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">Evidence Bundle</div>
                  </div>
                  {/* Successful exit highlight */}
                  <div className="mt-2.5 inline-flex items-center gap-1 px-2 py-0.5 bg-[var(--color-riftless-signal)]/10 border border-[var(--color-riftless-signal)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-riftless-signal)]" />
                    <span className="text-[9px] font-mono font-bold text-[var(--color-riftless-ink)] uppercase">EXECUTION EXIT</span>
                  </div>
                </div>

                {/* Path 5 (Signal Lime return trace and authorized writeback) */}
                <div className="topo-path-card bg-slate-50 p-4 border-2 border-[var(--color-riftless-signal)] relative overflow-hidden shadow-[0_0_15px_rgba(168,205,22,0.04)]">
                  <div className="text-[10px] font-mono text-[var(--color-riftless-graph-gray)] font-bold uppercase mb-2">
                    05. WRITEBACK INTEGRITY
                  </div>
                  <div className="space-y-1 font-mono text-xs">
                    <div className="font-bold text-[var(--color-riftless-ink)]">Evidence Bundle</div>
                    <div className="text-[var(--color-riftless-graph-gray)] text-[10px] flex items-center gap-1">
                      <span className="text-[var(--color-riftless-signal)]">✔</span> returning to Control Plane
                    </div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">FastAPI Orchestrator</div>
                    <div className="text-[var(--color-riftless-graph-gray)] text-[10px] flex items-center gap-1">
                      <span className="text-[var(--color-riftless-signal)]">✔</span> authorized catalog update
                    </div>
                    <div className="font-bold text-[var(--color-riftless-ink)]">Target DataHub Writeback</div>
                  </div>
                  {/* Successful evidence tracer */}
                  <div className="absolute top-2 right-2 flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-riftless-signal)] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-riftless-signal)]"></span>
                  </div>
                </div>

              </div>
            </div>

            {/* Secrets Guardrail Panel */}
            <div className="pt-6 border-t border-slate-100 flex justify-center">
              <div className="topo-security-envelope w-full max-w-3xl border border-slate-200 bg-slate-50 p-6 space-y-4">
                
                {/* Panel Header */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-slate-200 pb-3 gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-[var(--color-riftless-critical)] text-white font-mono text-[9px] font-extrabold uppercase">
                      SECURITY ENVELOPE
                    </span>
                    <span className="text-xs font-mono font-bold text-[var(--color-riftless-ink)] uppercase">
                      REDACTION & TRACE GUARDRAIL
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-[var(--color-riftless-critical)] font-extrabold tracking-wide uppercase">
                    SECRETS NEVER ENTER MODEL CONTEXT
                  </span>
                </div>

                {/* Visual Columns of Secrets Isolation */}
                <div className="grid grid-cols-1 md:grid-cols-11 gap-4 items-center">
                  
                  {/* Server Side Secrets */}
                  <div className="topo-secrets-left md:col-span-5 bg-white border border-slate-200 p-4 space-y-2">
                    <div className="text-[10px] font-mono text-[var(--color-riftless-graph-gray)] font-bold uppercase tracking-wider">
                      ● SERVER-SIDE ONLY SECRETS
                    </div>
                    <ul className="font-mono text-xs text-[var(--color-riftless-ink)] space-y-1.5">
                      <li className="flex items-center gap-2">
                        <span className="text-emerald-600">✔</span> GitHub Token
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-emerald-600">✔</span> DataHub Credentials
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-emerald-600">✔</span> DeepSeek API Key
                      </li>
                    </ul>
                  </div>

                  {/* Red Blocked Path Connector */}
                  <div className="topo-secrets-blocked-connector md:col-span-1 flex flex-col items-center justify-center space-y-1">
                    <span className="topo-secrets-cross text-[var(--color-riftless-critical)] font-black text-xl leading-none">×</span>
                    <div className="topo-secrets-blocked h-6 w-[2px] bg-[var(--color-riftless-critical)] relative flex items-center justify-center">
                      <span className="absolute text-[10px] font-mono font-bold text-[var(--color-riftless-critical)] tracking-tighter uppercase whitespace-nowrap bg-slate-50 px-1 py-0.5 scale-75 -rotate-90">
                        BLOCKED
                      </span>
                    </div>
                    <span className="topo-secrets-cross text-[var(--color-riftless-critical)] font-black text-xl leading-none">×</span>
                  </div>

                  {/* Model Received Safe Items */}
                  <div className="topo-secrets-right md:col-span-5 bg-white border border-slate-200 p-4 space-y-2">
                    <div className="text-[10px] font-mono text-[var(--color-riftless-graph-gray)] font-bold uppercase tracking-wider">
                      ● MODEL RECEIVES (REDACTED)
                    </div>
                    <ul className="font-mono text-xs text-[var(--color-riftless-ink)] space-y-1.5">
                      <li className="flex items-center gap-2">
                        <span className="text-amber-500">▪</span> Redacted Context Pack
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-amber-500">▪</span> Proposed Diff
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-amber-500">▪</span> Policy Constraints
                      </li>
                    </ul>
                  </div>

                </div>

              </div>
            </div>

          </div>
        </div>
      </section>

      {/* F2.8 — Failure & Recovery Model */}
      <section ref={failureRecoveryRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-[var(--color-riftless-ink)] text-[var(--color-riftless-paper)] border-t border-slate-800">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12 items-start border-b border-slate-800 pb-10">
            <div className="lg:col-span-8 space-y-4">
              <span className="fail-label text-xs lg:text-sm font-mono font-bold tracking-[0.25em] text-[var(--color-riftless-muted)] uppercase block">
                08 / FAILURE & RECOVERY
              </span>

              <h2 className="text-3xl sm:text-5xl font-display font-extrabold tracking-tighter uppercase leading-[0.95] text-[var(--color-riftless-paper)] overflow-hidden">
                <span className="fail-headline-line block">FAILURE STOPS</span>
                <span className="fail-headline-line block">THE WRITE.</span>
                <span className="fail-headline-line block">NOT THE EVIDENCE.</span>
              </h2>

              <p className="fail-supporting text-sm sm:text-base font-sans text-slate-400 leading-relaxed max-w-2xl">
                RIFTLESS blocks unsafe progression, preserves every available artifact, and makes recovery an explicit policy decision.
              </p>
            </div>

            <div className="fail-target-model lg:col-span-4 lg:text-right space-y-2 lg:pt-8">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-none">
                <span className="w-2 h-2 bg-[var(--color-riftless-critical)]" />
                <span className="text-[11px] lg:text-xs font-mono tracking-wider uppercase font-bold text-[var(--color-riftless-paper)]">
                  TARGET FAILURE HANDLING MODEL
                </span>
              </div>
              <p className="text-[11px] sm:text-xs font-mono text-slate-500">
                // Conceptual recovery specifications. Recovery backend not live.
              </p>
            </div>
          </div>

          {/* Continuous failure-handling boundary container */}
          <div className="border border-slate-800 bg-slate-950 rounded-none p-6 md:p-8 space-y-12">
            
            {/* 1. Main Trajectory Rail */}
            <div className="space-y-4">
              <div className="flex items-center justify-between font-mono text-[10px] text-slate-500 uppercase tracking-widest pb-2 border-b border-slate-900">
                <span>// FAILURE-HANDLING TRAJECTORY RAIL</span>
                <span className="hidden sm:inline">DETERMINISTIC SAFETY RUN</span>
              </div>

              {/* Shared continuous container & direction lines */}
              <div className="relative p-6 border border-slate-800/80 bg-slate-900/40 rounded-none">
                {/* Horizontal line on desktop */}
                <div className="fail-rail-desktop hidden md:block absolute top-[60px] left-8 right-8 h-[2px] bg-slate-800/80 z-0" />
                {/* Vertical line on mobile */}
                <div className="fail-spine-mobile md:hidden absolute left-[31px] top-6 bottom-6 w-[2px] bg-slate-800/80 z-0" />

                <div className="grid grid-cols-1 md:grid-cols-5 gap-6 md:gap-4 relative z-10">
                  
                  {/* Step 1: RUN IN PROGRESS */}
                  <div className="fail-trajectory-card flex md:flex-col items-start gap-4 md:gap-3">
                    <div className="fail-trajectory-dot flex-none w-8 h-8 rounded-full border border-slate-700 bg-slate-900 text-[11px] font-mono font-bold flex items-center justify-center text-slate-300 relative z-20">
                      01
                    </div>
                    <div className="space-y-1">
                      <h4 className="fail-trajectory-title text-[12px] font-mono font-bold tracking-wider text-slate-200 uppercase">
                        RUN IN PROGRESS
                      </h4>
                      <p className="fail-trajectory-desc text-[12px] font-sans text-slate-400 leading-snug">
                        Target pipeline execution and code transformation scanning.
                      </p>
                    </div>
                  </div>

                  {/* Step 2: FAILURE DETECTED */}
                  <div className="fail-trajectory-card flex md:flex-col items-start gap-4 md:gap-3">
                    <div className="fail-trajectory-dot flex-none w-8 h-8 rounded-full border border-[var(--color-riftless-warning)] bg-slate-900 text-[11px] font-mono font-bold flex items-center justify-center text-[var(--color-riftless-warning)] relative z-20">
                      02
                    </div>
                    <div className="space-y-1">
                      <h4 className="fail-trajectory-title text-[12px] font-mono font-bold tracking-wider text-[var(--color-riftless-warning)] uppercase">
                        FAILURE DETECTED
                      </h4>
                      <p className="fail-trajectory-desc text-[12px] font-sans text-slate-400 leading-snug">
                        Immediate interrupt triggered by validation engine.
                      </p>
                    </div>
                  </div>

                  {/* Step 3: WRITEBACK BLOCKED */}
                  <div className="fail-trajectory-card flex md:flex-col items-start gap-4 md:gap-3">
                    <div className="fail-trajectory-dot flex-none w-8 h-8 rounded-full border-2 border-[var(--color-riftless-critical)] bg-slate-900 text-[11px] font-mono font-bold flex items-center justify-center text-[var(--color-riftless-critical)] relative z-20 shadow-[0_0_8px_rgba(255,90,78,0.3)]">
                      03
                    </div>
                    <div className="space-y-1">
                      <h4 className="fail-trajectory-title text-[12px] font-mono font-bold tracking-wider text-[var(--color-riftless-critical)] uppercase">
                        WRITEBACK BLOCKED
                      </h4>
                      <p className="fail-trajectory-desc text-[12px] font-sans text-slate-400 leading-snug">
                        Hard block applied on catalog target write pathways.
                      </p>
                    </div>
                  </div>

                  {/* Step 4: ARTIFACTS PRESERVED */}
                  <div className="fail-trajectory-card flex md:flex-col items-start gap-4 md:gap-3">
                    <div className="fail-trajectory-dot flex-none w-8 h-8 rounded-full border border-slate-700 bg-slate-900 text-[11px] font-mono font-bold flex items-center justify-center text-slate-300 relative z-20">
                      04
                    </div>
                    <div className="space-y-1">
                      <h4 className="fail-trajectory-title text-[12px] font-mono font-bold tracking-wider text-slate-200 uppercase">
                        ARTIFACTS PRESERVED
                      </h4>
                      <p className="fail-trajectory-desc text-[12px] font-sans text-slate-400 leading-snug">
                        All state metadata, logs, and patches isolated securely.
                      </p>
                    </div>
                  </div>

                  {/* Step 5: RECOVERY DECISION */}
                  <div className="fail-trajectory-card flex md:flex-col items-start gap-4 md:gap-3">
                    <div className="fail-trajectory-dot flex-none w-8 h-8 rounded-full border border-slate-700 bg-slate-900 text-[11px] font-mono font-bold flex items-center justify-center text-slate-300 relative z-20">
                      05
                    </div>
                    <div className="space-y-1">
                      <h4 className="fail-trajectory-title text-[12px] font-mono font-bold tracking-wider text-slate-200 uppercase">
                        RECOVERY DECISION
                      </h4>
                      <p className="fail-trajectory-desc text-[12px] font-sans text-slate-400 leading-snug">
                        Deterministic policy action chosen to resolve fail-state.
                      </p>
                    </div>
                  </div>

                </div>
              </div>
            </div>

            {/* 2. Failure Matrix */}
            <div className="space-y-4">
              <div className="flex items-center justify-between font-mono text-[10px] text-slate-500 uppercase tracking-widest pb-2 border-b border-slate-900">
                <span>// FAILURE CLASSES & RESPONSE MATRIX</span>
                <span>4 EXPLICIT LEVELS</span>
              </div>

              {/* Shared Boundary Table */}
              <div className="border border-slate-800 bg-slate-900/20 divide-y divide-slate-800/80">
                
                {/* Row 1: INPUT FAILURE */}
                <div className="fail-matrix-row p-5 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
                  <div className="fail-matrix-class lg:col-span-3">
                    <span className="text-[10px] font-mono text-slate-500 tracking-wider block mb-1">LEVEL 01</span>
                    <h5 className="text-[13px] font-mono font-bold text-[var(--color-riftless-paper)] uppercase tracking-wide">
                      INPUT FAILURE
                    </h5>
                  </div>
                  <div className="fail-matrix-examples lg:col-span-4 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">EXAMPLES:</span>
                    <ul className="text-[12px] font-mono text-slate-400 space-y-0.5">
                      <li>▪ Invalid diff</li>
                      <li>▪ Unsupported SQL</li>
                      <li>▪ Missing repository context</li>
                    </ul>
                  </div>
                  <div className="fail-matrix-response lg:col-span-5 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">TARGET RESPONSE:</span>
                    <p className="text-[13px] font-sans text-slate-300 leading-snug">
                      Reject input before context assembly.
                    </p>
                  </div>
                </div>

                {/* Row 2: CONTEXT FAILURE */}
                <div className="fail-matrix-row p-5 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
                  <div className="fail-matrix-class lg:col-span-3">
                    <span className="text-[10px] font-mono text-slate-500 tracking-wider block mb-1">LEVEL 02</span>
                    <h5 className="text-[13px] font-mono font-bold text-[var(--color-riftless-paper)] uppercase tracking-wide">
                      CONTEXT FAILURE
                    </h5>
                  </div>
                  <div className="fail-matrix-examples lg:col-span-4 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">EXAMPLES:</span>
                    <ul className="text-[12px] font-mono text-slate-400 space-y-0.5">
                      <li>▪ DataHub unavailable</li>
                      <li>▪ Incomplete lineage</li>
                      <li>▪ Missing ownership metadata</li>
                    </ul>
                  </div>
                  <div className="fail-matrix-response lg:col-span-5 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">TARGET RESPONSE:</span>
                    <p className="text-[13px] font-sans text-slate-300 leading-snug">
                      Block grounded decision or require human review.
                    </p>
                  </div>
                </div>

                {/* Row 3: PLANNING FAILURE */}
                <div className="fail-matrix-row p-5 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
                  <div className="fail-matrix-class lg:col-span-3">
                    <span className="text-[10px] font-mono text-slate-500 tracking-wider block mb-1">LEVEL 03</span>
                    <h5 className="text-[13px] font-mono font-bold text-[var(--color-riftless-paper)] uppercase tracking-wide">
                      PLANNING FAILURE
                    </h5>
                  </div>
                  <div className="fail-matrix-examples lg:col-span-4 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">EXAMPLES:</span>
                    <ul className="text-[12px] font-mono text-slate-400 space-y-0.5">
                      <li>▪ DeepSeek unavailable</li>
                      <li>▪ Invalid remediation proposal</li>
                      <li>▪ Policy constraint conflict</li>
                    </ul>
                  </div>
                  <div className="fail-matrix-response lg:col-span-5 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">TARGET RESPONSE:</span>
                    <p className="text-[13px] font-sans text-slate-300 leading-snug">
                      Preserve deterministic decision and do not execute proposal.
                    </p>
                  </div>
                </div>

                {/* Row 4: VALIDATION FAILURE */}
                <div className="fail-matrix-row p-5 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
                  <div className="fail-matrix-class lg:col-span-3">
                    <span className="text-[10px] font-mono text-slate-500 tracking-wider block mb-1">LEVEL 04</span>
                    <h5 className="text-[13px] font-mono font-bold text-[var(--color-riftless-paper)] uppercase tracking-wide">
                      VALIDATION FAILURE
                    </h5>
                  </div>
                  <div className="fail-matrix-examples lg:col-span-4 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">EXAMPLES:</span>
                    <ul className="text-[12px] font-mono text-slate-400 space-y-0.5">
                      <li>▪ SQL parse failure / DuckDB execution</li>
                      <li>▪ dbt compile / test failures</li>
                    </ul>
                  </div>
                  <div className="fail-matrix-response lg:col-span-5 space-y-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">TARGET RESPONSE:</span>
                    <p className="text-[13px] font-sans text-slate-300 leading-snug">
                      Block writeback and preserve executable evidence.
                    </p>
                  </div>
                </div>

              </div>
            </div>

            {/* 3. Recovery Decision Branches & External Service Target Behaviors */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-6 border-t border-slate-900">
              
              {/* Recovery Decision Branches */}
              <div className="lg:col-span-6 space-y-4">
                <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
                  // RECOVERY DECISION BRANCHES
                </div>
                <div className="space-y-3">
                  
                  {/* SAFE RETRY */}
                  <div className="fail-branch-card fail-branch-safe border border-[var(--color-riftless-signal)]/30 bg-slate-900/20 p-4 relative overflow-hidden">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-mono font-bold text-[var(--color-riftless-signal)] uppercase tracking-wider">
                        ✔ SAFE RETRY
                      </span>
                      <span className="w-2 h-2 rounded-full bg-[var(--color-riftless-signal)] shadow-[0_0_6px_rgba(168,205,22,0.6)]" />
                    </div>
                    <p className="text-[13px] font-mono font-bold text-[var(--color-riftless-paper)]">
                      → RE-ENTER FAILED STAGE
                    </p>
                    <p className="text-xs font-sans text-slate-400 mt-1">
                      Authorized automatic retry loop for transient failures with safe state clean.
                    </p>
                  </div>

                  {/* HUMAN REVIEW */}
                  <div className="fail-branch-card fail-branch-human border border-[var(--color-riftless-warning)]/30 bg-slate-900/20 p-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-mono font-bold text-[var(--color-riftless-warning)] uppercase tracking-wider">
                        ▲ HUMAN REVIEW
                      </span>
                      <span className="w-2 h-2 rounded-full bg-[var(--color-riftless-warning)]" />
                    </div>
                    <p className="text-[13px] font-mono font-bold text-[var(--color-riftless-paper)]">
                      → REVISE CHANGE OR POLICY
                    </p>
                    <p className="text-xs font-sans text-slate-400 mt-1">
                      Alert operator to adjust policy files, schemas, or dbt code config manually.
                    </p>
                  </div>

                  {/* TERMINAL CLOSE */}
                  <div className="fail-branch-card fail-branch-terminal border border-[var(--color-riftless-critical)]/30 bg-slate-900/20 p-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-mono font-bold text-[var(--color-riftless-critical)] uppercase tracking-wider">
                        ✖ TERMINAL CLOSE
                      </span>
                      <span className="w-2 h-2 rounded-full bg-[var(--color-riftless-critical)]" />
                    </div>
                    <p className="text-[13px] font-mono font-bold text-[var(--color-riftless-paper)]">
                      → PRESERVE ARTIFACTS AND CLOSE RUN
                    </p>
                    <p className="text-xs font-sans text-slate-400 mt-1">
                      Abort run, fully freeze deployment boundary state, and write diagnostic summaries.
                    </p>
                  </div>

                </div>
              </div>

              {/* External Service Recovery Behavior */}
              <div className="lg:col-span-6 space-y-4">
                <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
                  // EXTERNAL-SERVICE RECOVERY TARGET BEHAVIOR
                </div>
                <div className="space-y-3">
                  
                  {/* DataHub Read */}
                  <div className="fail-ext-card border border-slate-800 bg-slate-900/30 p-4">
                    <div className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wide mb-1">
                      DATAHUB READ COUPLING
                    </div>
                    <div className="space-y-1 font-mono">
                      <div className="text-[12px] font-bold text-[var(--color-riftless-paper)]">DATAHUB READ UNAVAILABLE</div>
                      <div className="text-xs text-slate-400">→ CONTEXT ASSEMBLY BLOCKED</div>
                    </div>
                    <p className="text-[11px] font-sans text-slate-500 mt-2">
                      Ensures the system never hallucinates metadata models or lineage paths when the primary catalog reads fail.
                    </p>
                  </div>

                  {/* DeepSeek */}
                  <div className="fail-ext-card border border-slate-800 bg-slate-900/30 p-4">
                    <div className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wide mb-1">
                      MODEL PLANNING COUPLING
                    </div>
                    <div className="space-y-1 font-mono">
                      <div className="text-[12px] font-bold text-[var(--color-riftless-paper)]">DEEPSEEK UNAVAILABLE</div>
                      <div className="text-xs text-slate-400">→ NO REMEDIATION GENERATED</div>
                    </div>
                    <p className="text-[11px] font-sans text-slate-500 mt-2">
                      Fails safely by halting change generation without disrupting existing cluster processes.
                    </p>
                  </div>

                  {/* DataHub Writeback */}
                  <div className="fail-ext-card border border-slate-800 bg-slate-900/30 p-4">
                    <div className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wide mb-1">
                      CATALOG INTEGRATION COUPLING
                    </div>
                    <div className="space-y-1 font-mono">
                      <div className="text-[12px] font-bold text-[var(--color-riftless-paper)]">DATAHUB WRITEBACK UNAVAILABLE</div>
                      <div className="text-xs text-slate-400">→ RECORD PRESERVED FOR TARGET RETRY</div>
                    </div>
                    <p className="text-[11px] font-sans text-slate-500 mt-2">
                      Caches the final evidence logs locally to prevent loss of telemetry once write pathways reopen.
                    </p>
                  </div>

                </div>
              </div>

            </div>

            {/* 4. Preserved Evidence Trail Trace Line */}
            <div className="pt-6 border-t border-slate-900 space-y-4">
              <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
                // PRESERVED EVIDENCE TRAIL PIPELINE
              </div>
              <div className="relative border border-slate-800 bg-slate-900/10 py-4 px-6 overflow-hidden">
                {/* Horizontal line on desktop */}
                <div className="fail-evidence-line-desktop hidden md:block absolute top-1/2 left-6 right-6 h-[1px] bg-slate-800/40 -translate-y-1/2 z-0" />
                {/* Vertical line on mobile */}
                <div className="fail-evidence-line-mobile md:hidden absolute left-[28px] top-4 bottom-4 w-[1px] bg-slate-800/40 z-0" />

                <div className="flex flex-wrap items-center justify-between gap-y-4 gap-x-2 font-mono text-[11px] font-bold relative z-10">
                  
                  <div className="fail-evidence-item flex items-center gap-2 bg-slate-950 px-2 py-1">
                    <span className="text-[10px] text-slate-500">01</span>
                    <span className="text-[var(--color-riftless-paper)]">INPUT DIFF</span>
                  </div>

                  <span className="fail-evidence-slash text-slate-600 bg-slate-950 px-1 py-1">/</span>

                  <div className="fail-evidence-item flex items-center gap-2 bg-slate-950 px-2 py-1">
                    <span className="text-[10px] text-slate-500">02</span>
                    <span className="text-[var(--color-riftless-paper)]">CONTEXT SNAPSHOT</span>
                  </div>

                  <span className="fail-evidence-slash text-slate-600 bg-slate-950 px-1 py-1">/</span>

                  <div className="fail-evidence-item flex items-center gap-2 bg-slate-950 px-2 py-1">
                    <span className="text-[10px] text-slate-500">03</span>
                    <span className="text-[var(--color-riftless-paper)]">RISK DECISION</span>
                  </div>

                  <span className="fail-evidence-slash text-slate-600 bg-slate-950 px-1 py-1">/</span>

                  <div className="fail-evidence-item flex items-center gap-2 bg-slate-950 px-2 py-1">
                    <span className="text-[10px] text-slate-500">04</span>
                    <span className="text-[var(--color-riftless-paper)]">GENERATED PATCH</span>
                  </div>

                  <span className="fail-evidence-slash text-slate-600 bg-slate-950 px-1 py-1">/</span>

                  <div className="fail-evidence-item flex items-center gap-2 bg-slate-950 px-2 py-1">
                    <span className="text-[10px] text-slate-500">05</span>
                    <span className="text-[var(--color-riftless-paper)]">VALIDATION LOG</span>
                  </div>

                  <span className="fail-evidence-slash text-slate-600 bg-slate-950 px-1 py-1">/</span>

                  <div className="fail-evidence-item flex items-center gap-2 bg-slate-950 px-2 py-1">
                    <span className="text-[10px] text-slate-500">06</span>
                    <span className="text-[var(--color-riftless-critical)]">FAILURE REASON</span>
                  </div>

                </div>
              </div>
            </div>

            {/* 5. Guardrail Invariant Statement */}
            <div className="pt-6 border-t border-slate-900 flex justify-center">
              <div className="fail-invariant-envelope w-full max-w-3xl border border-dashed border-slate-800 bg-slate-900/10 p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="space-y-1">
                  <span className="px-2 py-0.5 bg-[var(--color-riftless-critical)] text-white font-mono text-[9px] font-extrabold uppercase">
                    TARGET RECOVERY INVARIANT
                  </span>
                  <p className="text-[15px] font-mono font-bold tracking-tight text-[var(--color-riftless-paper)]">
                    NO FAILURE PATH BYPASSES POLICY OR VALIDATION.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[var(--color-riftless-critical)] animate-pulse" />
                  <span className="text-[10px] font-mono font-bold text-[var(--color-riftless-critical)] uppercase tracking-wider">
                    HARD CONSTRAINT
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* F2.9 — Architecture Final CTA */}
      <section ref={architectureCtaRef} className="w-full py-20 px-4 sm:px-6 lg:px-8 bg-[var(--color-riftless-signal)] text-[var(--color-riftless-ink)]">
        <div className="max-w-7xl mx-auto space-y-10">
          
          {/* Section Header */}
          <div className="text-center space-y-6">
            <span className="cta-label text-xs sm:text-sm font-mono font-extrabold tracking-[0.25em] text-[var(--color-riftless-ink)]/70 uppercase block">
              09 / EXPLORE THE SYSTEM
            </span>

            <h2 className="text-4xl sm:text-6xl lg:text-7xl font-display font-extrabold uppercase tracking-tighter leading-[0.95] text-[var(--color-riftless-ink)] overflow-hidden">
              <span className="cta-headline-line block">TRACE THE CHANGE.</span>
              <span className="cta-headline-line block">VERIFY THE DECISION.</span>
            </h2>

            <p className="cta-supporting text-base sm:text-lg font-sans text-[var(--color-riftless-ink)]/80 leading-relaxed max-w-2xl mx-auto">
              Explore how RIFTLESS turns proposed data changes into grounded decisions, executable evidence, and preserved context.
            </p>
          </div>

          {/* Call To Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
            <Link
              to="/demo"
              className="cta-button w-full sm:w-auto px-8 py-4 bg-[var(--color-riftless-ink)] text-[var(--color-riftless-signal)] font-mono text-sm font-bold tracking-wider uppercase text-center rounded-none shadow-sm hover:bg-slate-900 focus-visible:ring-2 focus-visible:ring-slate-950 focus:ring-2 focus:ring-slate-950 outline-none transition-colors"
            >
              RUN THE DEMO →
            </Link>
            <Link
              to="/docs"
              className="cta-button w-full sm:w-auto px-8 py-4 border-2 border-[var(--color-riftless-ink)] text-[var(--color-riftless-ink)] font-mono text-sm font-bold tracking-wider uppercase text-center rounded-none hover:bg-[var(--color-riftless-ink)] hover:text-[var(--color-riftless-signal)] focus-visible:ring-2 focus-visible:ring-slate-950 focus:ring-2 focus:ring-slate-950 outline-none transition-colors"
            >
              READ THE DOCS →
            </Link>
          </div>

          {/* Architecture Summary Line */}
          <div className="w-full max-w-4xl mx-auto pt-10 border-t border-[var(--color-riftless-ink)]/15 space-y-4">
            <div className="text-[10px] font-mono font-bold tracking-widest text-center text-[var(--color-riftless-ink)]/60 uppercase">
              // CORE PIPELINE INTEGRITY TRACK
            </div>
            <div className="flex flex-col md:flex-row items-center justify-center gap-2 md:gap-4 font-mono text-xs sm:text-sm font-bold tracking-widest uppercase py-4 border-t border-b border-[var(--color-riftless-ink)]/15">
              <span className="cta-flow-node">CONTEXT</span>
              <span className="cta-flow-arrow hidden md:inline text-xl">→</span>
              <span className="cta-flow-arrow md:hidden text-xl rotate-90 my-1">↓</span>
              <span className="cta-flow-node">POLICY</span>
              <span className="cta-flow-arrow hidden md:inline text-xl">→</span>
              <span className="cta-flow-arrow md:hidden text-xl rotate-90 my-1">↓</span>
              <span className="cta-flow-node">REMEDIATION</span>
              <span className="cta-flow-arrow hidden md:inline text-xl">→</span>
              <span className="cta-flow-arrow md:hidden text-xl rotate-90 my-1">↓</span>
              <span className="cta-flow-node">EVIDENCE</span>
              <span className="cta-flow-arrow hidden md:inline text-xl">→</span>
              <span className="cta-flow-arrow md:hidden text-xl rotate-90 my-1">↓</span>
              <span className="cta-flow-node">WRITEBACK</span>
            </div>
          </div>

          {/* Target-state disclaimer */}
          <div className="text-center pt-4">
            <span className="cta-disclaimer text-[10px] font-mono font-extrabold text-[var(--color-riftless-ink)]/50 tracking-wider block">
              ARCHITECTURE SHOWN AS THE TARGET IMPLEMENTATION MODEL.
            </span>
          </div>

        </div>
      </section>

    </div>
  );
}
