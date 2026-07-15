import DesignationsTableBody from "./DesignationsTableBody";

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
  );
}
