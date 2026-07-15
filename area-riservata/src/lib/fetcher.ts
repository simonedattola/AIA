/** Fetch autenticato verso le API interne. */
export async function apiFetch<T>(url: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(url, {
      ...init,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
    if (!res.ok) {
      console.error(`API ${url}:`, res.status);
      return null;
    }
    return (await res.json()) as T;
  } catch (e) {
    console.error(`API ${url}:`, e);
    return null;
  }
}
