import { useEffect, useMemo, useState } from "react";
import { portalCalendario, portalSetPresenza } from "../../lib/portal-api";
import EventDetailModal from "../../components/events/EventDetailModal";
import PortalEventCard from "../../components/portal/PortalEventCard";
import { eventDateKey } from "../../lib/eventsDisplay";
import { Loader2, UserCheck, UserX } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import { FilterPill, SubsectionTitle } from "@/design-system";
import { PortalEmptyState, PortalPageHeader } from "../../components/portal/portal-ui";

function groupByMonth(events) {
  const groups = [];
  let current = null;
  for (const ev of events) {
    const d = new Date(`${eventDateKey(ev.date)}T12:00:00`);
    const key = `${d.getFullYear()}-${d.getMonth()}`;
    const label = d.toLocaleDateString("it-IT", { month: "long", year: "numeric" });
    if (!current || current.key !== key) {
      current = { key, label, events: [] };
      groups.push(current);
    }
    current.events.push(ev);
  }
  return groups;
}

export default function PortalCalendarioPage() {
  const [items, setItems] = useState([]);
  const [seasonStats, setSeasonStats] = useState({ presenti: 0, assenti: 0, stagione: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(null);
  const [filter, setFilter] = useState("all");
  const [modalEvent, setModalEvent] = useState(null);

  const load = () => {
    setLoading(true);
    setError("");
    return portalCalendario()
      .then((data) => {
        setItems(data.eventi);
        setSeasonStats({
          presenti: data.presenti,
          assenti: data.assenti,
          stagione: data.stagione || "",
        });
      })
      .catch((err) => {
        setItems([]);
        setError(err?.response?.data?.detail || "Impossibile caricare il calendario.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const setStato = async (eventId, stato) => {
    if (saving) return;
    setSaving(eventId);
    try {
      await portalSetPresenza(eventId, stato);
      await load();
    } catch (err) {
      if (err?.response?.status === 409) {
        await load();
        return;
      }
      throw err;
    } finally {
      setSaving(null);
    }
  };

  const needsPresenzaConfirmation = (e) => {
    const s = e.mioStato || "NON_RISPOSTO";
    return s === "NON_RISPOSTO" || s === "IN_DUBBIO";
  };

  const isPresenzaConfirmed = (e) => {
    const s = e.mioStato || "NON_RISPOSTO";
    return s === "PRESENTE" || s === "ASSENTE";
  };

  const pendingCount = useMemo(
    () => items.filter(needsPresenzaConfirmation).length,
    [items]
  );

  const filtered = useMemo(() => {
    if (filter === "pending") {
      return items.filter(needsPresenzaConfirmation);
    }
    if (filter === "confirmed") {
      return items.filter(isPresenzaConfirmed);
    }
    return items;
  }, [items, filter]);

  const groups = useMemo(() => groupByMonth(filtered), [filtered]);

  const filters = [
    { id: "all", label: "Tutti", count: items.length },
    { id: "pending", label: "Da confermare", count: pendingCount },
    { id: "confirmed", label: "Confermati", count: items.length - pendingCount },
  ];

  return (
    <div data-testid="portal-calendario-page">
      <PortalPageHeader
        title="Calendario"
        description="Eventi a cui sei invitato. Conferma la presenza agli appuntamenti."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-center gap-4">
          <div className="h-11 w-11 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
            <UserCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-navy-700 tabular-nums">{seasonStats.presenti}</div>
            <div className="text-sm text-slate-600">Presenze questa stagione</div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-center gap-4">
          <div className="h-11 w-11 rounded-lg bg-red-50 text-red-700 flex items-center justify-center shrink-0">
            <UserX className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-navy-700 tabular-nums">{seasonStats.assenti}</div>
            <div className="text-sm text-slate-600">Assenze questa stagione</div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-6" role="tablist" aria-label="Filtra eventi">
        {filters.map((f) => (
          <FilterPill
            key={f.id}
            role="tab"
            aria-selected={filter === f.id}
            active={filter === f.id}
            onClick={() => setFilter(f.id)}
            data-testid={`portal-calendario-filter-${f.id}`}
          >
            {f.label} ({f.count})
          </FilterPill>
        ))}
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center gap-2 py-16 text-slate-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          Caricamento calendario…
        </div>
      ) : filtered.length === 0 ? (
        <PortalEmptyState icon={SITE_ICONS.events}>
          {filter === "pending"
            ? "Hai già risposto a tutti gli appuntamenti in programma."
            : filter === "all"
              ? "Nessun evento in calendario."
              : "Nessun evento in questo filtro."}
        </PortalEmptyState>
      ) : (
        <div className="space-y-8">
          {groups.map((group) => (
            <section key={group.key}>
              <SubsectionTitle as="h2" className="text-lg font-bold capitalize mb-3">
                <span className="gold-divider mb-2 block" />
                {group.label}
              </SubsectionTitle>
              <div className="space-y-3">
                {group.events.map((ev) => (
                  <PortalEventCard
                    key={ev.id}
                    event={ev}
                    saving={saving === ev.id}
                    onSetStato={setStato}
                    onOpen={setModalEvent}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {modalEvent && (
        <EventDetailModal event={modalEvent} onClose={() => setModalEvent(null)} showAttachments />
      )}
    </div>
  );
}
