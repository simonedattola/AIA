import { formatPersonName } from "../format";

describe("formatPersonName", () => {
  it("title-cases all caps", () => {
    expect(formatPersonName("MARIO", "ROSSI")).toBe("Mario Rossi");
    expect(formatPersonName(null, null, "LORENZO ALESSIO")).toBe("Lorenzo Alessio");
  });

  it("handles Italian surnames with apostrophes", () => {
    expect(formatPersonName("NICOLO'", "D'AZZEO")).toBe("Nicolo' D'Azzeo");
    expect(formatPersonName("MATTEO", "DELL'ACQUA")).toBe("Matteo Dell'Acqua");
    expect(formatPersonName("CHRISTIAN", "IANNO'")).toBe("Christian Ianno'");
    expect(formatPersonName("NICOLO'", "LO GAGLIO")).toBe("Nicolo' Lo Gaglio");
    expect(formatPersonName("FABIO", "RE FERRE'")).toBe("Fabio Re Ferre'");
    expect(formatPersonName("ALESSANDRO FILIPPO", "ROMBOLA'")).toBe(
      "Alessandro Filippo Rombola'"
    );
  });

  it("normalizes curly apostrophes", () => {
    expect(formatPersonName("MATTEO", "DELL\u2019ACQUA")).toBe("Matteo Dell'Acqua");
    expect(formatPersonName("NICOLO\u2019", "D\u2019AZZEO")).toBe("Nicolo' D'Azzeo");
  });
});
