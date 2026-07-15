import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminDashboard } from "../../lib/api";
import PortalEventCard from "../../components/portal/PortalEventCard";
import DesignationsDataTable from "../../components/designations/DesignationsDataTable";
import { formatDateIt } from "../../lib/format";
import { AdminEmptyState, AdminPageHeader } from "../../components/admin/admin-ui";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { SITE_ICONS } from "../../lib/siteIcons";
import { ChevronRight, Loader2, Plus } from "lucide-react";

const sectionHeading = "text-sm font-semibold uppercase tracking-wider text-slate-500";

function StatCard({ to, icon: Icon, value, label, accent = "gold" }) {
  const iconWrap = accent === "navy" ? "bg-navy-50 text-navy-700" : "bg-gold-50 text-gold-600";
  return (
    <Link
      to={to}
      className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3 hover:border-navy-300 hover:shadow-sm transition-all group"
    >
      <div className={`h-10 w-10 rounded-lg ${iconWrap} flex items-center justify-center shrink-0`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xl font-bold text-navy-700 tabular-nums">{value}</div>
        <div className="text-sm text-slate-600">{label}</div>
      </div>
      <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-navy-600 shrink-0" />
    </Link>
  );
}

function SectionLink({ to, children, accent }) {
  return (
    <Link
      to={to}
      className="text-sm font-medium text-navy-600 hover:text-navy-800 inline-flex items-center gap-1"
    >
      {accent === "action" && <Plus className="h-4 w-4" />}
      {children}
      {accent !== "action" && <ChevronRight className="h-4 w-4" />}
    </Link>
  );
}

function ActionLink({ to, icon: Icon, label, description }) {
  return (
    <Link
      to={to}
      className="bg-white rounded-xl border border-slate-200 p-4 flex items-start gap-3 hover:border-navy-300 hover:shadow-sm transition-all group"
    >
      <div className="h-10 w-10 rounded-lg bg-navy-50 text-navy-700 flex items-center justify-center shrink-0">
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-medium text-navy-800 group-hover:text-navy-900 inline-flex items-center gap-1">
          <Plus className="h-4 w-4 text-gold-600" />
          {label}
        </div>
        {description && <p className="text-sm text-slate-500 mt-0.5">{description}</p>}
      </div>
      <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-navy-600 shrink-0 mt-0.5" />
    </Link>
  );
}

function stripHtml(html) {
  if (!html) return "";
  const doc = new DOMParser().parseFromString(html, "text/html");
  return (doc.body.textContent || "").replace(/\s+/g, " ").trim();
}

export default function AdminDashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    adminDashboard()
      .then(setData)
      .catch(() => setError("Impossibile caricare la panoramica. Riprova tra poco."));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 text-amber-900 p-4 text-sm" data-testid="admin-dashboard">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center gap-2 py-16 text-slate-500" data-testid="admin-dashboard">
        <Loader2 className="h-5 w-5 animate-spin" />
        Caricamento…
      </div>
    );
  }

  const publicDesignations = data.publicDesignations || [];
  const latestComunicazione = data.latestComunicazione;
  const ComunicazioniIcon = SITE_ICONS.comunicazioni;

  return (
    <div data-testid="admin-dashboard">
      <AdminPageHeader
        title="Dashboard"
        description="Panoramica amministrazione"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-10">
        <StatCard
          to={R.messaggiSito}
          icon={SITE_ICONS.messagesSite}
          value={data.messagesNew ?? 0}
          label="Messaggi dal sito da leggere"
          accent="navy"
        />
        <StatCard
          to={R.candidature}
          icon={SITE_ICONS.leads}
          value={data.leadsNew ?? 0}
          label="Candidature da leggere"
        />
      </div>

      <section className="mb-10">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className={sectionHeading}>Designazioni sul sito pubblico</h2>
          <div className="flex flex-wrap items-center gap-4">
            <SectionLink to={R.designazioni}>Gestisci designazioni</SectionLink>
            <SectionLink to={`${R.designazioni}?new=1`} accent="action">
              Aggiungi una nuova designazione
            </SectionLink>
          </div>
        </div>
        {publicDesignations.length === 0 ? (
          <AdminEmptyState
            icon={SITE_ICONS.designations}
            title="Nessuna designazione visibile sul sito in questo momento."
          />
        ) : (
          <DesignationsDataTable
            designations={publicDesignations}
            showNominativo
            maxVisibleRows={8}
            tableTestId="admin-dashboard-designations"
            rowTestIdPrefix="dashboard-designation"
          />
        )}
      </section>

      <section className="pt-10 mb-10 border-t border-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className={sectionHeading}>Prossimo evento</h2>
          <div className="flex flex-wrap items-center gap-4">
            <SectionLink to={R.eventi}>Vedi tutti gli eventi</SectionLink>
            <SectionLink to={`${R.eventi}?new=1`} accent="action">
              Aggiungi un nuovo evento
            </SectionLink>
          </div>
        </div>
        {!data.nextEvent ? (
          <AdminEmptyState icon={SITE_ICONS.events} title="Nessun evento in programma nella stagione corrente." />
        ) : (
          <Link
            to={`${R.eventi}?edit=${data.nextEvent.id}`}
            className="block rounded-xl transition-colors hover:opacity-95"
            aria-label={`Modifica evento: ${data.nextEvent.titolo}`}
          >
            <PortalEventCard event={data.nextEvent} />
          </Link>
        )}
      </section>

      <section className="pt-10 mb-10 border-t border-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className={sectionHeading}>Ultima comunicazione interna</h2>
          <div className="flex flex-wrap items-center gap-4">
            <SectionLink to={R.comunicazioniInterne}>Vedi tutte le comunicazioni</SectionLink>
            <SectionLink to={`${R.comunicazioniInterne}?new=1`} accent="action">
              Aggiungi una nuova comunicazione
            </SectionLink>
          </div>
        </div>
        {!latestComunicazione ? (
          <AdminEmptyState icon={ComunicazioniIcon} title="Nessuna comunicazione interna inviata." />
        ) : (
          <Link
            to={R.comunicazioniInterne}
            className="block bg-white rounded-xl border border-slate-200 p-5 sm:p-6 hover:border-navy-300 hover:shadow-sm transition-all group"
          >
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-lg bg-gold-50 text-gold-600 flex items-center justify-center shrink-0">
                <ComunicazioniIcon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-display font-semibold text-navy-800 group-hover:text-navy-900">
                  {latestComunicazione.title}
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  {formatDateIt(
                    (latestComunicazione.publishedAt || latestComunicazione.createdAt || "").slice(0, 10)
                  )}
                </p>
                {latestComunicazione.bodyHtml && (
                  <p className="text-sm text-slate-600 mt-2 line-clamp-2">
                    {stripHtml(latestComunicazione.bodyHtml)}
                  </p>
                )}
              </div>
              <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-navy-600 shrink-0 mt-1" />
            </div>
          </Link>
        )}
      </section>

      <section className="pt-10 border-t border-slate-200">
        <h2 className={`${sectionHeading} mb-4`}>Inserisci contenuti</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <ActionLink
            to={`${R.anagrafica}?new=1`}
            icon={SITE_ICONS.anagrafica}
            label="Aggiungi un nuovo associato"
            description="Crea un profilo in anagrafica"
          />
          <ActionLink
            to={R.articoloNuovo}
            icon={SITE_ICONS.articles}
            label="Nuovo articolo"
            description="News e successi sul sito pubblico"
          />
          <ActionLink
            to={`${R.galleria}?new=1`}
            icon={SITE_ICONS.gallery}
            label="Nuova immagine in galleria"
            description="Carica e approva foto per il sito"
          />
          <ActionLink
            to={`${R.documenti}?new=1`}
            icon={SITE_ICONS.documents}
            label="Nuovo documento"
            description="File o link nell'area documenti"
          />
        </div>
      </section>
    </div>
  );
}
