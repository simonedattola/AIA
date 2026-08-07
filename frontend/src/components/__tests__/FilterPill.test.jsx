import { render, screen, fireEvent } from "@testing-library/react";
import { FilterPill } from "../../design-system/FilterPill";

describe("FilterPill", () => {
  it("renders label and reflects active state", () => {
    render(
      <FilterPill active data-testid="pill-arbitri">
        Arbitri
      </FilterPill>
    );
    const pill = screen.getByTestId("pill-arbitri");
    expect(pill).toHaveTextContent("Arbitri");
    expect(pill).toHaveAttribute("aria-pressed", "true");
  });

  it("calls onClick when pressed", () => {
    const onClick = jest.fn();
    render(
      <FilterPill onClick={onClick} data-testid="pill">
        Tutti
      </FilterPill>
    );
    fireEvent.click(screen.getByTestId("pill"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
