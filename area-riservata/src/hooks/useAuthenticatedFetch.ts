"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState, useCallback } from "react";

/** Esegue fetch solo quando la sessione è attiva; evita dati vuoti al primo render. */
export function useAuthenticatedFetch<T>(
  fetcher: () => Promise<T | null>,
  deps: unknown[] = []
) {
  const { status } = useSession();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const reload = useCallback(() => {
    if (status !== "authenticated") return;
    setLoading(true);
    setError(false);
    fetcher()
      .then((d) => {
        if (d === null) setError(true);
        setData(d);
      })
      .finally(() => setLoading(false));
  }, [status, fetcher]);

  useEffect(() => {
    if (status === "loading") return;
    if (status !== "authenticated") {
      setLoading(false);
      return;
    }
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, reload, ...deps]);

  return { data, loading, error, reload, isAuthenticated: status === "authenticated" };
}
