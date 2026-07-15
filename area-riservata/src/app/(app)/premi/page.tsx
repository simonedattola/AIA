"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { formatDate } from "@/lib/utils";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader, PageError } from "@/components/ui/PageLoader";

type Traguardo = {
  id: string;
  tipo: string;
  data: string;
  descrizione: string;
  icona: string | null;
};

export default function PremiPage() {
  const { status } = useSession();
  const [traguardi, setTraguardi] = useState<Traguardo[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (status !== "authenticated") return;
    apiFetch<Traguardo[]>("/api/premi").then((d) => {
      if (!d) setError(true);
      else setTraguardi(d);
    });
  }, [status]);

  if (status === "loading") return <PageLoader />;
  if (error) return <PageError />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-blue-900">Premi & traguardi</h1>
      <div className="grid gap-4 sm:grid-cols-2">
        {traguardi.map((t) => (
          <div key={t.id} className="card flex gap-4">
            <span className="text-4xl">{t.icona || "🏆"}</span>
            <div>
              <p className="text-xs uppercase text-slate-500">{t.tipo}</p>
              <h2 className="font-semibold">{t.descrizione}</h2>
              <p className="text-sm text-slate-600">{formatDate(t.data)}</p>
            </div>
          </div>
        ))}
      </div>
      {traguardi.length === 0 && <p className="text-slate-500">Nessun traguardo registrato.</p>}
    </div>
  );
}
