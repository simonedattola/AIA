import { asAdminText, asAdminCount } from "./safeText";

const pydantic = {
  type: "value_error",
  loc: ["body", "email"],
  msg: "value is not a valid email",
  input: "x",
  ctx: {},
};

describe("asAdminText", () => {
  it("keeps strings and finite numbers", () => {
    expect(asAdminText("Ciao")).toBe("Ciao");
    expect(asAdminText(12)).toBe("12");
  });

  it("extracts msg from Pydantic-like objects (React #31)", () => {
    expect(asAdminText(pydantic)).toBe("value is not a valid email");
  });

  it("returns fallback for empty or unknown objects", () => {
    expect(asAdminText(null, "—")).toBe("—");
    expect(asAdminText({ foo: 1 }, "—")).toBe("—");
  });
});

describe("asAdminCount", () => {
  it("coerces invalid stats to 0", () => {
    expect(asAdminCount(3)).toBe(3);
    expect(asAdminCount(pydantic)).toBe(0);
    expect(asAdminCount(null)).toBe(0);
  });
});
