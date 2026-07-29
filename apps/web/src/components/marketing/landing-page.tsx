"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowRight,
  BookOpen,
  Captions,
  Check,
  ChevronRight,
  Link2,
  Menu,
  Play,
  X,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useLayoutEffect, useRef, useState } from "react";

import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";

type LandingPageProps = {
  isAuthenticated: boolean;
};

const steps = [
  {
    number: "01",
    icon: Link2,
    title: "Add a source",
    description: "Paste a YouTube video or playlist. Recall organizes the metadata automatically.",
  },
  {
    number: "02",
    icon: BookOpen,
    title: "Build your path",
    description: "Keep lessons ordered inside focused spaces with progress that stays visible.",
  },
  {
    number: "03",
    icon: Captions,
    title: "Study with context",
    description:
      "Watch, read the synchronized transcript, take notes, and continue where you left off.",
  },
];

export function LandingPage({ isAuthenticated }: LandingPageProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useLayoutEffect(() => {
    gsap.registerPlugin(ScrollTrigger);

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion || !rootRef.current) return;

    const context = gsap.context(() => {
      gsap
        .timeline({ defaults: { ease: "power3.out" } })
        .from("[data-hero-copy] > *", {
          y: 24,
          opacity: 0,
          duration: 0.75,
          stagger: 0.08,
        })
        .from(
          "[data-product-stage]",
          {
            y: 42,
            opacity: 0,
            scale: 0.985,
            duration: 1,
          },
          "-=0.4",
        );

      gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((element) => {
        gsap.from(element, {
          scrollTrigger: {
            trigger: element,
            start: "top 84%",
            once: true,
          },
          y: 28,
          opacity: 0,
          duration: 0.75,
          ease: "power3.out",
        });
      });

      gsap.from("[data-flow-step]", {
        scrollTrigger: {
          trigger: "[data-flow-grid]",
          start: "top 80%",
          once: true,
        },
        y: 24,
        opacity: 0,
        duration: 0.65,
        stagger: 0.12,
        ease: "power3.out",
      });
    }, rootRef);

    return () => context.revert();
  }, []);

  const primaryHref = isAuthenticated ? "/dashboard" : "/register";
  const primaryLabel = isAuthenticated ? "Open dashboard" : "Start learning";

  return (
    <div ref={rootRef} className="min-h-screen bg-background text-foreground">
      <header className="fixed inset-x-0 top-0 z-40 border-b border-white/[0.06] bg-background/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-5 sm:px-8">
          <Link href="/" aria-label="Recall home">
            <Logo />
          </Link>

          <nav className="hidden items-center gap-8 md:flex" aria-label="Main navigation">
            <a
              className="text-sm text-muted transition-colors hover:text-foreground"
              href="#product"
            >
              Product
            </a>
            <a className="text-sm text-muted transition-colors hover:text-foreground" href="#flow">
              How it works
            </a>
            <a className="text-sm text-muted transition-colors hover:text-foreground" href="#study">
              Study experience
            </a>
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            {!isAuthenticated ? (
              <Button asChild variant="ghost">
                <Link href="/login">Sign in</Link>
              </Button>
            ) : null}
            <Button asChild>
              <Link href={primaryHref}>
                {primaryLabel}
                <ArrowRight />
              </Link>
            </Button>
          </div>

          <button
            type="button"
            className="flex size-10 items-center justify-center text-muted transition-colors hover:text-foreground md:hidden"
            onClick={() => setMenuOpen((current) => !current)}
            aria-label={menuOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X /> : <Menu />}
          </button>
        </div>

        {menuOpen ? (
          <div className="border-t border-border bg-background px-5 py-5 md:hidden">
            <nav className="grid gap-1" aria-label="Mobile navigation">
              {[
                ["Product", "#product"],
                ["How it works", "#flow"],
                ["Study experience", "#study"],
              ].map(([label, href]) => (
                <a
                  key={href}
                  href={href}
                  className="py-3 text-sm text-muted"
                  onClick={() => setMenuOpen(false)}
                >
                  {label}
                </a>
              ))}
              <Button asChild className="mt-3 w-full">
                <Link href={primaryHref}>{primaryLabel}</Link>
              </Button>
            </nav>
          </div>
        ) : null}
      </header>

      <main>
        <section className="relative flex min-h-[min(940px,100svh)] flex-col overflow-hidden border-b border-border pt-16">
          <div
            data-hero-copy
            className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-center px-5 pb-10 pt-16 text-center sm:px-8 sm:pt-24"
          >
            <div className="inline-flex items-center gap-2 border border-border bg-surface px-3 py-1.5 font-mono text-[11px] uppercase text-muted">
              <span className="size-1.5 bg-success" />
              Built for focused, continuous learning
            </div>
            <h1 className="mt-7 max-w-4xl font-heading text-4xl font-semibold leading-[1.08] sm:text-6xl lg:text-7xl">
              Your learning OS
              <span className="block text-muted">for internet video.</span>
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-7 text-muted sm:text-lg sm:leading-8">
              Recall turns scattered videos into structured learning paths with synchronized
              transcripts, clear progress, and a place to continue.
            </p>
            <div className="mt-8 flex w-full flex-col justify-center gap-3 sm:w-auto sm:flex-row">
              <Button asChild size="lg" className="min-w-44">
                <Link href={primaryHref}>
                  {primaryLabel}
                  <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary" className="min-w-44">
                <a href="#product">
                  <Play className="fill-current" />
                  See the product
                </a>
              </Button>
            </div>
          </div>

          <div
            id="product"
            data-product-stage
            className="mx-auto w-full max-w-[1320px] px-3 sm:px-8"
          >
            <div className="overflow-hidden border border-border bg-surface p-1 shadow-[0_32px_100px_rgba(0,0,0,0.48)]">
              <div className="flex h-9 items-center border-b border-border px-3">
                <div className="flex gap-1.5" aria-hidden="true">
                  <span className="size-2 bg-white/20" />
                  <span className="size-2 bg-white/10" />
                  <span className="size-2 bg-primary/70" />
                </div>
                <span className="mx-auto font-mono text-[10px] text-muted">recall / dashboard</span>
              </div>
              <Image
                src="/product/dashboard.png"
                alt="Recall dashboard showing learning spaces, progress, and recent activity"
                width={1440}
                height={1024}
                priority
                className="h-auto w-full"
              />
            </div>
          </div>
        </section>

        <section id="flow" className="border-b border-border bg-surface/40 py-24 sm:py-32">
          <div className="mx-auto max-w-[1200px] px-5 sm:px-8">
            <div data-reveal className="max-w-2xl">
              <p className="font-mono text-xs uppercase text-primary">A clearer learning loop</p>
              <h2 className="mt-4 font-heading text-3xl font-semibold sm:text-5xl">
                From link to learning path.
              </h2>
              <p className="mt-5 text-base leading-7 text-muted sm:text-lg">
                No complex setup. Add the material you already trust and keep the learning context
                around it.
              </p>
            </div>

            <div
              data-flow-grid
              className="mt-14 grid border-y border-border md:grid-cols-3 md:divide-x md:divide-border"
            >
              {steps.map((step) => {
                const Icon = step.icon;
                return (
                  <article
                    key={step.number}
                    data-flow-step
                    className="border-b border-border py-8 last:border-b-0 md:border-b-0 md:px-8 md:first:pl-0 md:last:pr-0"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-muted">{step.number}</span>
                      <Icon className="size-5 text-primary" aria-hidden="true" />
                    </div>
                    <h3 className="mt-10 font-heading text-xl font-semibold">{step.title}</h3>
                    <p className="mt-3 max-w-sm text-sm leading-6 text-muted">{step.description}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section id="study" className="overflow-hidden border-b border-border py-24 sm:py-32">
          <div className="mx-auto max-w-[1320px] px-5 sm:px-8">
            <div data-reveal className="mx-auto max-w-3xl text-center">
              <p className="font-mono text-xs uppercase text-warm">Study with context</p>
              <h2 className="mt-4 font-heading text-3xl font-semibold sm:text-5xl">
                Video and transcript, in sync.
              </h2>
              <p className="mt-5 text-base leading-7 text-muted sm:text-lg">
                Navigate the curriculum, follow the complete transcript, and resume the exact lesson
                that matters.
              </p>
            </div>

            <div data-reveal className="relative mt-14">
              <div className="overflow-hidden border border-border bg-surface p-1 shadow-premium">
                <Image
                  src="/product/study-transcript.png"
                  alt="Recall study workspace with video, synchronized transcript, and curriculum"
                  width={1440}
                  height={1024}
                  className="h-auto w-full"
                />
              </div>
              <div className="absolute -bottom-8 right-4 hidden w-[210px] overflow-hidden border border-border bg-surface p-1 shadow-premium sm:block lg:right-10 lg:w-[260px]">
                <Image
                  src="/product/study-mobile.png"
                  alt="Recall study workspace on mobile"
                  width={390}
                  height={844}
                  className="h-auto w-full"
                />
              </div>
            </div>

            <div
              data-reveal
              className="mt-20 grid gap-4 border-t border-border pt-8 sm:grid-cols-3"
            >
              {["Timestamp navigation", "Automatic progress", "Curriculum continuity"].map(
                (item) => (
                  <div key={item} className="flex items-center gap-3 text-sm text-muted">
                    <span className="flex size-5 items-center justify-center border border-success/40 text-success">
                      <Check className="size-3" />
                    </span>
                    {item}
                  </div>
                ),
              )}
            </div>
          </div>
        </section>

        <section className="py-24 sm:py-32">
          <div data-reveal className="mx-auto max-w-4xl px-5 text-center sm:px-8">
            <p className="font-mono text-xs uppercase text-muted">One workspace. Every lesson.</p>
            <h2 className="mt-5 font-heading text-3xl font-semibold sm:text-5xl">
              Stop collecting videos.
              <span className="block text-muted">Start building knowledge.</span>
            </h2>
            <Button asChild size="lg" className="mt-8">
              <Link href={primaryHref}>
                {primaryLabel}
                <ChevronRight />
              </Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-[1440px] flex-col gap-5 px-5 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <Logo />
          <p className="text-xs text-muted">
            Structured learning from the content you already trust.
          </p>
          <div className="flex gap-5 text-xs text-muted">
            <Link href="/login" className="hover:text-foreground">
              Sign in
            </Link>
            <Link href="/register" className="hover:text-foreground">
              Create account
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
