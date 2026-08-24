import { useEffect } from "react";
import {
  DOCUMENT_TITLE_BY_SLUG,
  setDocumentTitle,
} from "../lib/documentTitle";

/**
 * Meta description + titolo scheda per pagine CMS.
 * Per slug di sistema usa titoli canonici (es. arbitri → «Arbitri», non Associati).
 */
export default function PageMeta({ page, title: titleOverride }) {
  useEffect(() => {
    if (!page && !titleOverride) return;

    const slug = page?.slug;
    const canonical = slug ? DOCUMENT_TITLE_BY_SLUG[slug] : null;
    const title = titleOverride || canonical || page?.metaTitle || page?.title;
    if (title) setDocumentTitle(title);

    const desc = page?.metaDescription || page?.summary || "";
    let el = document.querySelector('meta[name="description"]');
    if (!el) {
      el = document.createElement("meta");
      el.setAttribute("name", "description");
      document.head.appendChild(el);
    }
    if (desc) el.setAttribute("content", desc);
  }, [page, titleOverride]);

  return null;
}
