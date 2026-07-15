"use client";

import { useEffect, useState, useCallback } from "react";
import { useSession } from "next-auth/react";
import { formatDateTime } from "@/lib/utils";
import toast from "react-hot-toast";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader, PageError } from "@/components/ui/PageLoader";

type Partner = { id: string; nome: string; cognome: string; ruolo: string };
type Msg = { id: string; testo: string; mittenteId: string; createdAt: string; letto: boolean };
type Conv = { partner: Partner; messaggi: Msg[]; nonLetti: number };

export default function MessaggiPage() {
  const { status } = useSession();
  const [conversazioni, setConversazioni] = useState<Conv[]>([]);
  const [staff, setStaff] = useState<Partner[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [testo, setTesto] = useState("");
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    const d = await apiFetch<{ conversazioni: Conv[]; staff: Partner[] }>("/api/messaggi");
    if (!d) {
      setError(true);
      return;
    }
    setConversazioni(d.conversazioni);
    setStaff(d.staff);
  }, []);

  useEffect(() => {
    if (status !== "authenticated") return;
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [status, load]);

  const activeConv = conversazioni.find((c) => c.partner.id === active);

  const send = async () => {
    if (!active || !testo.trim()) return;
    const res = await fetch("/api/messaggi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ destinatarioId: active, testo }),
    });
    if (res.ok) {
      setTesto("");
      load();
      toast.success("Messaggio inviato");
    } else toast.error("Invio non riuscito");
  };

  const openChat = async (id: string) => {
    setActive(id);
    await fetch("/api/messaggi", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ partnerId: id }),
    });
    load();
  };

  if (status === "loading") return <PageLoader />;
  if (error) return <PageError />;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4 lg:flex-row">
      <aside className="card w-full overflow-y-auto lg:w-80">
        <h2 className="font-semibold">Conversazioni</h2>
        <ul className="mt-3 space-y-1">
          {staff.map((s) => (
            <li key={s.id}>
              <button
                type="button"
                className={`w-full rounded-lg px-3 py-3 text-left text-sm ${
                  active === s.id ? "bg-blue-900 text-white" : "hover:bg-slate-100"
                }`}
                onClick={() => openChat(s.id)}
              >
                {s.nome} {s.cognome}
                <span className="block text-xs opacity-70">{s.ruolo}</span>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <div className="card flex flex-1 flex-col min-h-[320px]">
        {activeConv ? (
          <>
            <h2 className="border-b pb-2 font-semibold">
              {activeConv.partner.nome} {activeConv.partner.cognome}
            </h2>
            <div className="flex-1 space-y-2 overflow-y-auto py-4">
              {activeConv.messaggi.map((m) => (
                <div key={m.id} className="rounded-lg bg-slate-100 px-3 py-2 text-sm">
                  <p>{m.testo}</p>
                  <p className="text-xs text-slate-500">{formatDateTime(m.createdAt)}</p>
                </div>
              ))}
            </div>
            <div className="flex gap-2 border-t pt-3">
              <input
                className="input flex-1"
                value={testo}
                onChange={(e) => setTesto(e.target.value)}
                placeholder="Scrivi un messaggio..."
                onKeyDown={(e) => e.key === "Enter" && send()}
              />
              <button type="button" className="btn-primary" onClick={send}>
                Invia
              </button>
            </div>
          </>
        ) : (
          <p className="text-slate-500">Seleziona una conversazione con consiglio o osservatori.</p>
        )}
      </div>
    </div>
  );
}
