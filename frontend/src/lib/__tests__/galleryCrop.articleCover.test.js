import {
  aspectOptionsForSlot,
  defaultAspectForPreset,
  galleryAspectRatio,
} from "../galleryCrop";

describe("article cover crop aspect", () => {
  it("uses 16:10 for article covers", () => {
    expect(defaultAspectForPreset("articleCover")).toBe("16:10");
    expect(galleryAspectRatio("16:10")).toBeCloseTo(1.6);
    expect(aspectOptionsForSlot("16:10")).toEqual([
      { id: "16:10", label: "Copertina 16:10", ratio: 16 / 10 },
    ]);
  });
});
