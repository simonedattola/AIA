import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { portalDashboard, portalSetPresenza } from "../../lib/portal-api";
import PortalEventCard from "../../components/portal/PortalEventCard";
import PortalDesignationCard from "../../components/portal/PortalDesignationCard";
import EventDetailModal from "../../components/events/EventDetailModal";
import { formatDateIt } from "../../lib/format";
import { PORTAL_ICONS } from "../../components/portal/portalNavItems";
import { PORTAL_ROUTES as R } from "../../lib/appRoutes";
import { ChevronRight, Loader2 } from "lucide-react";
import { PortalEmptyState, PortalPageHeader } from "../../components/portal/portal-ui";

const sectionHeading = "text-sm font-semibold uppercase tracking-wider text-slate-500";

const ComunicazioniIcon = PORTAL_ICONS.comunicazioni;
const MessaggiIcon = PORTAL_ICONS.messaggi;
const StoricoIcon = PORTAL_ICONS.storico;
const CalendarioIcon = PORTAL_ICONS.calendario;

export default function PortalDashboardPage() {
  const [data, setData] = useState(null);
  const [saving, setSaving] = useState(null);
  const [modalEvent, setModalEvent] = useState(null);

  const load = () => portalDashboard().then(setData);

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

  if (!data) {
    return (
      <div className="flex items-center justify-center gap-2 py-16 text-slate-500" data-testid="portal-dashboard-loading">
        <Loader2 className="h-5 w-5 animate-spin" />
        Caricamento dashboard…
      </div>
    );
  }

  const nextEvent = data.upcomingEvents?.[0];
  const nextDesignation = data.nextDesignation;
  const unreadComms = data.comunicazioniNonLette ?? 0;
  const unreadMessages = data.messaggiNonLetti ?? 0;

  return (
    <div data-testid="portal-dashboard-page">
      <PortalPageHeader
        title="Dashboard"
        description="Panoramica personale e prossimi appuntamenti"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        <Link
          to={R.comunicazioniInterne}
          className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3 hover:border-navy-300 hover:shadow-sm transition-all group"
        >
          <div className="h-10 w-10 rounded-lg bg-gold-50 text-gold-600 flex items-center justify-center shrink-0">
            <ComunicazioniIcon className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xl font-bold text-navy-700 tabular-nums">{unreadComms}</div>
            <div className="text-sm text-slate-600">Comunicazioni non lette</div>
          </div>
          <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-navy-600 shrink-0" />
        </Link>

        <Link
          to={R.messaggi}
          className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3 hover:border-navy-300 hover:shadow-sm transition-all group"
        >
          <div className="h-10 w-10 rounded-lg bg-navy-50 text-navy-700 flex items-center justify-center shrink-0">
            <MessaggiIcon className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xl font-bold text-navy-700 tabular-nums">{unreadMessages}</div>
            <div className="text-sm text-slate-600">Messaggi non letti</div>
          </div>
          <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-navy-600 shrink-0" />
        </Link>
      </div>

      <section className="mb-10">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className={sectionHeading}>Prossima partita</h2>
          <Link
            to={R.storicoArbitrale}
            className="text-sm font-medium text-navy-600 hover:text-navy-800 inline-flex items-center gap-1"
          >
            Vedi storico completo
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        {!nextDesignation ? (
          <PortalEmptyState icon={StoricoIcon}>
            Nessuna partita in programma.
          </PortalEmptyState>
        ) : (
          <PortalDesignationCard designation={nextDesignation} />
        )}
      </section>

      <section className="pt-10 mb-10 border-t border-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className={sectionHeading}>Prossimo evento</h2>
          <Link
            to={R.calendario}
            className="text-sm font-medium text-navy-600 hover:text-navy-800 inline-flex items-center gap-1"
          >
            Vedi calendario completo
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        {!nextEvent ? (
          <PortalEmptyState icon={CalendarioIcon}>
            Nessun evento in programma.
          </PortalEmptyState>
        ) : (
          <PortalEventCard
            event={nextEvent}
            saving={saving === nextEvent.id}
            onSetStato={setStato}
            onOpen={setModalEvent}
          />
        )}
      </section>

      <section className="pt-10 border-t border-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className={sectionHeading}>Ultime comunicazioni interne</h2>
          <Link
            to={R.comunicazioniInterne}
            className="text-sm font-medium text-navy-600 hover:text-navy-800 inline-flex items-center gap-1"
          >
            Vedi tutte le comunicazioni
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        {data.latestComunicazioni?.length === 0 ? (
          <PortalEmptyState icon={ComunicazioniIcon}>
            Nessuna comunicazione recente.
          </PortalEmptyState>
        ) : (
          <ul className="space-y-3">
            {data.latestComunicazioni.map((a) => (
              <li key={a.id}>
                <Link
                  to={R.comunicazione(a.id)}
                  className={`flex items-center gap-3 px-5 py-4 rounded-xl border bg-white transition-colors hover:border-navy-300 group ${
                    a.letta ? "border-slate-200" : "border-gold-300 bg-gold-50/30"
                  }`}
                >
                  {!a.letta ? (
                    <span className="h-2 w-2 rounded-full bg-gold-500 shrink-0" aria-label="Non letta" />
                  ) : (
                    <span className="h-2 w-2 rounded-full bg-transparent shrink-0" aria-hidden />
                  )}
                  <span className="flex-1 min-w-0">
                    <span className="block font-medium text-navy-700 group-hover:text-navy-900 truncate">
                      {a.title}
                    </span>
                    {a.createdAt && (
                      <span className="block text-xs text-slate-500 mt-0.5">
                        {formatDateIt(a.createdAt, { short: true })}
                      </span>
                    )}
                  </span>
                  <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-navy-600 shrink-0" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {modalEvent && (
        <EventDetailModal event={modalEvent} onClose={() => setModalEvent(null)} showAttachments />
      )}
    </div>
  );
}
