import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import IdeaCard from "./IdeaCard";

describe("IdeaCard", () => {
  it("renders title", () => {
    render(
      <IdeaCard
        idea={{
          id: 1,
          title: "AI Prompt Library",
          problem: "Teams lose prompts.",
          audience: "Product teams",
          difficulty: "weekend",
          tags: ["ai", "productivity"],
          source: "github",
          source_url: "https://github.com/example/repo",
        }}
      />
    );
    expect(screen.getByText("AI Prompt Library")).toBeInTheDocument();
  });
});
