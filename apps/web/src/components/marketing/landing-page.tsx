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
import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { Logo } from "@/components/logo";
import { landingCopy, type LandingLocale } from "@/components/marketing/landing-copy";
import { Button } from "@/components/ui/button";

type LandingPageProps = {
  isAuthenticated: boolean;
};

const stepIcons = [Link2, BookOpen, Captions] as const;
const localeStorageKey = "recall-landing-locale";

export function LandingPage({ isAuthenticated }: LandingPageProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [locale, setLocale] = useState<LandingLocale>("pt");
  const copy = landingCopy[locale];

  useEffect(() => {
    const storedLocale = window.localStorage.getItem(localeStorageKey);
    if (storedLocale === "pt" || storedLocale === "en") {
      setLocale(storedLocale);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(localeStorageKey, locale);
    document.documentElement.lang = locale;

    return () => {
      document.documentElement.lang = "en";
    };
  }, [locale]);

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
  const primaryLabel = isAuthenticated ? copy.actions.openDashboard : copy.actions.startLearning;
  const navigationItems = [
    [copy.navigation.product, "#product"],
    [copy.navigation.flow, "#flow"],
    [copy.navigation.study, "#study"],
  ] as const;

  function selectLocale(nextLocale: LandingLocale) {
    setLocale(nextLocale);
    setMenuOpen(false);
  }

  return (
    <div ref={rootRef} lang={locale} className="min-h-screen bg-background text-foreground">
      <header className="fixed inset-x-0 top-0 z-40 border-b border-white/[0.06] bg-background/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-5 sm:px-8">
          <Link href="/" aria-label={copy.navigation.home}>
            <Logo />
          </Link>

          <nav className="hidden items-center gap-8 md:flex" aria-label={copy.navigation.label}>
            {navigationItems.map(([label, href]) => (
              <a
                key={href}
                className="text-sm text-muted transition-colors hover:text-foreground"
                href={href}
              >
                {label}
              </a>
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            <LanguageSelector
              locale={locale}
              label={copy.language.label}
              portugueseLabel={copy.language.portuguese}
              englishLabel={copy.language.english}
              onSelect={selectLocale}
            />
            {!isAuthenticated ? (
              <Button asChild variant="ghost">
                <Link href="/login">{copy.navigation.signIn}</Link>
              </Button>
            ) : null}
            <Button asChild>
              <Link href={primaryHref}>
                {primaryLabel}
                <ArrowRight />
              </Link>
            </Button>
          </div>

          <div className="flex items-center gap-1 md:hidden">
            <LanguageSelector
              locale={locale}
              label={copy.language.label}
              portugueseLabel={copy.language.portuguese}
              englishLabel={copy.language.english}
              onSelect={selectLocale}
              compact
            />
            <button
              type="button"
              className="flex size-10 items-center justify-center text-muted transition-colors hover:text-foreground"
              onClick={() => setMenuOpen((current) => !current)}
              aria-label={menuOpen ? copy.navigation.closeMenu : copy.navigation.openMenu}
              aria-expanded={menuOpen}
            >
              {menuOpen ? <X /> : <Menu />}
            </button>
          </div>
        </div>

        {menuOpen ? (
          <div className="border-t border-border bg-background px-5 py-5 md:hidden">
            <nav className="grid gap-1" aria-label={copy.navigation.mobileLabel}>
              {navigationItems.map(([label, href]) => (
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
              {copy.hero.badge}
            </div>
            <h1 className="mt-7 max-w-4xl font-heading text-4xl font-semibold leading-[1.08] sm:text-6xl lg:text-7xl">
              {copy.hero.title}
              <span className="block text-muted">{copy.hero.titleAccent}</span>
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-7 text-muted sm:text-lg sm:leading-8">
              {copy.hero.description}
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
                  {copy.actions.seeProduct}
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
                alt={copy.hero.dashboardAlt}
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
              <p className="font-mono text-xs uppercase text-primary">{copy.flow.eyebrow}</p>
              <h2 className="mt-4 font-heading text-3xl font-semibold sm:text-5xl">
                {copy.flow.title}
              </h2>
              <p className="mt-5 text-base leading-7 text-muted sm:text-lg">
                {copy.flow.description}
              </p>
            </div>

            <div
              data-flow-grid
              className="mt-14 grid border-y border-border md:grid-cols-3 md:divide-x md:divide-border"
            >
              {copy.flow.steps.map((step, index) => {
                const Icon = stepIcons[index];
                return (
                  <article
                    key={step.title}
                    data-flow-step
                    className="border-b border-border py-8 last:border-b-0 md:border-b-0 md:px-8 md:first:pl-0 md:last:pr-0"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-muted">
                        {String(index + 1).padStart(2, "0")}
                      </span>
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
              <p className="font-mono text-xs uppercase text-warm">{copy.study.eyebrow}</p>
              <h2 className="mt-4 font-heading text-3xl font-semibold sm:text-5xl">
                {copy.study.title}
              </h2>
              <p className="mt-5 text-base leading-7 text-muted sm:text-lg">
                {copy.study.description}
              </p>
            </div>

            <div data-reveal className="relative mt-14">
              <div className="overflow-hidden border border-border bg-surface p-1 shadow-premium">
                <Image
                  src="/product/study-transcript.png"
                  alt={copy.study.desktopAlt}
                  width={1440}
                  height={1024}
                  className="h-auto w-full"
                />
              </div>
              <div className="absolute -bottom-8 right-4 hidden w-[210px] overflow-hidden border border-border bg-surface p-1 shadow-premium sm:block lg:right-10 lg:w-[260px]">
                <Image
                  src="/product/study-mobile.png"
                  alt={copy.study.mobileAlt}
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
              {copy.study.benefits.map((item) => (
                <div key={item} className="flex items-center gap-3 text-sm text-muted">
                  <span className="flex size-5 items-center justify-center border border-success/40 text-success">
                    <Check className="size-3" />
                  </span>
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24 sm:py-32">
          <div data-reveal className="mx-auto max-w-4xl px-5 text-center sm:px-8">
            <p className="font-mono text-xs uppercase text-muted">{copy.closing.eyebrow}</p>
            <h2 className="mt-5 font-heading text-3xl font-semibold sm:text-5xl">
              {copy.closing.title}
              <span className="block text-muted">{copy.closing.titleAccent}</span>
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
          <p className="text-xs text-muted">{copy.footer.description}</p>
          <div className="flex gap-5 text-xs text-muted">
            <Link href="/login" className="hover:text-foreground">
              {copy.navigation.signIn}
            </Link>
            <Link href="/register" className="hover:text-foreground">
              {copy.actions.createAccount}
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

type LanguageSelectorProps = {
  locale: LandingLocale;
  label: string;
  portugueseLabel: string;
  englishLabel: string;
  onSelect: (locale: LandingLocale) => void;
  compact?: boolean;
};

function LanguageSelector({
  locale,
  label,
  portugueseLabel,
  englishLabel,
  onSelect,
  compact = false,
}: LanguageSelectorProps) {
  return (
    <div
      className="flex h-8 items-center border border-border bg-surface p-0.5"
      role="group"
      aria-label={label}
    >
      {(
        [
          ["pt", "PT", portugueseLabel],
          ["en", "EN", englishLabel],
        ] as const
      ).map(([value, shortLabel, accessibleLabel]) => (
        <button
          key={value}
          type="button"
          className={`flex h-7 min-w-8 items-center justify-center px-2 font-mono text-[10px] transition-colors ${
            locale === value
              ? "bg-white/[0.08] text-foreground"
              : "text-muted hover:text-foreground"
          } ${compact ? "px-1.5" : ""}`}
          onClick={() => onSelect(value)}
          aria-label={accessibleLabel}
          aria-pressed={locale === value}
        >
          {shortLabel}
        </button>
      ))}
    </div>
  );
}
