"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import toast from "react-hot-toast";

const stati = ["PRESENTE", "ASSENTE", "IN_DUBBIO", "NON_RISPOSTO"] as const;

type Partecipante = {
  user: { id: string; nome: string; cognome: string; categoria: string | null };
  presenza: { stato: string };
};

export default function AdminPresenzePage() {
  const { eventoId } = useParams<{ eventoId: string }>();
  const [data, setData] = useState<{
    evento: { titolo: string };
    partecipanti: Partecipante[];
    stats: { presentePct: number; assentePct: number; dubbioPct: number; nonRispostoPct: number };
  } | null>(null);

  const load = () =>
    fetch(`/api/admin/presenze/${eventoId}`)
      .then((r) => r.json())
      .then(setData);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventoId]);

  const update = async (userId: string, stato: string) => {
    await fetch(`/api/admin/presenze/${eventoId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId, stato }),
    });
    toast.success("Aggiornato");
    load();
  };

  if (!data) return <p>Caricamento...</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Presenze: {data.evento.titolo}</h1>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="card text-center">Presenti {data.stats.presentePct}%</div>
        <div className="card text-center">Assenti {data.stats.assentePct}%</div>
        <div className="card text-center">Dubbio {data.stats.dubbioPct}%</div>
        <div className="card text-center">NR {data.stats.nonRispostoPct}%</div>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2 text-left">Associato</th>
              <th>Categoria</th>
              <th>Stato</th>
            </tr>
          </thead>
          <tbody>
            {data.partecipanti.map((p) => (
              <tr key={p.user.id} className="border-b">
                <td className="py-2">
                  {p.user.nome} {p.user.cognome}
                </td>
                <td>{p.user.categoria || "—"}</td>
                <td>
                  <select
                    className="input max-w-[160px]"
                    value={p.presenza.stato}
                    onChange={(e) => update(p.user.id, e.target.value)}
                  >
                    {stati.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
