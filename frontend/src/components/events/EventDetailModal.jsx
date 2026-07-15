import { X, MapPin, CalendarDays } from "lucide-react";
import { formatEventDateTimeIt } from "../../lib/format";
import { TYPE_LABEL, TYPE_COLOR } from "../../lib/eventsDisplay";
import { AttachmentList } from "../AttachmentList";

export default function EventDetailModal({ event, onClose, showAttachments = false }) {
  if (!event) return null;

  const tipoKey = (event.tipo || "").toLowerCase();

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
            {formatEventDateTimeIt(event.date, event.orario)}
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
        </div>
      </div>
    </div>
  );
}
