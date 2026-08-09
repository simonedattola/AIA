import { Link } from "react-router-dom";
import { CalendarDays } from "lucide-react";
import { formatDateIt } from "../../lib/format";
import {
  displayDesignationGara,
  formatDesignationMeta,
} from "../../lib/designationsDisplay";
import DesignationsTableBody from "./DesignationsTableBody";

function NominativoLink({ d }) {
  const label = d.memberName || "—";
  const slug = (d.memberSlug || "").trim();
  if (!slug) {
    return <span className="text-slate-700">{label}</span>;
  }
  return (
    <Link
      to={`/arbitri/${slug}`}
      className="inline-block text-navy-600 hover:text-navy-800 font-medium underline underline-offset-2 decoration-navy-300 hover:decoration-navy-600"
      data-testid={`designazione-nominativo-${slug}`}
      onClick={(e) => e.stopPropagation()}
      onTouchStart={(e) => e.stopPropagation()}
    >
      {label}
    </Link>
  );
}

function DesignationsMobileList({
  designations,
  showNominativo = false,
  rowTestIdPrefix = "member-designation",
}) {
  return (
    <ul className="divide-y divide-slate-200 lg:hidden" data-testid="designations-mobile-list">
      {designations.map((d, idx) => (
        <li
          key={d.id || idx}
          className={`px-4 py-3.5 ${idx % 2 === 0 ? "bg-white" : "bg-slate-50"}`}
          data-testid={d.id ? `${rowTestIdPrefix}-${d.id}` : undefined}
        >
          <div className="flex items-start justify-between gap-3 mb-2">
            <span className="inline-flex items-center gap-1.5 text-sm text-slate-700 whitespace-nowrap">
              <CalendarDays className="h-4 w-4 text-gold-400 shrink-0" />
              {formatDateIt(d.matchDate, { short: true })}
            </span>
            <span className="text-xs bg-navy-50 text-navy-700 px-2.5 py-1 rounded font-medium shrink-0">
              {d.role}
            </span>
          </div>
          <p className="text-sm font-medium text-navy-700 leading-snug break-words">
            {displayDesignationGara(d)}
          </p>
          <p className="text-xs text-slate-500 mt-1 break-words">{formatDesignationMeta(d)}</p>
          {showNominativo && (
            <p className="text-sm mt-2">
              <NominativoLink d={d} />
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

export default function DesignationsDataTable({
  designations = [],
  showNominativo = false,
  className = "",
  maxVisibleRows = null,
  tableTestId = "designations-data-table",
  rowTestIdPrefix = "member-designation",
}) {
  if (!designations.length) return null;

  const scrollable = maxVisibleRows != null && maxVisibleRows > 0;
  const rowPx = 52;
  const headPx = 44;
  const scrollMaxHeight = scrollable ? headPx + maxVisibleRows * rowPx : undefined;

  return (
    <div
      className={`border border-slate-200 rounded-xl overflow-hidden shadow-sm ${className}`}
      data-testid={tableTestId === "designations-data-table" ? "designations-data-table" : undefined}
    >
      <DesignationsMobileList
        designations={designations}
        showNominativo={showNominativo}
        rowTestIdPrefix={rowTestIdPrefix}
      />
      <div
        className={`hidden lg:block min-w-0 ${scrollable ? "overflow-y-auto" : ""}`}
        style={scrollMaxHeight ? { maxHeight: `${scrollMaxHeight}px` } : undefined}
        data-testid={scrollable ? "designations-scroll" : undefined}
      >
        <DesignationsTableBody
          designations={designations}
          showNominativo={showNominativo}
          tableTestId={tableTestId}
          rowTestIdPrefix={rowTestIdPrefix}
          stickyHeader={scrollable}
        />
      </div>
    </div>
  );
}
