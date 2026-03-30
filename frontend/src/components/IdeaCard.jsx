import { ExternalLink, UserRound } from "lucide-react";

import { Badge } from "./ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";

function sourceLabel(source) {
  return source === "reddit" ? "Reddit" : "GitHub";
}

function compact(value, max = 120) {
  const cleaned = String(value || "").replace(/\s+/g, " ").trim();
  if (cleaned.length <= max) {
    return cleaned;
  }
  return `${cleaned.slice(0, max - 1)}...`;
}

export default function IdeaCard({ idea, onOpen }) {
  const handleOpen = () => onOpen(idea);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          handleOpen();
        }
      }}
      className="h-full text-left"
    >
      <Card className="group h-full border-border/60 bg-card/80 transition duration-300 hover:-translate-y-1 hover:shadow-xl">
      <CardHeader className="space-y-3 pb-4">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="line-clamp-3 text-balance text-xl leading-snug tracking-tight">
            {compact(idea.title, 86)}
          </CardTitle>
          <Badge variant="secondary" className="shrink-0 rounded-full px-2.5 py-1 text-[11px] uppercase tracking-wide">
            {idea.difficulty}
          </Badge>
        </div>
        <CardDescription className="line-clamp-3 text-sm leading-relaxed text-muted-foreground">
          {compact(idea.problem, 180) || "No idea summary available."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <p className="flex items-start gap-2 text-sm text-muted-foreground">
          <UserRound className="h-4 w-4" />
          <span className="line-clamp-2">{compact(idea.audience, 92) || "Product teams and operators"}</span>
        </p>

        <div className="flex flex-wrap gap-2">
          {idea.tags?.map((tag) => (
            <Badge key={tag} variant="outline">
              #{tag}
            </Badge>
          ))}
        </div>

        <div className="flex items-center justify-between gap-3">
          <a
            href={idea.source_url}
            target="_blank"
            rel="noreferrer"
            onClick={(event) => event.stopPropagation()}
            className="inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
          >
            {sourceLabel(idea.source)}
            <ExternalLink className="h-4 w-4" />
          </a>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground group-hover:text-foreground">
            Open details
          </span>
        </div>
      </CardContent>
      </Card>
    </div>
  );
}
