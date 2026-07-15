"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { formatDate } from "@/lib/utils";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader, PageError } from "@/components/ui/PageLoader";

type Gara = {
  id: string;
  categoria: string;
  girone: string | null;
  ruolo: string;
  squadraCasa: string;
  squadraTrasf: string;
  dataGara: string;
  risultato: string | null;
};

type StoricoData = {
  gare: Gara[];
  stats: { totale: number; stagione: number; categorie: string[]; mediaMese: string };
  chartData: { mese: string; totale: number }[];
  stagioni: string[];
};

export default function StoricoPage() {
  const { status } = useSession();
  const [stagione, setStagione] = useState("");
  const [data, setData] = useState<StoricoData | null>(null);
  const [error, setError] = useState(false);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (status !== "authenticated") return;
    const q = stagione ? `?stagione=${encodeURIComponent(stagione)}` : "";
    apiFetch<StoricoData>(`/api/storico${q}`).then((d) => {
      if (!d) {
        setError(true);
        return;
      }
      setError(false);
      setData(d);
      if (!initialized && d.stagioni.length > 0) {
        setStagione(d.stagioni[0]);
        setInitialized(true);
      }
    });
  }, [status, stagione, initialized]);

  if (status === "loading") return <PageLoader />;
  if (error || !data) return <PageError />;

  const { gare, stats, chartData, stagioni } = data;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-blue-900">Storico arbitrale</h1>

      <div className="flex flex-wrap gap-4">
        <select
          className="input max-w-xs"
          value={stagione}
          onChange={(e) => setStagione(e.target.value)}
        >
          {stagioni.map((s) => (
            <option key={s} value={s}>
              Stagione {s}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card text-center">
          <p className="text-2xl font-bold text-blue-900">{stats.totale}</p>
          <p className="text-sm text-slate-600">Gare totali</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-bold">{stats.stagione}</p>
          <p className="text-sm text-slate-600">In stagione</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-bold">{stats.categorie.length}</p>
          <p className="text-sm text-slate-600">Categorie</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-bold">{stats.mediaMese}</p>
          <p className="text-sm text-slate-600">Media gare/mese</p>
        </div>
      </div>

      <div className="card min-h-[280px]">
        <h2 className="mb-2 font-semibold">Progressione carriera</h2>
        <div className="h-[220px] w-full min-w-0">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData}>
                <XAxis dataKey="mese" tick={{ fontSize: 10 }} />
                <YAxis allowDecimals={false} width={32} />
                <Tooltip />
                <Bar dataKey="totale" fill="#1e3a8a" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-16 text-center text-sm text-slate-500">Nessun dato per il grafico</p>
          )}
        </div>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full min-w-[600px] text-left text-sm">
          <thead>
            <tr className="border-b text-slate-600">
              <th className="py-2">Data</th>
              <th>Categoria</th>
              <th>Ruolo</th>
              <th>Partita</th>
              <th>Risultato</th>
            </tr>
          </thead>
          <tbody>
            {gare.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  Nessuna gara per questa stagione
                </td>
              </tr>
            )}
            {gare.map((g) => (
              <tr key={g.id} className="border-b">
                <td className="py-2">{formatDate(g.dataGara)}</td>
                <td>{g.categoria}</td>
                <td>{g.ruolo}</td>
                <td>
                  {g.squadraCasa} vs {g.squadraTrasf}
                </td>
                <td>{g.risultato || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
