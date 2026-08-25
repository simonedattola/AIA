import { useEffect, useState } from "react";
import { fetchPage, fetchStats } from "./api";

export function useCmsPage(slug) {
  const [page, setPage] = useState(undefined);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    setPage(undefined);
    setStats(null);
    let cancelled = false;
    // Non bloccare il render della pagina su /stats (può richiedere secondi).
    fetchPage(slug)
      .catch(() => null)
      .then((p) => {
        if (!cancelled) setPage(p);
      });
    fetchStats()
      .catch(() => null)
      .then((s) => {
        if (!cancelled) setStats(s);
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  return { page, stats, loading: page === undefined };
}

export function cmsHeaderProps(page, defaults = {}) {
  return {
    eyebrow: page?.eyebrow || defaults.eyebrow || "",
    title: page?.heading || page?.title || defaults.title || "",
    description: page?.summary || defaults.description || "",
    bg: page?.image || defaults.bg || "",
  };
}
