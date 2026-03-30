import { ExternalLink, UserRound } from "lucide-react";

import { Badge } from "./ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";

function sourceLabel(source) {
  return source === "reddit" ? "Reddit" : "GitHub";
}

export default function IdeaCard({ idea }) {
  return (
    <Card className="h-full border-white/70 bg-white/75 transition hover:-translate-y-0.5 hover:shadow-md">
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="text-balance text-xl leading-snug">{idea.title}</CardTitle>
          <Badge variant="secondary" className="shrink-0">
            {idea.difficulty}
          </Badge>
        </div>
        <CardDescription className="line-clamp-3 text-sm leading-relaxed">
          {idea.problem || "No summary available."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <UserRound className="h-4 w-4" />
          <span>{idea.audience || "General builders"}</span>
        </p>

        <div className="flex flex-wrap gap-2">
          {idea.tags?.map((tag) => (
            <Badge key={tag} variant="outline">
              #{tag}
            </Badge>
          ))}
        </div>

        <a
          href={idea.source_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
        >
          {sourceLabel(idea.source)}
          <ExternalLink className="h-4 w-4" />
        </a>
      </CardContent>
    </Card>
  );
}
