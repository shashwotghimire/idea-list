import { useEffect, useMemo, useState } from "react";

import { fetchIdeas, fetchTags } from "./api";
import Filters from "./components/Filters";
import IdeaCard from "./components/IdeaCard";
import SearchBar from "./components/SearchBar";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./components/ui/dialog";
import ThemeToggle from "./components/ui/theme-toggle";

const INITIAL_FILTERS = {
  search: "",
  difficulty: "all",
  source: "all",
  tag: "",
  limit: 20,
  offset: 0,
};

export default function App() {
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [ideas, setIdeas] = useState([]);
  const [total, setTotal] = useState(0);
  const [tags, setTags] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedIdea, setSelectedIdea] = useState(null);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = isDark ? "dark" : "light";
  }, [isDark]);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError("");
    const query = {
      ...filters,
      difficulty: filters.difficulty === "all" ? "" : filters.difficulty,
      source: filters.source === "all" ? "" : filters.source,
    };
    fetchIdeas(query)
      .then((data) => {
        if (cancelled) {
          return;
        }
        setIdeas(data.items ?? []);
        setTotal(data.total ?? 0);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Could not load ideas from the API.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [filters]);

  useEffect(() => {
    fetchTags().then(setTags).catch(() => setTags([]));
  }, []);

  const pageLabel = useMemo(() => {
    const start = filters.offset + 1;
    const end = Math.min(filters.offset + filters.limit, total);
    if (total === 0) {
      return "0 results";
    }
    return `${start}-${end} of ${total}`;
  }, [filters.limit, filters.offset, total]);

  const canGoBack = filters.offset > 0;
  const canGoNext = filters.offset + filters.limit < total;

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-8 space-y-4 rounded-2xl border border-border/70 bg-card/70 p-6 shadow-sm backdrop-blur-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
          <Badge variant="secondary">Daily idea feed</Badge>
          <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            Discover buildable side project ideas.
          </h1>
          <p className="max-w-2xl text-base text-muted-foreground sm:text-lg">
              Curated from Reddit and GitHub, enriched by Kimi, for technical and non-technical audiences.
          </p>
          </div>
          <ThemeToggle dark={isDark} onToggle={() => setIsDark((prev) => !prev)} />
        </div>

        <SearchBar
          value={filters.search}
          onChange={(value) => setFilters((prev) => ({ ...prev, search: value, offset: 0 }))}
        />
        <Filters
          filters={filters}
          tags={tags}
          onDifficultyChange={(difficulty) =>
            setFilters((prev) => ({ ...prev, difficulty, offset: 0 }))
          }
          onSourceChange={(source) => setFilters((prev) => ({ ...prev, source, offset: 0 }))}
          onTagChange={(tag) => setFilters((prev) => ({ ...prev, tag, offset: 0 }))}
          onReset={() => setFilters(INITIAL_FILTERS)}
        />
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm font-medium text-muted-foreground">{pageLabel}</p>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={!canGoBack}
              onClick={() =>
                setFilters((prev) => ({ ...prev, offset: Math.max(prev.offset - prev.limit, 0) }))
              }
            >
              Previous
            </Button>
            <Button
              size="sm"
              disabled={!canGoNext}
              onClick={() => setFilters((prev) => ({ ...prev, offset: prev.offset + prev.limit }))}
            >
              Next
            </Button>
          </div>
        </div>

        {isLoading ? (
          <div className="rounded-xl border border-border/70 bg-card/70 p-8 text-center text-muted-foreground">
            Loading ideas...
          </div>
        ) : null}

        {error ? (
          <div className="rounded-xl border border-destructive/30 bg-red-50/80 p-8 text-center text-destructive">
            {error}
          </div>
        ) : null}

        {!isLoading && !error && ideas.length === 0 ? (
          <div className="rounded-xl border border-border/70 bg-card/70 p-8 text-center text-muted-foreground">
            No ideas match your filters.
          </div>
        ) : null}

        {!isLoading && !error && ideas.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {ideas.map((idea) => (
              <IdeaCard key={idea.id} idea={idea} onOpen={setSelectedIdea} />
            ))}
          </div>
        ) : null}
      </section>

      <Dialog open={Boolean(selectedIdea)} onOpenChange={(open) => !open && setSelectedIdea(null)}>
        <DialogContent>
          {selectedIdea ? (
            <>
              <DialogHeader>
                <DialogTitle>{selectedIdea.title}</DialogTitle>
                <DialogDescription>
                  {selectedIdea.source === "reddit" ? "From Reddit" : "From GitHub"}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 text-sm">
                <p>{selectedIdea.problem}</p>
                <p>
                  <span className="font-medium">Audience:</span> {selectedIdea.audience}
                </p>
                <p>
                  <span className="font-medium">Monetization:</span> {selectedIdea.monetization}
                </p>
                <div className="flex flex-wrap gap-2">
                  {selectedIdea.tags?.map((tag) => (
                    <Badge key={tag} variant="outline">
                      #{tag}
                    </Badge>
                  ))}
                </div>
                <a
                  href={selectedIdea.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline"
                >
                  Open source post/repo
                </a>
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>
    </main>
  );
}
