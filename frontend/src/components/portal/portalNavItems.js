import { PORTAL_ICONS, SITE_ICONS } from "../../lib/siteIcons";
import { PORTAL_ROUTES as R } from "../../lib/appRoutes";

/** Voci menu area associati — unica fonte per etichette e icone. */
export const PORTAL_NAV = [
  { to: R.root, icon: SITE_ICONS.dashboard, label: "Dashboard", end: true },
  { to: R.comunicazioniInterne, icon: SITE_ICONS.comunicazioni, label: "Comunicazioni interne" },
  { to: R.calendario, icon: SITE_ICONS.events, label: "Calendario" },
  { to: R.storicoArbitrale, icon: SITE_ICONS.storico, label: "Storico arbitrale" },
  { to: R.documenti, icon: SITE_ICONS.documents, label: "Documenti" },
  { to: R.utility, icon: SITE_ICONS.utility, label: "Utility" },
  { to: R.galleria, icon: SITE_ICONS.gallery, label: "Galleria" },
  { to: R.premiEMenzioni, icon: SITE_ICONS.premi, label: "Premi e menzioni" },
  { to: R.messaggi, icon: SITE_ICONS.messagesChat, label: "Messaggi" },
  { to: R.profilo, icon: SITE_ICONS.profilo, label: "Profilo" },
];

export { PORTAL_ICONS };

/** Icona menu per path area riservata. */
export function portalIconForPath(path) {
  const item =
    PORTAL_NAV.find((n) => n.to === path) ||
    PORTAL_NAV.find((n) => path.startsWith(`${n.to}/`) || path.startsWith(`${n.to}?`));
  return item?.icon ?? SITE_ICONS.dashboard;
}
