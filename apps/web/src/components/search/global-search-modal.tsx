"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Clock3, Command, FileSearch, Loader2, Search, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";

import type { SearchKind, SearchResult, SearchResultClickPayload, SearchQuery } from "@recall/shared";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  getRecentSearches,
  recordSearchClick,
  saveRecentSearch,
  searchLearningContent,
} from "@/lib/api/search";
import { cn, formatTimestamp } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";

const searchKinds: Array<{ value: SearchKind; label: string }> = [
  { value: "all", label: "All" },
  { value: "transcript", label: "Transcripts" },
  { value: "note", label: "Notes" },
  { value: "summary", label: "Summaries" },
  { value: "concept", label: "Concepts" },
  { value: "important_moment", label: "Important Moments" },
];

const openSearchEvent = "recall:open-search";

export function GlobalSearchModal() {
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<SearchKind>("all");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [recentSearches, setRecentSearches] = useState<SearchQuery[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const deferredQuery = useDeferredValue(query.trim());

  const shouldSearch = deferredQuery.length >= 2;
  const canLoadMore = results.length < total;

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
      }
    }

    function onOpenSearch() {
      setOpen(true);
    }

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener(openSearchEvent, onOpenSearch);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener(openSearchEvent, onOpenSearch);
    };
  }, []);

  useEffect(() => {
    if (!open || !token) return;
    const timer = window.setTimeout(() => inputRef.current?.focus(), 30);
    void getRecentSearches(token)
      .then(setRecentSearches)
      .catch(() => undefined);
    return () => window.clearTimeout(timer);
  }, [open, token]);

  useEffect(() => {
    if (!open || !token) return;
    if (!shouldSearch) {
      setResults([]);
      setTotal(0);
      setPage(1);
      setLoading(false);
      setError(null);
      setSelectedIndex(0);
      return;
    }

    const timeout = window.setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await searchLearningContent(token, {
          q: deferredQuery,
          kind,
          page: 1,
          per_page: 8,
        });
        setResults(response.hits);
        setTotal(response.total);
        setPage(1);
        setSelectedIndex(0);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Search is unavailable.");
      } finally {
        setLoading(false);
      }
    }, 180);

    return () => window.clearTimeout(timeout);
  }, [deferredQuery, kind, open, shouldSearch, token]);

  const visibleItems = useMemo(() => {
    if (shouldSearch) {
      return results.map((item) => ({ key: item.id, type: "result" as const, item }));
    }
    return recentSearches.map((item) => ({ key: item.id, type: "recent" as const, item }));
  }, [recentSearches, results, shouldSearch]);

  async function openResult(result: SearchResult) {
    if (!token) return;
    const nextQuery = query.trim();
    if (nextQuery) {
      await Promise.allSettled([
        saveRecentSearch(token, { query: nextQuery }),
        recordSearchClick(token, toClickPayload(nextQuery, result)),
      ]);
    }

    const params = new URLSearchParams();
    params.set("video", result.video_id);
    params.set("tab", result.target_tab);
    if (typeof result.timestamp === "number" && result.timestamp > 0) {
      params.set("t", String(Math.floor(result.timestamp)));
    }
    params.set("q", nextQuery || result.title);
    setOpen(false);
    router.push(`/spaces/${result.space_id}?${params.toString()}`);
  }

  async function loadMore() {
    if (!token || !shouldSearch || loading || !canLoadMore) return;
    setLoading(true);
    try {
      const nextPage = page + 1;
      const response = await searchLearningContent(token, {
        q: deferredQuery,
        kind,
        page: nextPage,
        per_page: 8,
      });
      setResults((current) => [...current, ...response.hits]);
      setPage(nextPage);
      setTotal(response.total);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Search is unavailable.");
    } finally {
      setLoading(false);
    }
  }

  async function applyRecentSearch(item: SearchQuery) {
    setQuery(item.query);
    setKind("all");
    setSelectedIndex(0);
    inputRef.current?.focus();
  }

  function onInputKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (!visibleItems.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSelectedIndex((current) => Math.min(current + 1, visibleItems.length - 1));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setSelectedIndex((current) => Math.max(current - 1, 0));
      return;
    }
    if (event.key !== "Enter") return;

    const selected = visibleItems[selectedIndex];
    if (!selected) return;
    event.preventDefault();
    if (selected.type === "recent") {
      void applyRecentSearch(selected.item);
      return;
    }
    void openResult(selected.item);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-4xl border-border bg-background/95 p-0 backdrop-blur-2xl">
        <DialogHeader className="border-b border-border px-6 pb-4 pt-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <DialogTitle className="flex items-center gap-2 text-xl">
                <Search className="size-5 text-primary" />
                Search Your Learning Knowledge
              </DialogTitle>
              <DialogDescription className="mt-1">
                Find transcript sections, AI summaries, notes, concepts, and important moments instantly.
              </DialogDescription>
            </div>
            <div className="hidden items-center gap-2 rounded-md border border-border bg-surface/80 px-3 py-2 text-xs text-muted sm:flex">
              <Command className="size-3.5" />
              Cmd/Ctrl + K
            </div>
          </div>
        </DialogHeader>

        <div className="px-6 pb-6 pt-4">
          <div className="rounded-xl border border-border bg-surface/70 p-3 shadow-insetPanel">
            <div className="flex items-center gap-3 rounded-lg border border-border bg-background/80 px-4 py-3">
              <Search className="size-4 text-primary" />
              <Input
                ref={inputRef}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={onInputKeyDown}
                placeholder="Search a concept, explanation, note, or timestamped moment..."
                className="h-auto border-0 bg-transparent px-0 py-0 text-base shadow-none focus-visible:ring-0"
              />
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {searchKinds.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setKind(option.value)}
                  className={cn(
                    "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                    kind === option.value
                      ? "border-primary/40 bg-primary/10 text-foreground"
                      : "border-border bg-background/70 text-muted hover:border-primary/25 hover:text-foreground",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-5 min-h-[360px]">
            {loading ? (
              <ModalState
                icon={<Loader2 className="size-5 animate-spin" />}
                title="Searching your knowledge base..."
                body="Looking across transcripts, summaries, notes, concepts, and important moments."
              />
            ) : error ? (
              <ModalState
                icon={<FileSearch className="size-5" />}
                title="Search is temporarily unavailable."
                body={error}
              />
            ) : shouldSearch && results.length === 0 ? (
              <ModalState
                icon={<FileSearch className="size-5" />}
                title="No learning content matched your search."
                body="Try a broader term, switch the filter, or search using a concept from the transcript."
              />
            ) : !shouldSearch && recentSearches.length === 0 ? (
              <ModalState
                icon={<Sparkles className="size-5" />}
                title="Search across everything you learned"
                body="Press Cmd/Ctrl + K anytime to jump to concepts, transcript explanations, notes, and important moments."
              />
            ) : (
              <div className="grid gap-3">
                {!shouldSearch ? (
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted">Recent searches</p>
                ) : (
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted">
                    {total} result{total === 1 ? "" : "s"}
                  </p>
                )}

                <AnimatePresence initial={false}>
                  {visibleItems.map((entry, index) =>
                    entry.type === "recent" ? (
                      <motion.button
                        key={entry.key}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        type="button"
                        onClick={() => void applyRecentSearch(entry.item)}
                        className={cn(
                          "flex items-center justify-between rounded-lg border px-4 py-3 text-left transition-colors",
                          index === selectedIndex
                            ? "border-primary/40 bg-primary/10"
                            : "border-border bg-surface/70 hover:border-primary/25 hover:bg-white/[0.04]",
                        )}
                      >
                        <span className="flex items-center gap-3 text-sm text-foreground">
                          <Clock3 className="size-4 text-primary" />
                          {entry.item.query}
                        </span>
                        <span className="text-xs text-muted">Reuse search</span>
                      </motion.button>
                    ) : (
                      <SearchResultCard
                        key={entry.key}
                        result={entry.item}
                        isActive={index === selectedIndex}
                        onOpen={() => void openResult(entry.item)}
                      />
                    ),
                  )}
                </AnimatePresence>

                {shouldSearch && canLoadMore ? (
                  <div className="pt-2">
                    <Button type="button" variant="secondary" onClick={() => void loadMore()} disabled={loading}>
                      {loading ? <Loader2 className="animate-spin" /> : null}
                      Load more
                    </Button>
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function SearchResultCard({
  result,
  isActive,
  onOpen,
}: {
  result: SearchResult;
  isActive: boolean;
  onOpen: () => void;
}) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      type="button"
      onClick={onOpen}
      className={cn(
        "rounded-xl border p-4 text-left transition-colors",
        isActive
          ? "border-primary/45 bg-primary/10"
          : "border-border bg-surface/70 hover:border-primary/25 hover:bg-white/[0.04]",
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-border bg-background/70 px-2 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-muted">
          {formatKind(result.kind)}
        </span>
        <span className="text-xs text-primary">{result.space_title}</span>
        {typeof result.timestamp === "number" && result.timestamp > 0 ? (
          <span className="font-mono text-xs text-muted">{formatTimestamp(result.timestamp)}</span>
        ) : null}
      </div>

      <div className="mt-3 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-foreground">{result.video_title}</p>
          <p className="mt-1 text-xs text-muted">{result.title}</p>
        </div>
        <span className="text-[11px] uppercase tracking-[0.18em] text-muted">
          {Math.round(result.relevance_score * 100)}%
        </span>
      </div>

      <p
        className="mt-3 text-sm leading-6 text-foreground/85"
      >
        {renderHighlightedExcerpt(result.highlighted_excerpt || result.excerpt)}
      </p>
    </motion.button>
  );
}

function ModalState({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="grid min-h-[360px] place-items-center rounded-xl border border-border bg-surface/60 px-6 py-10 text-center shadow-insetPanel">
      <div>
        <div className="mx-auto grid size-12 place-items-center rounded-md border border-border bg-background/80 text-primary">
          {icon}
        </div>
        <h3 className="mt-4 font-heading text-lg font-semibold text-foreground">{title}</h3>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-muted">{body}</p>
      </div>
    </div>
  );
}

function formatKind(kind: SearchKind) {
  return {
    all: "All",
    transcript: "Transcript",
    note: "Note",
    summary: "Summary",
    concept: "Concept",
    important_moment: "Moment",
  }[kind];
}

function toClickPayload(query: string, result: SearchResult): SearchResultClickPayload {
  return {
    query,
    result_kind: result.kind,
    result_id: result.id,
    space_id: result.space_id,
    video_id: result.video_id,
    timestamp: result.timestamp,
  };
}

function renderHighlightedExcerpt(text: string) {
  const parts = text.split(/(<em>.*?<\/em>)/g).filter(Boolean);
  return parts.map((part, index) => {
    if (part.startsWith("<em>") && part.endsWith("</em>")) {
      return (
        <em
          key={`${index}-${part}`}
          className="rounded-sm bg-warm/20 px-0.5 not-italic text-foreground"
        >
          {part.slice(4, -5)}
        </em>
      );
    }
    return <span key={`${index}-${part}`}>{part}</span>;
  });
}

export function openGlobalSearch() {
  window.dispatchEvent(new Event(openSearchEvent));
}