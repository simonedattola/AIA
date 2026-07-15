import { useEffect, useState } from "react";
import { fetchPage, fetchStats } from "./api";

export function useCmsPage(slug) {
  const [page, setPage] = useState(undefined);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    setPage(undefined);
    Promise.all([fetchPage(slug).catch(() => null), fetchStats().catch(() => null)]).then(([p, s]) => {
      setPage(p);
      setStats(s);
    });
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
