import { formatPersonName } from "../format";

describe("formatPersonName", () => {
  it("title-cases all caps", () => {
    expect(formatPersonName("MARIO", "ROSSI")).toBe("Mario Rossi");
    expect(formatPersonName(null, null, "LORENZO ALESSIO")).toBe("Lorenzo Alessio");
  });
});
