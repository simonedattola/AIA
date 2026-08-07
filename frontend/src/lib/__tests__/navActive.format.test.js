import { isNavItemActive, normalizePublicNavItem } from "../navActive";
import { contactPreferenceLabel, formatDateShort } from "../format";

describe("navActive", () => {
  it("marks nested paths as active for section links", () => {
    expect(isNavItemActive("/news/foo", "/news")).toBe(true);
    expect(isNavItemActive("/", "/news")).toBe(false);
    expect(isNavItemActive("/", "/")).toBe(true);
  });

  it("normalizes legacy /associati href to /arbitri", () => {
    const item = normalizePublicNavItem({ href: "/associati", label: "Associati" });
    expect(item.href).toBe("/arbitri");
  });
});

describe("format helpers", () => {
  it("maps contact preference labels", () => {
    expect(contactPreferenceLabel("email")).toBe("Email");
    expect(contactPreferenceLabel("phone", { lowercase: true })).toBe("telefono");
  });

  it("formats short Italian dates", () => {
    expect(formatDateShort("2026-05-17")).toMatch(/17/);
  });
});
