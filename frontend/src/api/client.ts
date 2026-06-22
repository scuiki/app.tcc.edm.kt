// Same-origin fetch helper. The Vite dev server proxies /assignments and /dashboard/* to the
// internal uvicorn (D-01/D-04), so the browser always talks to its own origin — no base URL, no CORS,
// no stateful HTTP client. Mirrors the backend's one-resource-per-request discipline (deps.get_conn):
// one fetch per path.

export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json() as Promise<T>;
}
