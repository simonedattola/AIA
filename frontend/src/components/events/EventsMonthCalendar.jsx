import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  MONTHS_IT,
  WEEKDAYS_IT,
  buildMonthGrid,
  eventDateKey,
  groupEventsByDate,
  todayKey,
  ymdKey,
} from "../../lib/eventsDisplay";

const NAV_BTN =
  "inline-flex items-center justify-center p-2 rounded-md border border-white/30 text-white hover:bg-white/10 transition-colors";

/** Altezza fissa di ogni cella giorno — uguale per tutti i mesi, con o senza eventi. */
const DAY_CELL =
  "h-[4.75rem] sm:h-[5rem] rounded-md border p-1.5 sm:p-2 flex flex-col overflow-hidden";

export default function EventsMonthCalendar({
  events = [],
  month,
  onMonthChange,
  selectedEventId,
  onSelectEvent,
  className = "",
}) {
  const year = month.getFullYear();
  const monthIndex = month.getMonth();
  const byDate = groupEventsByDate(events);
  const cells = buildMonthGrid(year, monthIndex);
  const today = todayKey();

  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col ${className}`}
      data-testid="events-month-calendar"
    >
      <div className="flex items-center justify-between gap-3 px-4 sm:px-5 py-4 bg-gradient-to-r from-navy-700 to-navy-600 text-white shrink-0">
        <button type="button" onClick={() => onMonthChange(-1)} className={NAV_BTN} aria-label="Mese precedente">
          <ChevronLeft className="h-5 w-5" />
        </button>
        <div className="text-center">
          <p className="text-[10px] uppercase tracking-[0.2em] text-gold-400 font-semibold mb-0.5">Calendario</p>
          <h2 className="font-display text-lg sm:text-xl font-bold capitalize">
            {MONTHS_IT[monthIndex]} {year}
          </h2>
        </div>
        <button type="button" onClick={() => onMonthChange(1)} className={NAV_BTN} aria-label="Mese successivo">
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>

      <div className="p-3 sm:p-4">
        <div className="grid grid-cols-7 gap-1 mb-1.5">
          {WEEKDAYS_IT.map((wd) => (
            <div
              key={wd}
              className="text-center text-[10px] sm:text-xs font-bold uppercase tracking-wide text-navy-600/70 py-1"
            >
              {wd}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1 auto-rows-[4.75rem] sm:auto-rows-[5rem]">
          {cells.map((day, idx) => {
            if (day === null) {
              return <div key={`empty-${idx}`} className={DAY_CELL} aria-hidden />;
            }
            const dateKey = ymdKey(year, monthIndex, day);
            const dayEvents = byDate[dateKey] || [];
            const isToday = dateKey === today;
            const hasSelected = dayEvents.some((e) => e.id === selectedEventId);

            return (
              <div
                key={dateKey}
                className={`${DAY_CELL} transition-colors ${
                  isToday
                    ? "border-navy-600 bg-navy-50/60 shadow-sm"
                    : hasSelected
                      ? "border-gold-400 bg-gold-50/50 shadow-sm"
                      : dayEvents.length
                        ? "border-slate-200 bg-slate-50/80"
                        : "border-slate-100 bg-white"
                }`}
              >
                <span
                  className={`text-[11px] sm:text-xs font-semibold leading-none shrink-0 ${
                    isToday ? "text-navy-700" : "text-slate-600"
                  }`}
                >
                  {day}
                </span>
                <div className="flex-1 min-h-0 mt-0.5 flex flex-col gap-0.5 overflow-hidden">
                  {dayEvents.map((ev) => {
                    const selected = ev.id === selectedEventId;
                    const past = eventDateKey(ev.date) < today;
                    return (
                      <button
                        key={ev.id}
                        type="button"
                        onClick={() => onSelectEvent(ev)}
                        title={ev.titolo}
                        className={`flex-1 min-h-0 w-full overflow-hidden text-left px-1 py-1 rounded transition-colors ${
                          selected
                            ? "bg-gold-400 text-navy-900 font-semibold ring-1 ring-gold-500/80"
                            : past
                              ? "bg-slate-200/90 text-slate-700 hover:bg-slate-300/90"
                              : "bg-navy-600 text-white hover:bg-navy-700"
                        }`}
                      >
                        <span className="block text-[9px] sm:text-[10px] leading-tight line-clamp-3">
                          {ev.titolo}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
