"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatDateTime } from "@/lib/utils";

type Notifica = {
  id: string;
  testo: string;
  tipo: string;
  link: string | null;
  letta: boolean;
  createdAt: string;
};

export function NotificationDropdown() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notifica[]>([]);

  const load = async () => {
    const res = await fetch("/api/notifiche");
    if (res.ok) setItems(await res.json());
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const unread = items.filter((n) => !n.letta).length;

  const markRead = async (id: string) => {
    await fetch("/api/notifiche", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, letta: true }),
    });
    load();
  };

  const remove = async (id: string) => {
    await fetch(`/api/notifiche?id=${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="btn-secondary relative !min-w-[44px] !px-3"
        aria-label="Notifiche"
      >
        🔔
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-600 text-xs text-white">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-50 mt-2 w-[min(100vw-2rem,24rem)] rounded-xl border bg-white shadow-lg">
            <div className="border-b px-4 py-3 font-semibold">Notifiche</div>
            <ul className="max-h-80 overflow-y-auto">
              {items.length === 0 && (
                <li className="px-4 py-6 text-center text-sm text-slate-500">Nessuna notifica</li>
              )}
              {items.map((n) => (
                <li key={n.id} className={`border-b px-4 py-3 text-sm ${n.letta ? "opacity-60" : ""}`}>
                  <p>{n.testo}</p>
                  <p className="mt-1 text-xs text-slate-500">{formatDateTime(n.createdAt)}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {n.link && (
                      <Link href={n.link} className="text-xs text-blue-800 underline" onClick={() => setOpen(false)}>
                        Apri
                      </Link>
                    )}
                    {!n.letta && (
                      <button type="button" className="text-xs text-blue-800" onClick={() => markRead(n.id)}>
                        Segna letta
                      </button>
                    )}
                    <button type="button" className="text-xs text-red-600" onClick={() => remove(n.id)}>
                      Elimina
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
