import { useEffect } from "react";

export default function PageMeta({ page }) {
  useEffect(() => {
    if (!page) return;
    const title = page.metaTitle || page.title;
    if (title) document.title = title.includes("AIA") ? title : `${title} · AIA Legnano`;
    const desc = page.metaDescription || page.summary || "";
    let el = document.querySelector('meta[name="description"]');
    if (!el) {
      el = document.createElement("meta");
      el.setAttribute("name", "description");
      document.head.appendChild(el);
    }
    if (desc) el.setAttribute("content", desc);
  }, [page]);

  return null;
}
