import { Link } from "react-router-dom";
import { CalendarDays } from "lucide-react";
import { formatDateIt } from "../../lib/format";
import {
  displayDesignationGara,
  formatDesignationMeta,
} from "../../lib/designationsDisplay";

function NominativoLink({ d }) {
  const label = d.memberName || "—";
  const slug = (d.memberSlug || "").trim();
  if (!slug) {
    return <span className="text-slate-700">{label}</span>;
  }
  return (
    <Link
      to={`/arbitri/${slug}`}
      className="text-navy-600 hover:text-navy-800 font-medium underline underline-offset-2 decoration-navy-300 hover:decoration-navy-600"
      data-testid={`designazione-nominativo-${slug}`}
    >
      {label}
    </Link>
  );
}

export default function DesignationsMobileList({
  designations = [],
  showNominativo = false,
  renderNominativo,
  renderActions,
  rowTestIdPrefix = "member-designation",
}) {
  if (!designations.length) return null;

  const showNominativoCol = showNominativo || renderNominativo;
  const showActionsCol = typeof renderActions === "function";

  return (
    <ul className="flex flex-col gap-3" data-testid="designations-mobile-list">
      {designations.map((d, idx) => (
        <li
          key={d.id || idx}
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          data-testid={d.id ? `${rowTestIdPrefix}-${d.id}` : undefined}
        >
          <div className="flex items-start justify-between gap-3 mb-2">
            <span className="inline-flex items-center gap-1.5 text-sm text-slate-700 whitespace-nowrap">
              <CalendarDays className="h-4 w-4 text-gold-400 shrink-0" aria-hidden />
              {formatDateIt(d.matchDate, { short: true })}
            </span>
            <span className="text-xs bg-navy-50 text-navy-700 px-2.5 py-1 rounded font-medium shrink-0">
              {d.role}
            </span>
          </div>
          <p className="text-base font-semibold text-navy-700 leading-snug">
            {displayDesignationGara(d)}
          </p>
          <p className="mt-1 text-sm text-slate-600">{formatDesignationMeta(d)}</p>
          {showNominativoCol && (
            <p className="mt-2.5 text-sm">
              <span className="text-slate-500 mr-1.5">Nominativo</span>
              {renderNominativo ? renderNominativo(d) : <NominativoLink d={d} />}
            </p>
          )}
          {showActionsCol && (
            <div className="mt-3 pt-3 border-t border-slate-100 flex justify-end">
              {renderActions(d)}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
