import { formatIgCount } from "../instagram-widget-utils";

describe("formatIgCount", () => {
  it("formats millions", () => {
    expect(formatIgCount(3100000)).toBe("3.1M");
  });

  it("formats thousands", () => {
    expect(formatIgCount(1200)).toBe("1.2K");
  });

  it("returns plain numbers for small counts", () => {
    expect(formatIgCount(796)).toBe("796");
  });

  it("returns null for invalid", () => {
    expect(formatIgCount(null)).toBeNull();
  });
});
