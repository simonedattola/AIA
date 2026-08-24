import {
  DOCUMENT_TITLE_BY_SLUG,
  documentTitleSegmentForPath,
  formatDocumentTitle,
} from "../documentTitle";

describe("formatDocumentTitle", () => {
  it("aggiunge il punto e AIA Legnano", () => {
    expect(formatDocumentTitle("Home")).toBe("Home · AIA Legnano");
    expect(formatDocumentTitle("Arbitri")).toBe("Arbitri · AIA Legnano");
  });

  it("non duplica il brand", () => {
    expect(formatDocumentTitle("Home · AIA Legnano")).toBe("Home · AIA Legnano");
    expect(formatDocumentTitle("Dashboard · AIA Legnano")).toBe("Dashboard · AIA Legnano");
  });

  it("restituisce solo il brand se vuoto", () => {
    expect(formatDocumentTitle("")).toBe("AIA Legnano");
    expect(formatDocumentTitle(null)).toBe("AIA Legnano");
  });
});

describe("documentTitleSegmentForPath", () => {
  it("mappa home e arbitri (non associati)", () => {
    expect(documentTitleSegmentForPath("/")).toBe("Home");
    expect(documentTitleSegmentForPath("/arbitri")).toBe("Arbitri");
    expect(documentTitleSegmentForPath("/arbitri")).not.toBe("Associati");
  });

  it("mappa area associati per pagina", () => {
    expect(documentTitleSegmentForPath("/area-associati")).toBe("Dashboard");
    expect(documentTitleSegmentForPath("/area-associati/profilo")).toBe("Profilo");
    expect(documentTitleSegmentForPath("/area-associati/storico-arbitrale")).toBe(
      "Storico arbitrale"
    );
    expect(documentTitleSegmentForPath("/area-associati/login")).toBe(
      "Accesso area associati"
    );
  });

  it("mappa amministrazione per pagina", () => {
    expect(documentTitleSegmentForPath("/amministrazione")).toBe("Dashboard");
    expect(documentTitleSegmentForPath("/amministrazione/anagrafica")).toBe("Anagrafica");
    expect(documentTitleSegmentForPath("/amministrazione/designazioni")).toBe("Designazioni");
    expect(documentTitleSegmentForPath("/amministrazione/login")).toBe(
      "Accesso amministrazione"
    );
    expect(documentTitleSegmentForPath("/amministrazione/articoli/abc")).toBe(
      "Modifica articolo"
    );
  });
});

describe("DOCUMENT_TITLE_BY_SLUG", () => {
  it("usa Arbitri e non Associati", () => {
    expect(DOCUMENT_TITLE_BY_SLUG.arbitri).toBe("Arbitri");
    expect(DOCUMENT_TITLE_BY_SLUG.home).toBe("Home");
  });
});
