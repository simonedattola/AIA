/**
 * Icone Lucide condivise — unica fonte per admin, portale associati e componenti.
 */
import {
  Award,
  BookOpen,
  Calendar,
  ClipboardList,
  FileText,
  FolderOpen,
  GraduationCap,
  Images,
  Inbox,
  LayoutDashboard,
  Layers,
  ListChecks,
  MessageSquare,
  MessageSquareQuote,
  Newspaper,
  Settings,
  User,
  Users,
} from "lucide-react";

export const SITE_ICONS = {
  dashboard: LayoutDashboard,
  anagrafica: Users,
  members: Users,
  designations: ListChecks,
  comunicazioni: Newspaper,
  articles: BookOpen,
  events: Calendar,
  messagesSite: Inbox,
  messagesChat: MessageSquare,
  leads: GraduationCap,
  gallery: Images,
  testimonials: MessageSquareQuote,
  documents: FileText,
  utility: FolderOpen,
  pages: Layers,
  settings: Settings,
  storico: ClipboardList,
  premi: Award,
  profilo: User,
};

/** Alias per pagine admin (stesse icone del menu). */
export const ADMIN_ICONS = SITE_ICONS;

/** Icone area associati — stessi simboli, chiavi orientate al portale. */
export const PORTAL_ICONS = {
  dashboard: SITE_ICONS.dashboard,
  storico: SITE_ICONS.storico,
  calendario: SITE_ICONS.events,
  utility: SITE_ICONS.utility,
  comunicazioni: SITE_ICONS.comunicazioni,
  documenti: SITE_ICONS.documents,
  premi: SITE_ICONS.premi,
  media: SITE_ICONS.gallery,
  messaggi: SITE_ICONS.messagesChat,
  profilo: SITE_ICONS.profilo,
};
