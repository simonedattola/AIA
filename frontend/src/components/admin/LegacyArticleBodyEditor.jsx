import { useState } from "react";
import ArticleProse from "../ArticleProse";
import { Code, Eye } from "lucide-react";

const textareaCls =
  "w-full min-h-[28rem] px-3 py-2 border border-slate-300 rounded-md font-mono text-xs leading-relaxed focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none";

export default function LegacyArticleBodyEditor({ value, onChange }) {
  const [mode, setMode] = useState("preview");

  return (
    <div className="border border-slate-300 rounded-md bg-white overflow-hidden" data-testid="legacy-article-body-editor">
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 border-b border-slate-200 bg-slate-50">
        <p className="text-xs text-slate-600">
          Articolo importato da WordPress — usa l&apos;anteprima fedele o modifica il codice HTML (iframe, gallerie, tabelle).
        </p>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => setMode("preview")}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium ${
              mode === "preview" ? "bg-navy-600 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Eye className="h-3.5 w-3.5" /> Anteprima
          </button>
          <button
            type="button"
            onClick={() => setMode("html")}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium ${
              mode === "html" ? "bg-navy-600 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Code className="h-3.5 w-3.5" /> HTML
          </button>
        </div>
      </div>

      {mode === "preview" ? (
        <div className="p-6 max-w-none">
          {value?.trim() ? (
            <ArticleProse html={value} testId="legacy-article-preview" />
          ) : (
            <p className="text-sm text-slate-500">Nessun contenuto.</p>
          )}
        </div>
      ) : (
        <textarea
          value={value || ""}
          onChange={(e) => onChange?.(e.target.value)}
          className={textareaCls}
          spellCheck={false}
          data-testid="legacy-article-html"
        />
      )}
    </div>
  );
}
