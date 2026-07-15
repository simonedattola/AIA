"use client";

import Image from "next/image";
import { useEffect, useState, useCallback } from "react";
import { useSession } from "next-auth/react";
import toast from "react-hot-toast";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader, PageError } from "@/components/ui/PageLoader";

type MediaItem = { id: string; titolo: string; url: string };
type Pref = { id: string; elementoId: string };

export default function MediaPage() {
  const { status } = useSession();
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [preferiti, setPreferiti] = useState<Pref[]>([]);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    const d = await apiFetch<{ media: MediaItem[]; preferiti: Pref[] }>("/api/media");
    if (!d) {
      setError(true);
      return;
    }
    setMedia(d.media);
    setPreferiti(d.preferiti);
  }, []);

  useEffect(() => {
    if (status === "authenticated") load();
  }, [status, load]);

  const toggle = async (id: string) => {
    const exists = preferiti.find((p) => p.elementoId === id);
    if (exists) {
      await fetch(`/api/preferiti?id=${exists.id}`, { method: "DELETE", credentials: "same-origin" });
    } else {
      await fetch("/api/preferiti", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ tipo: "MEDIA", elementoId: id }),
      });
    }
    toast.success(exists ? "Rimosso" : "Salvato nei preferiti");
    load();
  };

  if (status === "loading") return <PageLoader />;
  if (error) return <PageError />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-blue-900">Media personale</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {media.map((m) => (
          <div key={m.id} className="card overflow-hidden p-0">
            <div className="relative aspect-video bg-slate-200">
              <Image src={m.url} alt={m.titolo} fill className="object-cover" unoptimized />
            </div>
            <div className="p-3">
              <p className="font-medium">{m.titolo}</p>
              <div className="mt-2 flex gap-2">
                <a href={m.url} target="_blank" rel="noreferrer" className="btn-secondary text-xs">
                  Apri
                </a>
                <button type="button" className="btn-secondary text-xs" onClick={() => toggle(m.id)}>
                  {preferiti.some((p) => p.elementoId === m.id) ? "★" : "☆"}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {media.length === 0 && <p className="text-slate-500">Nessun media disponibile.</p>}
    </div>
  );
}
