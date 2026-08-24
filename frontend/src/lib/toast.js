/* Tiny toast helper - global stack with custom event API.
   Usage: import { toast } from "../lib/toast";
          toast.success("Salvato!");  toast.error("Errore"); */
import { useEffect, useState, useCallback } from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";

let nextId = 1;
const listeners = new Set();

export const toast = {
  show(message, type = "info", duration = 3500) {
    const id = nextId++;
    listeners.forEach((l) => l({ type: "add", item: { id, message, type, duration } }));
    if (duration > 0) setTimeout(() => toast.dismiss(id), duration);
    return id;
  },
  success(m, d) { return this.show(m, "success", d); },
  error(m, d = 5000) { return this.show(m, "error", d); },
  info(m, d) { return this.show(m, "info", d); },
  dismiss(id) { listeners.forEach((l) => l({ type: "remove", id })); },
};

export function ToastContainer() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    const onEvt = (e) => {
      if (e.type === "add") setItems((prev) => [...prev, e.item]);
      if (e.type === "remove") setItems((prev) => prev.filter((x) => x.id !== e.id));
    };
    listeners.add(onEvt);
    return () => listeners.delete(onEvt);
  }, []);

  const close = useCallback((id) => toast.dismiss(id), []);

  return (
    <div className="fixed top-4 right-4 z-[100] space-y-2 pointer-events-none" data-testid="toast-container">
      {items.map((it) => {
        const Icon = it.type === "success" ? CheckCircle2 : it.type === "error" ? AlertTriangle : Info;
        const cls = it.type === "success"
          ? "bg-emerald-50 border-emerald-300 text-emerald-800"
          : it.type === "error"
          ? "bg-red-50 border-red-300 text-red-800"
          : "bg-navy-50 border-navy-300 text-navy-800";
        return (
          <div key={it.id} className={`pointer-events-auto flex items-start gap-3 max-w-md p-4 rounded-lg border shadow-lg ${cls} animate-fade-up`} data-testid={`toast-${it.type}`}>
            <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1 text-sm font-medium">{it.message}</div>
            <button onClick={() => close(it.id)} className="opacity-70 hover:opacity-100"><X className="h-4 w-4" /></button>
          </div>
        );
      })}
    </div>
  );
}

/* Helper to parse axios errors uniformly */
export function apiErrorMessage(err, fallback = "Errore. Riprova.") {
  const d = err?.response?.data;
  if (!d) return err?.message || fallback;
  if (typeof d === "string") return d;
  if (typeof d.detail === "string") return d.detail;
  if (Array.isArray(d.detail)) {
    // Pydantic validation errors
    return d.detail.map((e) => `${(e.loc || []).slice(-1)[0] || ""}: ${e.msg || e.message || ""}`.trim()).filter(Boolean).join(" · ") || fallback;
  }
  if (d.detail && typeof d.detail === "object") {
    if (typeof d.detail.msg === "string") return d.detail.msg;
    if (typeof d.detail.message === "string") return d.detail.message;
  }
  return fallback;
}
