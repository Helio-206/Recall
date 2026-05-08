"use client";

import type { ElementType } from "react";

import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowUpRight,
  BookMarked,
  BrainCircuit,
  Captions,
  Search,
  Target,
} from "lucide-react";

const WORKSPACE_ITEMS = [
  {
    title: "Saved with context",
    body: "The capture remembers where the lesson belongs, not just the raw URL.",
    icon: BookMarked,
  },
  {
    title: "Searchable later",
    body: "Find the exact explanation across transcript, note, and summary.",
    icon: Search,
  },
  {
    title: "Rebuilt by AI",
    body: "Modules and next steps emerge from the content you already collected.",
    icon: BrainCircuit,
  },
  {
    title: "Made to finish",
    body: "Progress stays visible so attention does not dissolve after the first save.",
    icon: Target,
  },
] as const;

const SEARCH_RESULTS = [
  ["14:08", "Transcript hit", "Dependency inversion is introduced through a concrete contrast."],
  ["22:31", "Summary", "Architecture principle connected to maintainable module boundaries."],
  ["28:40", "Saved note", "Timestamped insight recovered later from search."],
] as const;

export function ProductPreview() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div className="relative mx-auto w-full max-w-6xl px-1 sm:px-4">
      <div className="pointer-events-none absolute inset-x-8 top-10 h-64 rounded-full bg-[radial-gradient(circle,rgba(125,93,255,0.36),rgba(7,7,13,0)_68%)] blur-3xl" />

      <div className="relative mx-auto max-w-5xl">
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: 28, scale: 0.96 }}
          animate={prefersReducedMotion ? undefined : { opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="relative"
        >
          <motion.div
            animate={prefersReducedMotion ? undefined : { y: [0, 16, 0] }}
            transition={{ duration: 5.8, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
            className="absolute inset-x-8 top-12 h-[82%] rounded-[34px] border border-white/8 bg-[linear-gradient(180deg,rgba(40,45,78,0.34),rgba(8,9,16,0.4))]"
          />
          <motion.div
            animate={prefersReducedMotion ? undefined : { y: [0, 10, 0] }}
            transition={{ duration: 4.8, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut", delay: 0.2 }}
            className="absolute inset-x-4 top-6 h-[90%] rounded-[34px] border border-white/10 bg-[linear-gradient(180deg,rgba(61,66,118,0.32),rgba(8,9,16,0.48))]"
          />

          <div className="pointer-events-none absolute left-1/2 top-[18%] h-64 w-[72%] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(111,94,255,0.30),rgba(8,9,16,0)_68%)] blur-3xl" />

          <div className="relative overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(180deg,rgba(14,16,26,0.98),rgba(7,8,14,0.96))] shadow-[0_40px_120px_rgba(0,0,0,0.38)] backdrop-blur-2xl">
            <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.38),transparent)]" />

            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4 lg:px-7">
              <div className="flex items-center gap-2">
                <span className="size-2.5 rounded-full bg-white/22" />
                <span className="size-2.5 rounded-full bg-white/12" />
                <span className="size-2.5 rounded-full bg-primary/70" />
              </div>
              <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-white/46">
                Recall learning cockpit
              </div>
            </div>

            <div className="grid gap-6 p-5 lg:grid-cols-[1.02fr_0.98fr] lg:p-7">
              <div className="space-y-4">
                <div className="rounded-[26px] border border-white/10 bg-white/[0.03] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] lg:p-6">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm text-white/48">Learning architecture</p>
                      <h3 className="mt-2 max-w-[14ch] font-heading text-3xl font-semibold leading-tight tracking-[-0.04em] text-white">
                        A workspace that turns captures into mastery.
                      </h3>
                    </div>
                    <span className="grid size-11 place-items-center rounded-2xl border border-white/10 bg-white/[0.04] text-white/60">
                      <ArrowUpRight className="size-5" />
                    </span>
                  </div>

                  <div className="mt-6 grid gap-3 sm:grid-cols-2">
                    {WORKSPACE_ITEMS.map((item) => (
                      <FeatureCard key={item.title} {...item} />
                    ))}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <MetricCard label="Spaces" value="12" />
                  <MetricCard label="Lessons" value="148" />
                  <MetricCard label="Focus" value="84%" />
                </div>
              </div>

              <div className="grid gap-4">
                <div className="rounded-[26px] border border-white/10 bg-white/[0.03] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                  <div className="flex items-center gap-3 text-sm text-white/52">
                    <Search className="size-4 text-primary" />
                    Search inside what you already learned
                  </div>

                  <div className="mt-4 rounded-2xl border border-white/10 bg-[#090b12] px-4 py-3 text-white/84">
                    Where was dependency inversion explained?
                  </div>

                  <div className="mt-4 space-y-3">
                    {SEARCH_RESULTS.map(([time, label, copy]) => (
                      <SearchResult key={time} time={time} label={label} copy={copy} />
                    ))}
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-[0.9fr_1.1fr]">
                  <div className="rounded-[26px] border border-white/10 bg-white/[0.03] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                    <div className="flex items-center gap-3 text-sm text-white/48">
                      <Captions className="size-4 text-violet" />
                      Transcript state
                    </div>
                    <p className="mt-4 font-heading text-4xl font-semibold tracking-[-0.04em] text-white">98%</p>
                    <p className="mt-2 text-sm leading-7 text-white/56">
                      Indexed and ready for retrieval across transcript, notes, and summary.
                    </p>
                  </div>

                  <div className="rounded-[26px] border border-white/10 bg-white/[0.03] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                    <div className="flex items-center gap-3 text-sm text-white/48">
                      <BrainCircuit className="size-4 text-primary" />
                      AI reconstruction
                    </div>
                    <div className="mt-4 space-y-3">
                      <SummaryLine label="Modules" value="Foundations → Search → Practice" />
                      <SummaryLine label="Next step" value="Continue with semantic retrieval lesson" />
                      <SummaryLine label="Review" value="4 prompts generated from today’s captures" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function FeatureCard({
  title,
  body,
  icon: Icon,
}: {
  title: string;
  body: string;
  icon: ElementType;
}) {
  return (
    <div className="rounded-[22px] border border-white/10 bg-[#0a0c14] p-4">
      <div className="flex items-center gap-3 text-white/78">
        <span className="grid size-10 place-items-center rounded-2xl border border-white/10 bg-white/[0.04] text-primary">
          <Icon className="size-4" />
        </span>
        <p className="font-medium text-white">{title}</p>
      </div>
      <p className="mt-3 text-sm leading-7 text-white/54">{body}</p>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4">
      <p className="text-sm text-white/46">{label}</p>
      <p className="mt-4 font-heading text-4xl font-semibold tracking-[-0.05em] text-white">{value}</p>
    </div>
  );
}

function SearchResult({
  time,
  label,
  copy,
}: {
  time: string;
  label: string;
  copy: string;
}) {
  return (
    <div className="rounded-[20px] border border-white/10 bg-[#090b12] p-4">
      <div className="flex items-center justify-between gap-3 text-xs text-white/42">
        <span>{label}</span>
        <span className="font-mono">{time}</span>
      </div>
      <p className="mt-3 text-sm leading-7 text-white/78">{copy}</p>
    </div>
  );
}

function SummaryLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[20px] border border-white/10 bg-[#090b12] p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-white/40">{label}</div>
      <div className="mt-2 text-sm leading-7 text-white/78">{value}</div>
    </div>
  );
}