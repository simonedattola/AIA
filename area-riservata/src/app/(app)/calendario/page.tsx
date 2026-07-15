"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader } from "@/components/ui/PageLoader";

const CalendarView = dynamic(
  () => import("@/components/calendario/CalendarView").then((m) => m.CalendarView),
  { ssr: false, loading: () => <PageLoader label="Caricamento calendario..." /> }
);

type ApiEvent = {
  id: string;
  titolo: string;
  tipo: string;
  dataInizio: string;
  dataFine: string | null;
  luogo: string | null;
  presenze: { stato: string }[];
  calendario: { id: string }[];
};

type Designazione = {
  id: string;
  campionato: string;
  squadraCasa: string;
  squadraTrasf: string;
  dataGara: string;
  ruolo: string;
  luogo: string | null;
};

export default function CalendarioPage() {
  const { status } = useSession();
  const [calEvents, setCalEvents] = useState<
    {
      id: string;
      title: string;
      start: Date;
      end: Date;
      resource: {
        tipo: string;
        eventoId?: string;
        luogo?: string;
        presenza?: string;
        inCalendario?: boolean;
      };
    }[]
  >([]);

  const load = useCallback(async () => {
    const data = await apiFetch<{ eventi: ApiEvent[]; designazioni: Designazione[] }>("/api/eventi");
    if (!data) return;
    const evts = data.eventi.map((e) => ({
      id: e.id,
      title: `${e.tipo}: ${e.titolo}`,
      start: new Date(e.dataInizio),
      end: new Date(e.dataFine || e.dataInizio),
      resource: {
        tipo: e.tipo,
        eventoId: e.id,
        luogo: e.luogo ?? undefined,
        presenza: e.presenze[0]?.stato,
        inCalendario: e.calendario.length > 0,
      },
    }));
    const des = data.designazioni.map((d) => ({
      id: `des-${d.id}`,
      title: `Designazione: ${d.squadraCasa} vs ${d.squadraTrasf}`,
      start: new Date(d.dataGara),
      end: new Date(d.dataGara),
      resource: { tipo: "DESIGNAZIONE", luogo: d.luogo ?? undefined },
    }));
    setCalEvents([...evts, ...des]);
  }, []);

  useEffect(() => {
    if (status === "authenticated") load();
  }, [status, load]);

  if (status === "loading") return <PageLoader />;
  if (status !== "authenticated") return null;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-blue-900">Calendario personale</h1>
      <p className="text-sm text-slate-600">
        Raduni, RTO, allenamenti, eventi sezionali e designazioni. Seleziona un evento per gestire la presenza.
      </p>
      <CalendarView events={calEvents} onRefresh={load} />
    </div>
  );
}
