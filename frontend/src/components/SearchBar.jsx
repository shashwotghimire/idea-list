import { Search } from "lucide-react";

import { Input } from "./ui/input";

export default function SearchBar({ value, onChange }) {
  return (
    <label className="relative block">
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search title or problem"
        className="pl-9"
      />
    </label>
  );
}
