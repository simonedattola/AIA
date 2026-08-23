import { asAdminList } from "../lib/api";

describe("asAdminList", () => {
  it("returns arrays unchanged", () => {
    const list = [{ id: "1" }];
    expect(asAdminList(list)).toBe(list);
  });

  it("returns empty array for non-array payloads", () => {
    expect(asAdminList({ email: "admin@test.it" })).toEqual([]);
    expect(asAdminList(null)).toEqual([]);
    expect(asAdminList(undefined)).toEqual([]);
  });
});
