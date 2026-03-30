import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

const DIFFICULTIES = ["all", "weekend", "1-3 months", "6 months"];
const SOURCES = ["all", "reddit", "github"];

export default function Filters({
  filters,
  tags,
  onDifficultyChange,
  onSourceChange,
  onTagChange,
  onReset,
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Select value={filters.difficulty} onValueChange={onDifficultyChange}>
        <SelectTrigger>
          <SelectValue placeholder="All difficulties" />
        </SelectTrigger>
        <SelectContent>
        {DIFFICULTIES.map((item) => (
          <SelectItem key={item || "all"} value={item}>
            {item === "all" ? "All difficulties" : item}
          </SelectItem>
        ))}
        </SelectContent>
      </Select>

      <Select value={filters.source} onValueChange={onSourceChange}>
        <SelectTrigger>
          <SelectValue placeholder="All sources" />
        </SelectTrigger>
        <SelectContent>
        {SOURCES.map((item) => (
          <SelectItem key={item || "all"} value={item}>
            {item === "all" ? "All sources" : item}
          </SelectItem>
        ))}
        </SelectContent>
      </Select>

      <Input
        list="tags-list"
        value={filters.tag}
        onChange={(event) => onTagChange(event.target.value)}
        placeholder="Filter by tag"
      />
      <datalist id="tags-list">
        {tags.map((tag) => (
          <option key={tag} value={tag} />
        ))}
      </datalist>

      <Button variant="secondary" onClick={onReset}>
        Reset filters
      </Button>
    </div>
  );
}
