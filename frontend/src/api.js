const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function withQuery(path, query) {
  const url = new URL(path, API_BASE);
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

export async function fetchIdeas(params = {}) {
  const response = await fetch(withQuery("/ideas", params));
  if (!response.ok) {
    throw new Error("Failed to fetch ideas");
  }
  return response.json();
}

export async function fetchTags() {
  const response = await fetch(withQuery("/tags", {}));
  if (!response.ok) {
    throw new Error("Failed to fetch tags");
  }
  return response.json();
}
