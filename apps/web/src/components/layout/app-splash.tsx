"use client";

import gsap from "gsap";
import { useEffect, useRef, useState } from "react";

import { Logo } from "@/components/logo";

export function AppSplash() {
  const splashRef = useRef<HTMLDivElement | null>(null);
  const progressRef = useRef<HTMLDivElement | null>(null);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const hasPlayed = window.sessionStorage.getItem("recall-splash-played");
    if (hasPlayed) {
      setVisible(false);
      return;
    }

    window.sessionStorage.setItem("recall-splash-played", "true");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const timeline = gsap.timeline({
      onComplete: () => setVisible(false),
    });

    timeline
      .fromTo(
        progressRef.current,
        { scaleX: 0 },
        {
          scaleX: 1,
          duration: reducedMotion ? 0.15 : 1.15,
          ease: "power2.inOut",
        },
      )
      .to(splashRef.current, {
        opacity: 0,
        duration: reducedMotion ? 0.1 : 0.35,
        ease: "power2.out",
      });

    return () => {
      timeline.kill();
    };
  }, []);

  if (!visible) return null;

  return (
    <div
      ref={splashRef}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-background"
      role="status"
      aria-label="Loading Recall"
    >
      <div className="w-[min(320px,calc(100vw-48px))]">
        <Logo className="justify-center" />
        <div className="mt-8 h-px overflow-hidden bg-white/10">
          <div ref={progressRef} className="h-full origin-left bg-primary" />
        </div>
        <div className="mt-3 flex items-center justify-between font-mono text-[10px] uppercase text-muted">
          <span>Preparing workspace</span>
          <span>Recall</span>
        </div>
      </div>
    </div>
  );
}
