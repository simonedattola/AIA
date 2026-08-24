// Block registry: central source of truth for available block types.
// Each entry has: type, label, icon (lucide), defaultConfig, schema (for editor).
import {
  Layout, Type, ImageIcon, Megaphone, ListChecks, Clock, BarChart3,
  Code2, MoveVertical,
  Phone, Building2, UserCircle, LogIn,
} from "lucide-react";
import { SITE_ICONS } from "../lib/siteIcons";

export const BLOCK_TYPES = [
  {
    type: "hero",
    label: "Intestazione grande",
    desc: "Titolo, testo e immagine in cima alla pagina.",
    icon: Layout,
    defaultConfig: {
      eyebrow: "",
      title: "Titolo Hero",
      subtitle: "",
      backgroundImage: "",
      overlay: "navy",
      height: "tall",
      badgeLogoUrl: "",
      badgeText: "",
      primaryCta: { label: "", href: "" },
      secondaryCta: { label: "", href: "" },
      showStats: false,
    },
  },
  {
    type: "rich_text",
    label: "Testo",
    desc: "Paragrafi, elenchi e formattazione.",
    icon: Type,
    defaultConfig: {
      eyebrow: "",
      title: "",
      html: "<p>Scrivi qui il contenuto…</p>",
      maxWidth: "narrow",
      background: "white",
    },
  },
  {
    type: "text_image",
    label: "Testo con immagine",
    desc: "Testo affiancato a un'immagine.",
    icon: ImageIcon,
    defaultConfig: {
      eyebrow: "",
      title: "Titolo sezione",
      html: "<p>Descrizione…</p>",
      imageUrl: "",
      imageAspect: "3:4",
      imagePosition: "right",
      badgeLabel: "",
      badgeText: "",
      requirementsTitle: "",
      requirements: [],
      background: "white",
    },
  },
  {
    type: "cta",
    label: "Invito all'azione",
    desc: "Banner con titolo, testo e pulsante.",
    icon: Megaphone,
    defaultConfig: {
      eyebrow: "",
      title: "Call to Action",
      description: "",
      backgroundImage: "",
      primaryCta: { label: "Scopri", href: "/" },
      secondaryCta: { label: "", href: "" },
      style: "navy",
      formType: "",
      anchor: "",
    },
  },
  {
    type: "faq",
    label: "Domande frequenti",
    desc: "Elenco di domande e risposte.",
    icon: ListChecks,
    defaultConfig: {
      eyebrow: "",
      title: "Domande frequenti",
      background: "slate",
      items: [{ question: "Domanda", answer: "<p>Risposta</p>" }],
    },
  },
  {
    type: "timeline",
    label: "Passi",
    desc: "Elenco numerato di passaggi.",
    icon: Clock,
    defaultConfig: {
      eyebrow: "",
      title: "Il tuo percorso",
      items: [{ step: "01", title: "Passo 1", text: "Descrizione…" }],
    },
  },
  {
    type: "stats",
    label: "Numeri in evidenza",
    desc: "Cifre importanti con breve descrizione.",
    icon: BarChart3,
    defaultConfig: {
      eyebrow: "",
      title: "I numeri",
      background: "white",
      items: [{ icon: "Trophy", value: "10", label: "Anni", desc: "" }],
    },
  },
  {
    type: "gallery",
    label: "Galleria immagini",
    desc: "Griglia di foto con ingrandimento.",
    icon: SITE_ICONS.gallery,
    defaultConfig: {
      eyebrow: "",
      title: "Galleria",
      columns: 3,
      images: [],
    },
  },
  {
    type: "news_slider",
    label: "Ultime news",
    desc: "Si aggiorna automaticamente dagli articoli.",
    icon: SITE_ICONS.articles,
    defaultConfig: {
      eyebrow: "Aggiornamenti",
      title: "Ultime news",
      limit: 3,
      category: "",
      ctaLabel: "Tutte le news",
      ctaHref: "/news",
    },
  },
  {
    type: "events_list",
    label: "Prossimi eventi",
    desc: "Si aggiorna automaticamente dal calendario.",
    icon: SITE_ICONS.events,
    defaultConfig: {
      eyebrow: "Calendario",
      title: "Prossimi eventi",
      limit: 3,
      upcomingOnly: true,
      ctaLabel: "Tutti gli eventi",
      ctaHref: "/eventi",
      showInstagramWidget: true,
      showCalendar: false,
      showPresidentCard: false,
      instagramTitle: "AIA Legnano",
      instagramSubtitle: "Foto, aggiornamenti e vita della sezione su Instagram.",
      instagramPostUrl: "",
      instagramEmbed: {},
    },
  },
  {
    type: "testimonials",
    label: "Testimonianze",
    desc: "Citazioni gestite in Testimonianze.",
    icon: SITE_ICONS.testimonials,
    defaultConfig: {
      eyebrow: "",
      title: "Cosa dicono di noi",
      useGlobal: true,  // pull from /api/public/testimonials
      items: [],
    },
  },
  {
    type: "downloads",
    label: "Download",
    desc: "Lista documenti scaricabili.",
    icon: SITE_ICONS.documents,
    defaultConfig: {
      eyebrow: "",
      title: "Documenti",
      useGlobal: true,
      category: "",
      items: [],
    },
  },
  {
    type: "embed",
    label: "Embed HTML / iframe",
    desc: "YouTube, mappe, widget esterni.",
    icon: Code2,
    defaultConfig: {
      eyebrow: "",
      title: "",
      html: '<iframe width="100%" height="500" src="https://www.youtube.com/embed/..." frameborder="0" allowfullscreen></iframe>',
      aspectRatio: "16/9",
      maxWidth: "wide",
    },
  },
  {
    type: "spacer",
    label: "Spaziatore",
    desc: "Spazio bianco verticale.",
    icon: MoveVertical,
    defaultConfig: { height: "md" },
  },
  {
    type: "designations_table",
    label: "Designazioni",
    desc: "Si aggiorna automaticamente da AIA FIGC.",
    icon: SITE_ICONS.designations,
    defaultConfig: { eyebrow: "", title: "Designazioni", intro: "", limit: 300, searchPlaceholder: "Cerca gara o nominativo…", defaultRole: "" },
  },
  {
    type: "members_grid",
    label: "Elenco arbitri",
    desc: "Si aggiorna automaticamente dall'anagrafica.",
    icon: SITE_ICONS.members,
    defaultConfig: { eyebrow: "", title: "Arbitri", intro: "", limit: 500, searchPlaceholder: "Cerca per nome…", defaultRole: "" },
  },
  {
    type: "news_grid",
    label: "Tutte le news",
    desc: "Si aggiorna automaticamente dagli articoli.",
    icon: SITE_ICONS.articles,
    defaultConfig: { eyebrow: "", title: "News & Successi", intro: "", pageSize: 24, showFilters: true },
  },
  {
    type: "events_calendar",
    label: "Calendario eventi",
    desc: "Si aggiorna automaticamente dal calendario.",
    icon: SITE_ICONS.events,
    defaultConfig: { eyebrow: "", title: "Eventi", intro: "", listTitle: "Prossimi appuntamenti", listLimit: 50, showCalendar: false },
  },
  {
    type: "contact_section",
    label: "Contatti",
    desc: "Recapiti e modulo per scriverci.",
    icon: Phone,
    defaultConfig: { eyebrow: "", title: "Contatti", infoTitle: "Vieni a trovarci", intro: "", formTitle: "Scrivici" },
  },
  {
    type: "organigramma",
    label: "Organigramma",
    desc: "Si aggiorna automaticamente dall'anagrafica.",
    icon: Building2,
    defaultConfig: { eyebrow: "Governance", title: "Organigramma sezionale", intro: "Le persone che fanno funzionare la Sezione:", scope: "chi_siamo", presidentFallback: "" },
  },
  {
    type: "member_profile",
    label: "Profilo associato",
    desc: "Scheda dinamica dell'arbitro (usa slug dalla URL).",
    icon: UserCircle,
    defaultConfig: { eyebrow: "", title: "", intro: "" },
  },
  {
    type: "portal_login",
    label: "Login area associati",
    desc: "Form di accesso area riservata.",
    icon: LogIn,
    defaultConfig: {
      title: "Area associati",
      subtitle: "AIA Legnano",
      introHtml: "<p>Accedi con il <strong>codice meccanografico</strong> e la password fornita dalla sezione.</p>",
      showLogo: true,
    },
  },
];

export const BLOCK_BY_TYPE = Object.fromEntries(BLOCK_TYPES.map((b) => [b.type, b]));

/** Tipi offerti in «Aggiungi sezione» (niente blocchi tecnici o di sistema). */
export const BLOCK_TYPES_LIBRARY = BLOCK_TYPES.filter(
  (b) => !["spacer", "embed", "downloads", "member_profile", "portal_login"].includes(b.type)
);

export function newBlock(type) {
  const def = BLOCK_BY_TYPE[type];
  if (!def) return null;
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random()),
    type,
    enabled: true,
    config: JSON.parse(JSON.stringify(def.defaultConfig)),
  };
}
