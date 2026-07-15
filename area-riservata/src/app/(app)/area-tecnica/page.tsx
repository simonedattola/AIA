"use client";

import { useEffect, useState, useCallback } from "react";
import { useSession } from "next-auth/react";
import toast from "react-hot-toast";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader, PageError } from "@/components/ui/PageLoader";

const tipoIcons: Record<string, string> = {
  FILE_RTO: "📁",
  SLIDE: "📊",
  VIDEO: "🎬",
  QUIZ: "❓",
  REGOLAMENTO: "📜",
  CIRCOLARE: "📢",
  TEST_TECNICO: "📝",
};

type Doc = { id: string; titolo: string; tipo: string; url: string | null; filePath: string | null };
type Quiz = { id: string; titolo: string; url: string | null };
type Pref = { id: string; tipo: string; elementoId: string };

export default function AreaTecnicaPage() {
  const { status } = useSession();
  const [documenti, setDocumenti] = useState<Doc[]>([]);
  const [quiz, setQuiz] = useState<Quiz[]>([]);
  const [preferiti, setPreferiti] = useState<Pref[]>([]);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    const d = await apiFetch<{ documenti: Doc[]; quiz: Quiz[]; preferiti: Pref[] }>("/api/area-tecnica");
    if (!d) {
      setError(true);
      return;
    }
    setDocumenti(d.documenti);
    setQuiz(d.quiz);
    setPreferiti(d.preferiti);
  }, []);

  useEffect(() => {
    if (status === "authenticated") load();
  }, [status, load]);

  const togglePref = async (tipo: string, elementoId: string) => {
    const exists = preferiti.find((p) => p.tipo === tipo && p.elementoId === elementoId);
    if (exists) {
      await fetch(`/api/preferiti?id=${exists.id}`, { method: "DELETE", credentials: "same-origin" });
      toast.success("Rimosso dai preferiti");
    } else {
      await fetch("/api/preferiti", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ tipo, elementoId }),
      });
      toast.success("Aggiunto ai preferiti");
    }
    load();
  };

  const isPref = (tipo: string, id: string) =>
    preferiti.some((p) => p.tipo === tipo && p.elementoId === id);

  const prefItems = preferiti.map((p) => {
    const doc = documenti.find((d) => d.id === p.elementoId);
    const q = quiz.find((x) => x.id === p.elementoId);
    return doc?.titolo || q?.titolo || p.elementoId;
  });

  if (status === "loading") return <PageLoader />;
  if (error) return <PageError />;

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <div className="flex-1 space-y-6">
        <h1 className="text-2xl font-bold text-blue-900">Area tecnica / RTO</h1>

        <section className="card">
          <h2 className="font-semibold">Documenti e materiali</h2>
          <ul className="mt-3 divide-y">
            {documenti.map((d) => (
              <li key={d.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div className="flex items-center gap-2">
                  <span>{tipoIcons[d.tipo] || "📄"}</span>
                  <div>
                    <p className="font-medium">{d.titolo}</p>
                    <p className="text-xs text-slate-500">{d.tipo.replace("_", " ")}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  {(d.url || d.filePath) && (
                    <a
                      href={d.url || d.filePath || "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="btn-secondary text-xs"
                    >
                      Apri
                    </a>
                  )}
                  <button
                    type="button"
                    className="btn-secondary text-xs"
                    onClick={() => togglePref("DOCUMENTO", d.id)}
                  >
                    {isPref("DOCUMENTO", d.id) ? "★" : "☆"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h2 className="font-semibold">Quiz</h2>
          <ul className="mt-3 space-y-2">
            {quiz.map((q) => (
              <li key={q.id} className="flex justify-between py-2">
                <span>❓ {q.titolo}</span>
                <button type="button" className="btn-secondary text-xs" onClick={() => togglePref("QUIZ", q.id)}>
                  {isPref("QUIZ", q.id) ? "★" : "☆"}
                </button>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <aside className="card h-fit w-full lg:w-72">
        <h2 className="font-semibold">I miei preferiti</h2>
        <ul className="mt-3 space-y-2 text-sm">
          {prefItems.length === 0 && <li className="text-slate-500">Nessun preferito</li>}
          {prefItems.map((t, i) => (
            <li key={i}>★ {t}</li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
