import { Fragment } from "react";
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
      className="inline-block text-navy-600 hover:text-navy-800 font-medium underline underline-offset-2 decoration-navy-300 hover:decoration-navy-600"
      data-testid={`designazione-nominativo-${slug}`}
    >
      {label}
    </Link>
  );
}

export default function DesignationsTableBody({
  designations = [],
  showNominativo = false,
  renderNominativo,
  renderActions,
  tableTestId,
  rowTestIdPrefix = "member-designation",
  stickyHeader = false,
  isRowSelected,
  renderRowAfter,
}) {
  if (!designations.length) return null;

  const showNominativoCol = showNominativo || renderNominativo;
  const showActionsCol = typeof renderActions === "function";
  const colSpan = 4 + (showNominativoCol ? 1 : 0) + (showActionsCol ? 1 : 0);

  return (
    <table className="w-full min-w-0 md:min-w-[680px]" data-testid={tableTestId}>
      <thead>
        <tr
          className={`bg-navy-700 text-white text-left text-xs uppercase tracking-wider${
            stickyHeader ? " sticky top-0 z-10" : ""
          }`}
        >
          <th className="px-4 py-3 font-semibold">Data</th>
          <th className="px-4 py-3 font-semibold">Campionato</th>
          <th className="px-4 py-3 font-semibold">Gara</th>
          <th className="px-4 py-3 font-semibold">Ruolo</th>
          {showNominativoCol && <th className="px-4 py-3 font-semibold">Nominativo</th>}
          {showActionsCol && <th className="px-4 py-3 font-semibold text-right">Azioni</th>}
        </tr>
      </thead>
      <tbody>
        {designations.map((d, idx) => {
          const selected = isRowSelected?.(d);
          const zebra = idx % 2 === 0 ? "bg-white" : "bg-slate-50";
          return (
            <Fragment key={d.id || idx}>
              <tr
                className={`${selected ? "bg-navy-50 ring-1 ring-inset ring-navy-200" : zebra}`}
                data-testid={d.id ? `${rowTestIdPrefix}-${d.id}` : undefined}
              >
                <td className="px-4 py-3.5 text-sm whitespace-nowrap text-slate-700">
                  <span className="inline-flex items-center gap-1.5">
                    <CalendarDays className="h-4 w-4 text-gold-400 shrink-0" />
                    {formatDateIt(d.matchDate, { short: true })}
                  </span>
                </td>
                <td className="px-4 py-3.5 text-sm text-slate-600">{formatDesignationMeta(d)}</td>
                <td className="px-4 py-3.5 text-sm font-medium text-navy-700">{displayDesignationGara(d)}</td>
                <td className="px-4 py-3.5 text-sm">
                  <span className="text-xs bg-navy-50 text-navy-700 px-2.5 py-1 rounded font-medium whitespace-nowrap">
                    {d.role}
                  </span>
                </td>
                {showNominativoCol && (
                  <td className="px-4 py-3.5 text-sm">
                    {renderNominativo ? renderNominativo(d) : <NominativoLink d={d} />}
                  </td>
                )}
                {showActionsCol && (
                  <td className="px-4 py-3.5 text-sm text-right whitespace-nowrap">{renderActions(d)}</td>
                )}
              </tr>
              {selected && renderRowAfter && (
                <tr>
                  <td colSpan={colSpan} className="p-0">
                    {renderRowAfter(d)}
                  </td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
