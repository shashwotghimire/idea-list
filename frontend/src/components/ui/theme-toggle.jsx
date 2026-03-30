import { Moon, Sun } from "lucide-react";

import { Button } from "./button";

export default function ThemeToggle({ dark, onToggle }) {
  return (
    <Button
      type="button"
      variant="secondary"
      size="sm"
      onClick={onToggle}
      className="gap-2"
      aria-label="Toggle color mode"
    >
      <svg viewBox="0 0 40 40" className="h-4 w-4" aria-hidden="true">
        <circle cx="20" cy="20" r="18" fill="currentColor" opacity="0.16" />
        <path d="M20 7L23.6 16.4L33 20L23.6 23.6L20 33L16.4 23.6L7 20L16.4 16.4Z" fill="currentColor" />
      </svg>
      {dark ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
      {dark ? "Dark" : "Light"}
    </Button>
  );
}
