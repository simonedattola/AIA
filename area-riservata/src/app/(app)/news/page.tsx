"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { formatDate } from "@/lib/utils";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader, PageError } from "@/components/ui/PageLoader";

type FeedItem = {
  id: string;
  titolo: string;
  contenuto: string;
  createdAt: string;
  tipo: "news" | "successo" | "categoria";
};

const badges = { news: "Citazione", successo: "Successo", categoria: "Categoria" };

export default function NewsPage() {
  const { status } = useSession();
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (status !== "authenticated") return;
    apiFetch<FeedItem[]>("/api/news").then((d) => {
      if (!d) setError(true);
      else setFeed(d);
    });
  }, [status]);

  if (status === "loading") return <PageLoader />;
  if (error) return <PageError />;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-blue-900">News personalizzate</h1>
      <p className="text-sm text-slate-600">
        Articoli con citazioni, successi personali e news della tua categoria.
      </p>
      <div className="space-y-4">
        {feed.map((item) => (
          <article key={`${item.tipo}-${item.id}`} className="card">
            <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-900">
              {badges[item.tipo]}
            </span>
            <h2 className="mt-2 text-lg font-semibold">{item.titolo}</h2>
            <p className="mt-2 text-sm text-slate-700">{item.contenuto}</p>
            <p className="mt-2 text-xs text-slate-500">{formatDate(item.createdAt)}</p>
          </article>
        ))}
        {feed.length === 0 && <p className="text-slate-500">Nessuna news al momento.</p>}
      </div>
    </div>
  );
}
