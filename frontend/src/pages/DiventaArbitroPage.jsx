import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import SystemCmsPage from "./SystemCmsPage";

export default function DiventaArbitroPage() {
  const { hash } = useLocation();
  useEffect(() => {
    if (hash !== "#form") return;
    const t = setTimeout(() => document.getElementById("form")?.scrollIntoView({ behavior: "smooth", block: "start" }), 150);
    return () => clearTimeout(t);
  }, [hash]);
  return <SystemCmsPage slug="diventa-arbitro" testId="diventa-arbitro-page" />;
}
