import { memo } from "react";
import { MapPin } from "lucide-react";
import { formatEventDateTimeIt } from "../../lib/format";
import { eventDateKey, MONTHS_SHORT, TYPE_COLOR, TYPE_LABEL } from "../../lib/eventsDisplay";
import { PortalPresenzaPanel } from "./PortalEventPresenza";
import { asAdminText } from "../../lib/safeText";

function PortalEventCard({ event, saving, onSetStato, onOpen }) {
  const dateKey = eventDateKey(asAdminText(event.date));
  const d = new Date(`${dateKey}T12:00:00`);
  const tipoKey = asAdminText(event.tipo).toLowerCase();
  const titolo = asAdminText(event.titolo, "Evento");
  const luogo = asAdminText(event.luogo);
  const tipoLabel = TYPE_LABEL[tipoKey] || asAdminText(event.tipo) || "Evento";
  const tipoColor = TYPE_COLOR[tipoKey] || "bg-slate-100 text-slate-700";
  const clickable = typeof onOpen === "function";

  const detailProps = clickable
    ? {
        role: "button",
        tabIndex: 0,
        onClick: () => onOpen(event),
        onKeyDown: (ev) => {
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            onOpen(event);
          }
        },
        className:
          "flex flex-1 min-w-0 flex-col sm:flex-row sm:items-stretch cursor-pointer",
        "aria-label": `Apri dettagli: ${titolo}`,
      }
    : {
        className: "flex flex-1 min-w-0 flex-col sm:flex-row sm:items-stretch",
      };

  return (
    <article
      className={`bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm flex flex-col sm:flex-row sm:items-stretch transition-colors ${
        clickable ? "hover:border-navy-300" : ""
      }`}
    >
      <div {...detailProps}>
        <div className="flex sm:flex-col items-center gap-3 sm:gap-0 sm:w-[4.5rem] shrink-0 bg-navy-600 text-white px-4 py-3 sm:py-4">
          <div className="text-2xl font-bold leading-none tabular-nums">
            {d.getDate().toString().padStart(2, "0")}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-gold-400 font-semibold sm:mt-0.5">
            {MONTHS_SHORT[d.getMonth()]}
          </div>
        </div>

        <div className="flex-1 min-w-0 px-4 py-3 sm:py-4 flex flex-col justify-center border-b sm:border-b-0 sm:border-r border-slate-100">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-semibold ${tipoColor}`}>
              {tipoLabel}
            </span>
            {Array.isArray(event.attachments) && event.attachments.length > 0 && (
              <span className="text-[10px] text-slate-500 font-medium">
                {event.attachments.length} {event.attachments.length === 1 ? "allegato" : "allegati"}
              </span>
            )}
          </div>
          <h2 className="font-display text-base sm:text-lg font-bold text-navy-800 leading-snug line-clamp-2">
            {titolo}
          </h2>
          <p className="mt-1 text-xs text-slate-500">{formatEventDateTimeIt(asAdminText(event.date), asAdminText(event.orario), asAdminText(event.orarioFine))}</p>
          {luogo && (
            <p className="mt-1 text-xs text-slate-600 flex items-center gap-1 line-clamp-1">
              <MapPin className="h-3.5 w-3.5 shrink-0 text-navy-500" />
              {luogo}
            </p>
          )}
        </div>
      </div>

      {onSetStato && (
        <div className="sm:w-36 shrink-0" onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
          <PortalPresenzaPanel event={event} saving={saving} onSetStato={onSetStato} />
        </div>
      )}
    </article>
  );
}

export default memo(PortalEventCard);
