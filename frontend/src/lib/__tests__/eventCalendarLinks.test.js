import {
  buildIcsContent,
  eventStartDate,
  googleCalendarUrl,
  icsFilename,
} from "../eventCalendarLinks";

const sample = {
  id: "evt-123",
  titolo: "Riunione tecnica",
  date: "2026-09-15",
  orario: "18:30",
  luogo: "Sede AIA Legnano",
  descrizione: "Portare regolamento",
};

describe("eventCalendarLinks", () => {
  it("parses start date", () => {
    const d = eventStartDate(sample);
    expect(d).toBeInstanceOf(Date);
    expect(Number.isNaN(d.getTime())).toBe(false);
  });

  it("builds google calendar url", () => {
    const url = googleCalendarUrl(sample);
    expect(url).toContain("calendar.google.com/calendar/render");
    expect(url).toContain("action=TEMPLATE");
    expect(url).toContain("Riunione");
  });

  it("builds ics content", () => {
    const ics = buildIcsContent(sample);
    expect(ics).toContain("BEGIN:VEVENT");
    expect(ics).toContain("SUMMARY:Riunione tecnica");
    expect(ics).toContain("LOCATION:Sede AIA Legnano");
    expect(icsFilename(sample)).toMatch(/\.ics$/);
  });
});
