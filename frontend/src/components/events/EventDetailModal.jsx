import { X, MapPin, CalendarDays, CalendarPlus, Download } from "lucide-react";
import { formatEventDateTimeIt } from "../../lib/format";
import { TYPE_LABEL, TYPE_COLOR } from "../../lib/eventsDisplay";
import { AttachmentList } from "../AttachmentList";
import { downloadEventIcs, googleCalendarUrl } from "../../lib/eventCalendarLinks";

export default function EventDetailModal({
  event,
  onClose,
  showAttachments = false,
  showCalendarActions = true,
}) {
  if (!event) return null;

  const tipoKey = (event.tipo || "").toLowerCase();
  const gcal = showCalendarActions ? googleCalendarUrl(event) : "";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="event-modal-title"
      data-testid="event-detail-modal"
    >
      <div
        className="bg-white rounded-lg border border-slate-200 shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b border-slate-100 px-6 py-4 flex justify-between items-start gap-4">
          <div>
            <span
              className={`inline-block text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded ${
                TYPE_COLOR[tipoKey] || "bg-slate-100 text-slate-700"
              }`}
            >
              {TYPE_LABEL[tipoKey] || event.tipo}
            </span>
            <h2 id="event-modal-title" className="font-display text-xl font-bold text-navy-700 mt-2 leading-tight">
              {event.titolo}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded"
            aria-label="Chiudi"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <p className="flex items-center gap-2 text-sm text-slate-600">
            <CalendarDays className="h-4 w-4 text-gold-500 shrink-0" />
            {formatEventDateTimeIt(event.date, event.orario, event.orarioFine)}
          </p>
          {event.luogo && (
            <p className="flex items-center gap-2 text-sm text-slate-600">
              <MapPin className="h-4 w-4 text-navy-500 shrink-0" />
              {event.luogo}
            </p>
          )}
          {event.descrizione && (
            <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-line">{event.descrizione}</p>
          )}
          {showAttachments && <AttachmentList attachments={event.attachments} />}

          {showCalendarActions && (gcal || event.date) && (
            <div
              className="pt-2 border-t border-slate-100 space-y-2"
              data-testid="event-calendar-actions"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Aggiungi al tuo calendario
              </p>
              <div className="flex flex-wrap gap-2">
                {gcal && (
                  <a
                    href={gcal}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-navy-700 text-white text-sm font-medium hover:bg-navy-800"
                    data-testid="event-add-google-calendar"
                  >
                    <CalendarPlus className="h-4 w-4" />
                    Google Calendar
                  </a>
                )}
                <button
                  type="button"
                  onClick={() => downloadEventIcs(event)}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-md border border-slate-300 text-navy-700 text-sm font-medium hover:border-navy-500 hover:bg-slate-50"
                  data-testid="event-download-ics"
                >
                  <Download className="h-4 w-4" />
                  Apple / Outlook (.ics)
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
