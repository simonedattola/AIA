import { cn } from "../utils";

describe("cn + design-system font sizes", () => {
  it("keeps text-ds-section when merged with text color", () => {
    expect(
      cn(
        "font-display font-bold text-ds-section sm:text-ds-section-lg tracking-tight text-navy-700",
        "mb-2"
      )
    ).toContain("text-ds-section");
    expect(
      cn(
        "font-display font-bold text-ds-section sm:text-ds-section-lg tracking-tight text-navy-700",
        "mb-2"
      )
    ).toContain("text-navy-700");
  });

  it("keeps text-ds-cta when color override is text-white", () => {
    const result = cn(
      "font-display font-bold text-ds-cta sm:text-ds-cta-md lg:text-ds-cta-lg leading-[1.1] tracking-tight text-navy-700",
      "mb-6 whitespace-pre-line text-white"
    );
    expect(result).toContain("text-ds-cta");
    expect(result).toContain("text-white");
    expect(result).not.toContain("text-navy-700");
  });

  it("keeps text-ds-subsection with navy color", () => {
    const result = cn(
      "font-display font-bold text-ds-subsection sm:text-ds-subsection-lg tracking-tight text-navy-700",
      "mb-8 text-center"
    );
    expect(result).toContain("text-ds-subsection");
    expect(result).toContain("text-navy-700");
  });

  it("keeps text-ds-page with font-bold and color", () => {
    const result = cn(
      "font-display font-bold text-ds-page sm:text-ds-page-lg tracking-tight text-navy-700",
      "text-2xl sm:text-3xl font-bold tracking-tight mb-1"
    );
    expect(result).toContain("font-bold");
    expect(result).toContain("text-navy-700");
  });
});
