import { SITE_ICONS as I } from "../../lib/siteIcons";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";

/** Voci menu admin — stile piatto come area associati. */
export const ADMIN_NAV = [
  { to: R.dashboard, icon: I.dashboard, label: "Dashboard", end: true },
  { to: R.anagrafica, icon: I.anagrafica, label: "Anagrafica" },
  { to: R.designazioni, icon: I.designations, label: "Designazioni" },
  { to: R.comunicazioniInterne, icon: I.comunicazioni, label: "Comunicazioni interne" },
  { to: R.eventi, icon: I.events, label: "Eventi" },
  { to: R.articoli, icon: I.articles, label: "Articoli" },
  { to: R.messaggiSito, icon: I.messagesSite, label: "Messaggi sito" },
  { to: R.candidature, icon: I.leads, label: "Candidature" },
  { to: R.galleria, icon: I.gallery, label: "Galleria" },
  { to: R.testimonianze, icon: I.testimonials, label: "Testimonianze" },
  { to: R.documenti, icon: I.documents, label: "Documenti" },
  { to: R.utility, icon: I.utility, label: "Utility" },
  { to: R.pagine, icon: I.pages, label: "Pagine" },
  { to: R.impostazioni, icon: I.settings, label: "Impostazioni" },
];
