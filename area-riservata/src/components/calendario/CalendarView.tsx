"use client";

import { Calendar, dateFnsLocalizer, Views } from "react-big-calendar";
import { format, parse, startOfWeek, getDay } from "date-fns";
import { it } from "date-fns/locale";
import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { formatDateTime } from "@/lib/utils";

const locales = { it };
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 1 }),
  getDay,
  locales,
});

type CalEvent = {
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
};

const presenzaOpts = [
  { value: "PRESENTE", label: "Conferma" },
  { value: "ASSENTE", label: "Rifiuta" },
  { value: "IN_DUBBIO", label: "In dubbio" },
];

export function CalendarView({
  events,
  onRefresh,
}: {
  events: CalEvent[];
  onRefresh: () => void;
}) {
  const [selected, setSelected] = useState<CalEvent | null>(null);
  const [view, setView] = useState<typeof Views.MONTH | typeof Views.WEEK>(Views.MONTH);

  const messages = useMemo(
    () => ({
      month: "Mese",
      week: "Settimana",
      today: "Oggi",
      previous: "Prec",
      next: "Succ",
    }),
    []
  );

  const updatePresenza = async (stato: string) => {
    if (!selected?.resource.eventoId) return;
    await fetch("/api/presenze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ eventoId: selected.resource.eventoId, stato }),
    });
    toast.success("Presenza aggiornata");
    onRefresh();
  };

  const addToCalendar = async () => {
    if (!selected?.resource.eventoId) return;
    await fetch("/api/calendario-personale", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ eventoId: selected.resource.eventoId }),
    });
    toast.success("Aggiunto al calendario personale");
    onRefresh();
  };

  const sendReminder = async () => {
    if (!selected?.resource.eventoId) return;
    const res = await fetch("/api/reminder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ eventoId: selected.resource.eventoId }),
    });
    const data = await res.json();
    toast.success(data.emailSent ? "Email inviata" : "Reminder registrato (SMTP non configurato)");
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button type="button" className={view === Views.MONTH ? "btn-primary" : "btn-secondary"} onClick={() => setView(Views.MONTH)}>
          Mese
        </button>
        <button type="button" className={view === Views.WEEK ? "btn-primary" : "btn-secondary"} onClick={() => setView(Views.WEEK)}>
          Settimana
        </button>
      </div>
      <div className="card overflow-x-auto">
        <Calendar
          localizer={localizer}
          culture="it"
          events={events}
          view={view}
          onView={(v) => setView(v as typeof Views.MONTH)}
          messages={messages}
          style={{ height: 520, minWidth: 300 }}
          onSelectEvent={(e) => setSelected(e as CalEvent)}
        />
      </div>

      {selected && (
        <div className="card">
          <h3 className="font-semibold">{selected.title}</h3>
          <p className="text-sm text-slate-600">{formatDateTime(selected.start)}</p>
          {selected.resource.luogo && <p className="text-sm">📍 {selected.resource.luogo}</p>}
          {selected.resource.eventoId && (
            <div className="mt-4 flex flex-wrap gap-2">
              {presenzaOpts.map((o) => (
                <button key={o.value} type="button" className="btn-secondary" onClick={() => updatePresenza(o.value)}>
                  {o.label}
                </button>
              ))}
              <button type="button" className="btn-primary" onClick={addToCalendar}>
                Aggiungi al mio calendario
              </button>
              <button type="button" className="btn-secondary" onClick={sendReminder}>
                Ricevi reminder
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
