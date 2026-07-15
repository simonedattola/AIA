import { formatDateIt } from "../../lib/format";
import { eventDateKey, MONTHS_SHORT } from "../../lib/eventsDisplay";
import { displayDesignationGara, formatDesignationMeta } from "../../lib/designationsDisplay";

export default function PortalDesignationCard({ designation: d }) {
  const dateKey = eventDateKey(d.matchDate);
  const date = dateKey ? new Date(`${dateKey}T12:00:00`) : null;

  return (
    <article className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm flex flex-col sm:flex-row sm:items-stretch">
      <div className="flex sm:flex-col items-center gap-3 sm:gap-0 sm:w-[4.5rem] shrink-0 bg-navy-600 text-white px-4 py-3 sm:py-4">
        {date ? (
          <>
            <div className="text-2xl font-bold leading-none tabular-nums">
              {date.getDate().toString().padStart(2, "0")}
            </div>
            <div className="text-[10px] uppercase tracking-wider text-gold-400 font-semibold sm:mt-0.5">
              {MONTHS_SHORT[date.getMonth()]}
            </div>
          </>
        ) : (
          <div className="text-xs font-semibold uppercase tracking-wider text-gold-400">—</div>
        )}
      </div>

      <div className="flex-1 min-w-0 px-4 py-3 sm:py-4 flex flex-col justify-center border-b sm:border-b-0 sm:border-r border-slate-100">
        <h2 className="font-display text-base sm:text-lg font-bold text-navy-800 leading-snug line-clamp-2">
          {displayDesignationGara(d)}
        </h2>
        {dateKey && (
          <p className="mt-1 text-xs text-slate-500">{formatDateIt(d.matchDate, { short: true })}</p>
        )}
        <p className="mt-1 text-xs text-slate-600 line-clamp-2">{formatDesignationMeta(d)}</p>
      </div>

      <div className="sm:w-36 shrink-0 flex items-center justify-center px-3 py-4 bg-slate-50/80">
        <span className="inline-flex items-center justify-center px-2.5 py-1.5 rounded-md text-xs font-semibold bg-navy-50 text-navy-700 border border-navy-100 text-center">
          {d.role || "—"}
        </span>
      </div>
    </article>
  );
}
