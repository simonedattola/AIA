import DesignationsTableBody from "./DesignationsTableBody";
import DesignationsMobileList from "./DesignationsMobileList";

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
      className={className}
      data-testid={tableTestId === "designations-data-table" ? "designations-data-table" : undefined}
    >
      <div className="md:hidden" data-testid="designations-mobile">
        <div
          className={scrollable ? "overflow-y-auto pr-0.5" : undefined}
          style={scrollMaxHeight ? { maxHeight: `${scrollMaxHeight}px` } : undefined}
          data-testid={scrollable ? "designations-scroll-mobile" : undefined}
        >
          <DesignationsMobileList
            designations={designations}
            showNominativo={showNominativo}
            rowTestIdPrefix={rowTestIdPrefix}
          />
        </div>
      </div>

      <div
        className={`hidden md:block border border-slate-200 rounded-xl overflow-hidden shadow-sm`}
      >
        <div
          className={scrollable ? "overflow-y-auto overflow-x-auto" : "overflow-x-auto"}
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
    </div>
  );
}
