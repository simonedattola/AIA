/* Blocchi dinamici: configurazione CMS + dati live da API */
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams, Navigate, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  SectionTitle, SubsectionTitle, CardTitle, Eyebrow, Card, Button, CtaTitle, FilterPill,
} from "@/design-system";
import MemberGridCard from "../components/cards/MemberGridCard";
import NewsArticleCard from "../components/cards/NewsArticleCard";
import OrganigramPersonCard from "../components/cards/OrganigramPersonCard";
import {
  fetchDesignations, fetchMembers, fetchArticles, fetchCategories, fetchEvents, submitContact,
} from "../lib/api";
import { portalLogin } from "../lib/portal-api";
import { PORTAL_ROUTES } from "../lib/appRoutes";
import { useSite } from "../lib/site-context";
import { normalizeMember, memberRoleLabel } from "../lib/memberRoles";
import { formatDateIt, formatEventDateTimeIt, contactPreferenceLabel } from "../lib/format";
import DesignationsDataTable from "../components/designations/DesignationsDataTable";
import EventsMonthCalendar from "../components/events/EventsMonthCalendar";
import EventDetailModal from "../components/events/EventDetailModal";
import MediaImage from "../components/MediaImage";
import MemberProfileContent from "../components/members/MemberProfileContent";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../lib/brand";
import { isUpcomingEvent, eventDateKey } from "../lib/eventsDisplay";
import { resolveSectionMap } from "../lib/sectionMap";
import SectionMapPanel from "../components/maps/SectionMapPanel";
import { scrollPageToTop } from "../lib/scroll";
import {
  Filter, X, Search, ChevronLeft, ChevronRight, MapPin, Phone, Mail,
  Facebook, Instagram, CheckCircle2, Crown, Lock, Hash,
} from "lucide-react";

function SectionIntro({ eyebrow, title, intro }) {
  if (!eyebrow && !title && !intro) return null;
  return (
    <div className="mb-8">
      {eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{eyebrow}</Eyebrow>}
      {title && <SectionTitle className="mb-3">{title}</SectionTitle>}
      {intro && <p className="text-lg text-slate-600 leading-relaxed">{intro}</p>}
      {(title || eyebrow) && <span className="gold-divider mt-6 block" />}
    </div>
  );
}

const ROLE_FILTERS_DES = [
  { value: "", label: "Tutti i ruoli" },
  { value: "Arbitro", label: "Arbitro" },
  { value: "Assistente", label: "Assistenti" },
];

export function DesignationsTableBlock({ config: c }) {
  const [items, setItems] = useState([]);
  const [filterRole, setFilterRole] = useState(c.defaultRole || "");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params = { limit: c.limit || 300 };
    if (filterRole) params.role = filterRole;
    fetchDesignations(params)
      .then((d) => { setItems(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setError("Impossibile caricare le designazioni."); setItems([]); setLoading(false); });
  }, [filterRole, c.limit]);

  const filtered = useMemo(() => {
    const s = search.trim().toLowerCase();
    if (!s) return items;
    return items.filter((d) =>
      [d.matchLabel, d.memberName, d.role, d.championship, d.category, d.girone, d.matchDay, d.matchHome, d.matchAway].join(" ").toLowerCase().includes(s)
    );
  }, [items, search]);

  return (
    <section className="site-section bg-background" data-testid="designations-table-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionIntro eyebrow={c.eyebrow} title={c.title} intro={c.intro} />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-200">
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="h-4 w-4 text-slate-400 mr-1" />
            {ROLE_FILTERS_DES.map((r) => (
              <FilterPill key={r.value || "all"} active={filterRole === r.value} onClick={() => setFilterRole(r.value)}>
                {r.label}
              </FilterPill>
            ))}
          </div>
          <div className="relative w-full md:w-72">
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={c.searchPlaceholder || "Cerca gara o nominativo…"} className="w-full pl-4 pr-9 py-2 border border-slate-300 rounded-md text-sm focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none" />
            {search && <button type="button" onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400"><X className="h-4 w-4" /></button>}
          </div>
        </div>
        {loading ? <p className="text-slate-500">Caricamento…</p> : error ? <p className="text-red-600">{error}</p> : filtered.length === 0 ? <p className="text-slate-500">Nessuna designazione corrispondente.</p> : (
          <DesignationsDataTable designations={filtered} showNominativo tableTestId="designazioni-table" />
        )}
      </div>
    </section>
  );
}

/** Filtri pagina Arbitri (codici AIA + assistente). */
const ARBITRI_FILTERS = [
  { key: "", label: "Tutti" },
  { key: "AE", label: "Arbitro Effettivo" },
  { key: "ASSISTENTE", label: "Assistente Arbitrale" },
  { key: "AB", label: "Arbitro Benemerito" },
  { key: "AFR", label: "Arbitro Fuori Ruolo" },
];

function matchesArbitriFilter(m, filterKey) {
  if (!filterKey) return true;
  const code = String(m.role || "").trim().toUpperCase();
  const cat = String(m.category || "").toLowerCase();
  if (filterKey === "AB") {
    return code === "AB" || cat.includes("benemerito");
  }
  if (filterKey === "ASSISTENTE") {
    return (
      code === "AA" ||
      m.memberRole === "assistente" ||
      cat.includes("assistente arbitrale")
    );
  }
  if (filterKey === "AFR") {
    return code === "AFR" || cat.includes("fuori ruolo");
  }
  if (filterKey === "AE") {
    if (code === "AA" || m.memberRole === "assistente") return false;
    if (code === "AB" || cat.includes("benemerito")) return false;
    if (code === "AFR" || cat.includes("fuori ruolo")) return false;
    // Codice AIA AE; senza codice: arbitri non assistenti/benemeriti/fuori ruolo
    return !code || code === "AE";
  }
  return true;
}

export function MembersGridBlock({ config: c }) {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState(c.defaultRole || "");
  const [qualFilter, setQualFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const isObserversPage = c.defaultRole === "osservatore";
  const showArbitriFilters = !isObserversPage && !c.defaultRole;

  useEffect(() => {
    setLoading(true);
    const params = { limit: c.limit || 500 };
    if (c.defaultRole) params.memberRole = c.defaultRole;
    else if (role && !showArbitriFilters) params.memberRole = role;
    fetchMembers(params).then((d) => setItems(d.map(normalizeMember))).finally(() => setLoading(false));
  }, [role, c.limit, c.defaultRole, showArbitriFilters]);

  const filtered = useMemo(() => {
    let list = items;
    if (showArbitriFilters) {
      list = list.filter((m) => matchesArbitriFilter(m, qualFilter));
    }
    const s = search.trim().toLowerCase();
    if (!s) return list;
    return list.filter((m) => `${m.firstName} ${m.lastName} ${m.category} ${m.role} ${memberRoleLabel(m)}`.toLowerCase().includes(s));
  }, [items, search, qualFilter, showArbitriFilters]);

  return (
    <section className="site-section bg-background" data-testid="members-grid-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionIntro eyebrow={c.eyebrow} title={c.title} intro={c.intro} />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-200">
          <div className="flex items-center gap-2 flex-wrap">
            {showArbitriFilters
              ? ARBITRI_FILTERS.map((k) => (
                  <FilterPill key={k.key || "all"} active={qualFilter === k.key} onClick={() => setQualFilter(k.key)} data-testid={`arbitri-filter-${k.key || "all"}`}>
                    {k.label}
                  </FilterPill>
                ))
              : null}
          </div>
          <div className="relative w-full md:w-72">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={c.searchPlaceholder || "Cerca per nome…"} className="w-full pl-10 pr-9 py-2 border border-slate-300 rounded-md text-sm focus:border-navy-600 focus:outline-none" />
          </div>
        </div>
        {loading ? <p className="text-slate-500">Caricamento…</p> : (
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-ds-grid">
            {filtered.map((m) => (
              <MemberGridCard key={m.id} member={m} />
            ))}
          </div>
        )}
        {!loading && filtered.length === 0 && <p className="text-slate-500">Nessun associato trovato.</p>}
      </div>
    </section>
  );
}

export function NewsGridBlock({ config: c }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [cats, setCats] = useState([]);
  const [params, setParams] = useSearchParams();
  const cat = params.get("c") || "";
  const page = Math.max(1, parseInt(params.get("page") || "1", 10) || 1);
  const [loading, setLoading] = useState(true);
  const pageSize = c.pageSize || 24;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  useEffect(() => { fetchCategories().then(setCats).catch(() => setCats([])); }, []);

  useEffect(() => {
    setLoading(true);
    fetchArticles({ category: cat || undefined, limit: pageSize, skip: (page - 1) * pageSize })
      .then((d) => { setItems(d.items || d); setTotal(d.total ?? (d.items || d).length); setLoading(false); })
      .catch(() => { setItems([]); setLoading(false); });
  }, [cat, page, pageSize]);

  // La query `page` non cambia il pathname: ScrollToTop non scatta — riportiamo in cima a mano.
  useEffect(() => {
    scrollPageToTop();
  }, [page, cat]);

  const setCategory = (v) => {
    if (v) setParams({ c: v, page: "1" });
    else setParams(page > 1 ? { page: String(page) } : {});
  };

  const goPage = (next) => {
    setParams({ ...(cat ? { c: cat } : {}), page: String(next) });
  };

  return (
    <section className="site-section" data-testid="news-grid-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionIntro eyebrow={c.eyebrow} title={c.title} intro={c.intro} />
        {c.showFilters !== false && cats.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap mb-10">
            <Filter className="h-4 w-4 text-slate-400 mr-1" />
            <FilterPill active={!cat} onClick={() => setCategory("")}>Tutte</FilterPill>
            {cats.map((x) => (
              <FilterPill key={x} active={cat === x} onClick={() => setCategory(x)}>{x}</FilterPill>
            ))}
          </div>
        )}
        {loading && <p className="text-slate-500">Caricamento…</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {items.map((a) => (
            <NewsArticleCard key={a.slug} article={a} />
          ))}
        </div>
        {!loading && items.length === 0 && <p className="text-slate-500 mt-8">Nessun articolo disponibile.</p>}
        {!loading && totalPages > 1 && (
          <nav className="flex flex-wrap items-center justify-center gap-3 mt-12 pt-8 border-t border-slate-200" aria-label="Paginazione articoli">
            <Button type="button" disabled={page <= 1} onClick={() => goPage(page - 1)} variant="outline" size="sm">
              <ChevronLeft className="h-4 w-4" aria-hidden /> Precedente
            </Button>
            <span className="text-sm text-slate-600">Pagina {page} di {totalPages}</span>
            <Button type="button" disabled={page >= totalPages} onClick={() => goPage(page + 1)} variant="outline" size="sm">
              Successiva <ChevronRight className="h-4 w-4" aria-hidden />
            </Button>
          </nav>
        )}
      </div>
    </section>
  );
}

const EVENT_MONTHS_SHORT = ["GEN", "FEB", "MAR", "APR", "MAG", "GIU", "LUG", "AGO", "SET", "OTT", "NOV", "DIC"];

/** Card evento allineata alla home (`events_list`). */
function PublicEventCard({ e, onClick }) {
  const d = new Date(e.date);
  return (
    <Card
      as="button"
      type="button"
      interactive
      padding="default"
      className="w-full text-left flex flex-col sm:flex-row gap-4 sm:gap-5 items-start p-4 sm:p-5"
      onClick={onClick}
    >
      <div className="flex flex-col items-center justify-center bg-navy-600 text-white rounded-md w-16 h-16 flex-shrink-0">
        <div className="text-2xl font-bold leading-none">{d.getDate().toString().padStart(2, "0")}</div>
        <Eyebrow as="div" className="text-[10px] tracking-wider mt-1 text-gold-400">
          {EVENT_MONTHS_SHORT[d.getMonth()]}
        </Eyebrow>
      </div>
      <div className="flex-1 min-w-0">
        {e.tipo && (
          <Eyebrow as="div" className="inline-block tracking-wider text-gold-400 mb-1.5">
            {e.tipo}
          </Eyebrow>
        )}
        <CardTitle as="h3" className="text-lg">{e.titolo}</CardTitle>
        {e.descrizione && <p className="text-slate-600 text-sm mt-1.5 line-clamp-2">{e.descrizione}</p>}
        {e.luogo && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-2">
            <MapPin className="h-3.5 w-3.5" /> {e.luogo}
          </div>
        )}
        {!e.tipo && (
          <Eyebrow as="div" className="text-gold-600 mt-2">{formatEventDateTimeIt(e.date, e.orario, e.orarioFine)}</Eyebrow>
        )}
      </div>
    </Card>
  );
}

export function EventsCalendarBlock({ config: c }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMonth, setViewMonth] = useState(() => { const n = new Date(); return new Date(n.getFullYear(), n.getMonth(), 1); });
  const [selectedId, setSelectedId] = useState(null);
  const [modalEvent, setModalEvent] = useState(null);
  const listLimit = c.listLimit || 50;
  const showCalendar = c.showCalendar === true;

  useEffect(() => {
    fetchEvents({ limit: 500 }).then((data) => { setItems(data); setLoading(false); });
  }, []);

  const upcoming = useMemo(() => items.filter(isUpcomingEvent).sort((a, b) => eventDateKey(a.date).localeCompare(eventDateKey(b.date))), [items]);
  const listEvents = useMemo(() => upcoming.slice(0, listLimit), [upcoming, listLimit]);
  const listIds = useMemo(() => new Set(listEvents.map((e) => e.id)), [listEvents]);

  const shiftViewMonth = (delta) => {
    setViewMonth((prev) => {
      const base = prev instanceof Date ? prev : new Date();
      return new Date(base.getFullYear(), base.getMonth() + delta, 1);
    });
  };

  const handleSelect = (event) => {
    setSelectedId(event.id);
    setModalEvent(event);
    if (showCalendar) {
      const [y, m] = eventDateKey(event.date).split("-");
      setViewMonth(new Date(Number(y), Number(m) - 1, 1));
    }
  };

  return (
    <section className="site-section bg-background bg-pattern-stadio" data-testid="events-calendar-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionIntro
          eyebrow={c.eyebrow || (showCalendar ? "" : "Calendario sezionale")}
          title={c.title || (showCalendar ? "" : "Prossimi eventi")}
          intro={c.intro}
        />
        <div className={cn("grid grid-cols-1 gap-8 lg:gap-10", showCalendar && "lg:grid-cols-12")}>
          <div className={showCalendar ? "lg:col-span-6" : "max-w-3xl"}>
            {showCalendar && (
              <SubsectionTitle as="h3" className="mb-6">{c.listTitle || "Prossimi appuntamenti"}</SubsectionTitle>
            )}
            {loading ? (
              <p className="text-slate-500">Caricamento…</p>
            ) : listEvents.length === 0 ? (
              <p className="text-slate-500">Nessun evento in programma.</p>
            ) : (
              <ul className="space-y-3">
                {listEvents.map((e) => (
                  <li key={e.id}>
                    <PublicEventCard e={e} onClick={() => handleSelect(e)} />
                  </li>
                ))}
              </ul>
            )}
          </div>
          {showCalendar && (
            <div className="lg:col-span-6">
              <EventsMonthCalendar
                events={items}
                month={viewMonth}
                onMonthChange={shiftViewMonth}
                selectedEventId={selectedId}
                onSelectEvent={(event) => {
                  setSelectedId(event.id);
                  const [y, m] = eventDateKey(event.date).split("-");
                  setViewMonth(new Date(Number(y), Number(m) - 1, 1));
                  setModalEvent(listIds.has(event.id) ? event : event);
                }}
              />
            </div>
          )}
        </div>
        <EventDetailModal event={modalEvent} onClose={() => setModalEvent(null)} />
      </div>
    </section>
  );
}

function ContactInfoRow({ icon, title, value, href }) {
  if (!value) return null;
  const inner = <><div className="text-xs uppercase tracking-wider text-slate-500 mb-1">{title}</div><div className="font-medium text-navy-700">{value}</div></>;
  return (
    <div className="flex gap-4">
      <div className="w-10 h-10 rounded-full bg-navy-50 text-navy-600 flex items-center justify-center flex-shrink-0">{icon}</div>
      <div>{href ? <a href={href} className="hover:text-navy-600">{inner}</a> : inner}</div>
    </div>
  );
}

export function ContactSectionBlock({ config: c }) {
  const { settings } = useSite();
  const s = settings || {};
  const sectionMap = resolveSectionMap(s);
  const [form, setForm] = useState({ name: "", email: "", subject: "", body: "" });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await submitContact(form);
      setSubmitted(true);
    } catch (err) {
      setError(err?.response?.data?.detail || "Errore invio. Riprova.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="site-section bg-background" data-testid="contact-section-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-5 space-y-6">
          <SectionIntro eyebrow={c.eyebrow} title={c.infoTitle || c.title} intro={c.intro} />
          <ContactInfoRow icon={<MapPin className="h-5 w-5" />} title="Indirizzo" value={s.address} />
          <ContactInfoRow icon={<Phone className="h-5 w-5" />} title="Telefono" value={s.phone} href={s.phone ? `tel:${s.phone}` : null} />
          <ContactInfoRow icon={<Mail className="h-5 w-5" />} title="Email" value={s.email} href={s.email ? `mailto:${s.email}` : null} />
          <div className="flex items-center gap-3 pt-4">
            {s.facebookUrl && <a href={s.facebookUrl} target="_blank" rel="noopener noreferrer" className="p-2.5 rounded-full bg-navy-50 text-navy-600 hover:bg-navy-100"><Facebook className="h-5 w-5" /></a>}
            {s.instagramUrl && <a href={s.instagramUrl} target="_blank" rel="noopener noreferrer" className="p-2.5 rounded-full bg-navy-50 text-navy-600 hover:bg-navy-100"><Instagram className="h-5 w-5" /></a>}
          </div>
          {sectionMap && (
            <SectionMapPanel
              embedUrl={sectionMap.embedUrl}
              linkUrl={sectionMap.linkUrl}
              title={s.address ? `Mappa — ${s.address}` : "Mappa sezione"}
              caption={sectionMap.caption}
              className="mt-2"
              testId="contact-section-map"
            />
          )}
        </div>
        <div className="lg:col-span-7">
          {submitted ? (
            <Card variant="accent" shadow="md" className="text-navy-700 p-8 sm:p-10 shadow-2xl text-center" data-testid="contact-success">
              <CheckCircle2 className="h-16 w-16 text-gold-400 mx-auto mb-5" />
              <SubsectionTitle as="h3" className="mb-3 text-center">
                Grazie {(form.name.trim().split(/\s+/)[0]) || form.name}!
              </SubsectionTitle>
              <p className="text-slate-600 text-center">
                Un referente della sezione ti contatterà a breve tramite{" "}
                {contactPreferenceLabel("email", { lowercase: true })}.
              </p>
            </Card>
          ) : (
            <Card as="form" onSubmit={submit} padding="none" className="p-8 space-y-5">
              <SubsectionTitle as="h2">{c.formTitle || "Scrivici"}</SubsectionTitle>
              {error && <p className="text-red-600 text-sm">{error}</p>}
              {["name", "email", "subject"].map((k) => (
                <label key={k} className="block">
                  <span className="block text-sm font-medium text-slate-700 mb-1.5">{k === "name" ? "Nome" : k === "email" ? "Email" : "Oggetto"}</span>
                  <input required type={k === "email" ? "email" : "text"} value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:border-navy-600 focus:outline-none" />
                </label>
              ))}
              <label className="block">
                <span className="block text-sm font-medium text-slate-700 mb-1.5">Messaggio</span>
                <textarea required rows={5} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:border-navy-600 focus:outline-none" />
              </label>
              <Button type="submit" disabled={submitting} variant="primary">{submitting ? "Invio…" : "Invia messaggio"}</Button>
            </Card>
          )}
        </div>
      </div>
    </section>
  );
}

export function OrganigrammaBlock({ config: c, stats }) {
  const [people, setPeople] = useState([]);

  useEffect(() => {
    fetchMembers({ scope: c.scope || "chi_siamo", limit: 100 })
      .then((all) => setPeople(all.map(normalizeMember)))
      .catch(() => setPeople([]));
  }, [c.scope]);

  const orgKind = (m) => String(m.organigrammaKind || "").toLowerCase();
  const president =
    people.find((m) => m.isPresident) ||
    people.find((m) => {
      const k = orgKind(m);
      if (k === "ors" || k === "collaboratore") return false;
      const t = (m.boardTitle || "").toLowerCase();
      if (t.includes("revisione") || /vice\s*-?\s*presidente|vicepresidente/.test(t)) return false;
      return /\bpresidente\b/.test(t) && (k === "cds" || !k);
    });
  const isConsiglioTitle = (title) => {
    const t = (title || "").toLowerCase();
    if (!t || /revisione/i.test(t)) return false;
    return (
      /\bvice\b/.test(t) ||
      t.includes("segretario") ||
      t.includes("cassiere") ||
      t.includes("consigliere") ||
      (t.includes("consiglio") && !t.includes("collaboratore"))
    );
  };
  const isCollaboratoreTitle = (title) => {
    const t = (title || "").toLowerCase();
    if (!t || /revisione/i.test(t) || isConsiglioTitle(t)) return false;
    return (
      t.includes("collaboratore") ||
      t.includes("area ") ||
      t.startsWith("area") ||
      t.includes("referente") ||
      t.includes("responsabile") ||
      t.includes("gestione")
    );
  };
  const revisione = people.filter(
    (m) => orgKind(m) === "ors" || (!orgKind(m) && /revisione/i.test(m.boardTitle || ""))
  );
  const consiglio = people.filter(
    (m) =>
      m.id !== president?.id &&
      (orgKind(m) === "cds" || (!orgKind(m) && isConsiglioTitle(m.boardTitle)))
  );
  const collaboratori = people.filter(
    (m) =>
      m.id !== president?.id &&
      !revisione.some((x) => x.id === m.id) &&
      !consiglio.some((x) => x.id === m.id) &&
      (orgKind(m) === "collaboratore" ||
        (!orgKind(m) && (isCollaboratoreTitle(m.boardTitle) || !isConsiglioTitle(m.boardTitle))))
  );

  if (!president && consiglio.length === 0 && collaboratori.length === 0 && revisione.length === 0) return null;

  return (
    <section className="site-section bg-background bg-pattern-stadio border-t border-slate-200" data-testid="organigramma-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionIntro eyebrow={c.eyebrow || "Governance"} title={c.title || "Organigramma sezionale"} intro={c.intro || "Le persone che fanno funzionare la Sezione:"} />
        {president && (
          <div className="mb-12 max-w-6xl mx-auto">
            <Card as={Link} to={president.slug ? `/arbitri/${president.slug}` : "#"} interactive padding="none" shadow="md" className="shadow-xl overflow-hidden grid grid-cols-1 md:grid-cols-12 block">
              <div className="md:col-span-5 aspect-[4/5] md:aspect-auto overflow-hidden bg-slate-100">
                {president.photoUrl ? <MediaImage src={president.photoUrl} alt="" className="w-full h-full object-cover" /> : (
                  <div className="w-full h-full bg-navy-600 flex items-center justify-center text-white text-4xl font-bold">{president.firstName[0]}{president.lastName[0]}</div>
                )}
              </div>
              <div className="md:col-span-7 p-8 lg:p-12 flex flex-col justify-center border-t-4 md:border-t-0 md:border-l-4 border-gold-400">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gold-400/15 text-gold-700 text-xs uppercase tracking-wider font-semibold mb-4 w-fit">
                  <Crown className="h-3.5 w-3.5" /> Presidente di Sezione
                </div>
                <CtaTitle as="h3" className="text-4xl lg:text-5xl leading-tight mb-3">
                  {president.firstName} <span className="text-gold-400">{president.lastName}</span>
                </CtaTitle>
                <p className="text-slate-600 text-lg leading-relaxed whitespace-pre-line">
                  {(president.chiSiamoText || "").trim() || c.presidentFallback || "Guida la Sezione promuovendo formazione tecnica, spirito associativo e crescita delle nuove generazioni arbitrali."}
                </p>
                {president.boardTitle && (
                  <p className="text-sm text-slate-500 mt-3">{president.boardTitle}</p>
                )}
              </div>
            </Card>
          </div>
        )}
        {consiglio.length > 0 && (
          <div className="mb-12">
            <SubsectionTitle as="h3" className="mb-8 text-center">Consiglio Direttivo Sezionale</SubsectionTitle>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-ds-grid">
              {consiglio.map((m) => <OrganigramPersonCard key={m.id} member={m} subtitle={m.boardTitle || "Consiglio Direttivo"} />)}
            </div>
          </div>
        )}
        {collaboratori.length > 0 && (
          <div className="mb-12">
            <SubsectionTitle as="h3" className="mb-8 text-center">Collaboratori</SubsectionTitle>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-ds-grid">
              {collaboratori.map((m) => <OrganigramPersonCard key={m.id} member={m} subtitle={m.boardTitle || "Collaboratore"} />)}
            </div>
          </div>
        )}
        {revisione.length > 0 && (
          <div>
            <SubsectionTitle as="h3" className="mb-8 text-center">Organo di Revisione Sezionale</SubsectionTitle>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-ds-grid">
              {revisione.map((m) => <OrganigramPersonCard key={m.id} member={m} subtitle={m.boardTitle || "Organo di Revisione"} />)}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export function MemberProfileBlock({ config: c, memberSlug }) {
  return <MemberProfileContent memberSlug={memberSlug} />;
}

export function PortalLoginBlock({ config: c }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ codice: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (localStorage.getItem("aia_member_token")) {
    return <Navigate to={PORTAL_ROUTES.root} replace />;
  }

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await portalLogin(form.codice.trim(), form.password);
      localStorage.setItem("aia_member_token", res.token);
      localStorage.setItem("aia_member", JSON.stringify(res.member));
      navigate(PORTAL_ROUTES.root);
    } catch (err) {
      setError(err?.response?.data?.detail || "Credenziali non valide");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="portal-login-block">
      {c.showLogo !== false && (
        <div className="flex items-center gap-3 mb-8">
          <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.lg} />
          <div>
            <CardTitle as="div" className="text-xl">{c.title || "Area Associati"}</CardTitle>
            <Eyebrow as="div" className="tracking-[0.18em] text-slate-500 font-medium">{c.subtitle || "AIA Legnano"}</Eyebrow>
          </div>
        </div>
      )}
      {c.introHtml && <div className="prose-aia text-sm text-slate-600 mb-6" dangerouslySetInnerHTML={{ __html: c.introHtml }} />}
      <form onSubmit={submit} className="space-y-4">
        {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-sm">{error}</div>}
        <label className="block">
          <span className="block text-sm font-medium text-slate-700 mb-1">Codice meccanografico</span>
          <div className="relative">
            <Hash className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input required value={form.codice} onChange={(e) => setForm({ ...form, codice: e.target.value })} className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:ring-2 focus:ring-navy-500" placeholder="es. 12345678" />
          </div>
        </label>
        <label className="block">
          <span className="block text-sm font-medium text-slate-700 mb-1">Password</span>
          <div className="relative">
            <Lock className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:ring-2 focus:ring-navy-500" />
          </div>
        </label>
        <Button type="submit" disabled={loading} variant="primary" className="w-full">{loading ? "Accesso…" : "Accedi"}</Button>
      </form>
      <p className="text-center text-sm text-slate-500 mt-6">
        <Link to="/" className="text-navy-600 hover:underline">← Torna al sito</Link>
      </p>
    </div>
  );
}
