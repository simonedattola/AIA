import { SITE_ICONS } from "../../lib/siteIcons";
import DesignationsTableBody from "../designations/DesignationsTableBody";
import { formatSeasonLabel } from "../../lib/designationsDisplay";
import { PortalEmptyState } from "./portal-ui";

export { formatSeasonLabel, displayDesignationGara, formatDesignationMeta } from "../../lib/designationsDisplay";

export default function DesignationsTable({
  designations,
  seasonsAvailable = [],
  season,
  onSeasonChange,
  emptyMessage = "Nessuna designazione per questa stagione.",
}) {
  return (
    <>
      {seasonsAvailable.length > 0 && onSeasonChange && (
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <label className="flex items-center gap-2 text-sm text-slate-600 shrink-0">
            <span className="font-medium">Stagione</span>
            <select
              value={season || seasonsAvailable[0]}
              onChange={(e) => onSeasonChange(e.target.value)}
              className="border border-slate-300 rounded-md px-3 py-1.5 text-sm focus:border-navy-600 focus:outline-none"
            >
              {seasonsAvailable.map((s) => (
                <option key={s} value={s}>
                  {formatSeasonLabel(s)}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}
      {designations.length === 0 ? (
        <PortalEmptyState icon={SITE_ICONS.designations}>{emptyMessage}</PortalEmptyState>
      ) : (
        <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm overflow-x-auto">
          <DesignationsTableBody designations={designations} />
        </div>
      )}
    </>
  );
}
