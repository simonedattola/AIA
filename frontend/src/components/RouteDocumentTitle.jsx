import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import {
  documentTitleSegmentForPath,
  formatDocumentTitle,
  setDocumentTitle,
} from "../lib/documentTitle";

/** Imposta il titolo scheda da un segmento (es. "Home" → "Home · AIA Legnano"). */
export function useDocumentTitle(segment) {
  useEffect(() => {
    if (segment == null || segment === "") return undefined;
    setDocumentTitle(segment);
    return undefined;
  }, [segment]);
}

/**
 * Titolo scheda per ogni route. Evita che resti quello dell'ultima pagina CMS
 * quando si entra in area associati / amministrazione.
 */
export default function RouteDocumentTitle() {
  const { pathname } = useLocation();

  useEffect(() => {
    const segment = documentTitleSegmentForPath(pathname);
    document.title = formatDocumentTitle(segment);
  }, [pathname]);

  return null;
}
