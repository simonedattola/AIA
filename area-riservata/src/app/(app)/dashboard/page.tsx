"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { formatDate, formatDateTime } from "@/lib/utils";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader, PageError } from "@/components/ui/PageLoader";

type DashboardData = {
  prossimaDesignazione: {
    campionato: string;
    squadraCasa: string;
    squadraTrasf: string;
    dataGara: string;
    ruolo: string;
  } | null;
  prossimiEventi: { id: string; titolo: string; tipo: string; dataInizio: string; luogo: string | null }[];
  newsTecniche: { id: string; titolo: string; createdAt: string }[];
  comunicazioni: { id: string; titolo: string; createdAt: string }[];
  notifiche: { id: string; testo: string; link: string | null }[];
};

export default function DashboardPage() {
  const { status } = useSession();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (status !== "authenticated") return;
    apiFetch<DashboardData>("/api/dashboard").then((d) => {
      if (!d) setError(true);
      else setData(d);
    });
  }, [status]);

  if (status === "loading") return <PageLoader />;
  if (error || !data) return <PageError />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-blue-900">Dashboard</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <section className="card sm:col-span-2 lg:col-span-1">
          <h2 className="font-semibold text-blue-900">Prossima designazione</h2>
          {data.prossimaDesignazione ? (
            <div className="mt-3 text-sm">
              <p className="font-medium">
                {data.prossimaDesignazione.squadraCasa} vs {data.prossimaDesignazione.squadraTrasf}
              </p>
              <p className="text-slate-600">{data.prossimaDesignazione.campionato} — {data.prossimaDesignazione.ruolo}</p>
              <p className="text-slate-500">{formatDateTime(data.prossimaDesignazione.dataGara)}</p>
              <Link href="/calendario" className="mt-2 inline-block text-sm text-blue-800 underline">
                Vai al calendario
              </Link>
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-500">Nessuna designazione in programma</p>
          )}
        </section>

        <section className="card">
          <h2 className="font-semibold">Prossimi eventi</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {data.prossimiEventi.length === 0 && <li className="text-slate-500">Nessun evento</li>}
            {data.prossimiEventi.map((e) => (
              <li key={e.id}>
                <span className="font-medium">{e.titolo}</span>
                <br />
                <span className="text-slate-500">{formatDate(e.dataInizio)}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h2 className="font-semibold">Notifiche importanti</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {data.notifiche.length === 0 && <li className="text-slate-500">Nessuna</li>}
            {data.notifiche.map((n) => (
              <li key={n.id}>
                {n.testo}
                {n.link && (
                  <Link href={n.link} className="ml-1 text-blue-800 underline">
                    →
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h2 className="font-semibold">Ultime news tecniche</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {data.newsTecniche.map((n) => (
              <li key={n.id}>
                <Link href="/news" className="text-blue-800 hover:underline">
                  {n.titolo}
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h2 className="font-semibold">Comunicazioni interne</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {data.comunicazioni.map((c) => (
              <li key={c.id}>
                <span className="font-medium">{c.titolo}</span>
                <br />
                <span className="text-slate-500">{formatDate(c.createdAt)}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
