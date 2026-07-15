import { SITE_ICONS } from "../../lib/siteIcons";
import { formatDateIt } from "../../lib/format";
import { AttachmentList } from "../AttachmentList";
import { PortalEmptyState } from "../portal/portal-ui";

const UtilityIcon = SITE_ICONS.utility;
const EventIcon = SITE_ICONS.events;

export default function UtilityRtoSessions({ sessions = [], emptyMessage }) {
  if (!sessions.length) {
    return (
      <PortalEmptyState icon={SITE_ICONS.utility}>
        {emptyMessage || "Nessun materiale eventi pubblicato."}
      </PortalEmptyState>
    );
  }

  return (
    <div className="space-y-4" data-testid="utility-event-material">
      {sessions.map((session) => (
        <article
          key={session.id}
          className="bg-white rounded-xl border border-slate-200 overflow-hidden"
          data-testid={`event-material-${session.id}`}
        >
          <div className="px-4 py-3 sm:px-5 sm:py-4 bg-slate-50 border-b border-slate-100 flex flex-wrap items-center gap-x-3 gap-y-1">
            <UtilityIcon className="h-4 w-4 text-navy-600 shrink-0" />
            <h3 className="font-display font-semibold text-navy-800">{session.titolo}</h3>
            {session.tipo && (
              <span className="text-xs bg-slate-200 text-slate-700 px-2 py-0.5 rounded">{session.tipo}</span>
            )}
            <span className="text-xs text-slate-500 inline-flex items-center gap-1 ml-auto">
              <EventIcon className="h-3.5 w-3.5" />
              {formatDateIt(session.date, { short: true })}
            </span>
          </div>
          <div className="p-4 sm:p-5">
            {session.descrizione && (
              <p className="text-sm text-slate-600 mb-3">{session.descrizione}</p>
            )}
            {session.utilityMaterial?.length > 0 ? (
              <AttachmentList attachments={session.utilityMaterial} showVideoPreview />
            ) : (
              <p className="text-sm text-slate-500">Nessun file in questa cartella.</p>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
