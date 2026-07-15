import { useCallback, useEffect, useState } from "react";
import { adminPresenzeEvento, adminPresenzeEventoSave } from "../../lib/api";
import { Save, Users } from "lucide-react";
import { Button } from "@/design-system";
import { AdminEmptyState } from "./admin-ui";

const PRESENZA_STATI_ADMIN = ["PRESENTE", "ASSENTE", "NON_RISPOSTO"];

function statoLabel(s) {
  if (s === "IN_DUBBIO") return "In dubbio (da confermare)";
  return (s || "NON_RISPOSTO").replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
}

function statoOptionsForRow(stato) {
  if (stato === "IN_DUBBIO") {
    return ["IN_DUBBIO", ...PRESENZA_STATI_ADMIN];
  }
  return PRESENZA_STATI_ADMIN;
}

export default function EventPresenzePanel({ eventId, invitedCount = 0 }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    if (!eventId) return;
    setLoading(true);
    setError("");
    adminPresenzeEvento(eventId)
      .then((res) => setRows(res.associati || []))
      .catch(() => setError("Impossibile caricare le presenze"))
      .finally(() => setLoading(false));
  }, [eventId]);

  useEffect(() => {
    load();
  }, [load]);

  const setStato = (memberId, stato) => {
    setRows((prev) => prev.map((r) => (r.memberId === memberId ? { ...r, stato } : r)));
  };

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      await adminPresenzeEventoSave(
        eventId,
        rows.map((r) => ({ memberId: r.memberId, stato: r.stato }))
      );
      load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Salvataggio non riuscito");
    } finally {
      setSaving(false);
    }
  };

  if (!eventId) return null;

  return (
    <div data-testid="event-presenze-panel">
      <p className="text-sm text-slate-600 mb-4">
        {invitedCount > 0
          ? `Presenze degli ${invitedCount} associati invitati a questo evento.`
          : "Presenze di tutti gli associati (nessun invito selettivo impostato)."}
      </p>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-500">Caricamento presenze…</p>
      ) : rows.length === 0 ? (
        <AdminEmptyState icon={Users} title="Nessun associato in anagrafica." />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {rows.map((r) => (
              <div
                key={r.memberId}
                className="border border-slate-200 rounded-lg px-3 py-2.5 bg-slate-50/50"
                data-testid={`presenza-row-${r.memberId}`}
              >
                <div className="text-sm font-medium text-navy-700 truncate mb-2" title={r.nome}>
                  {r.nome}
                </div>
                <select
                  value={r.stato}
                  onChange={(e) => setStato(r.memberId, e.target.value)}
                  className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm bg-white"
                  data-testid={`presenza-${r.memberId}`}
                  aria-label={`Stato presenza di ${r.nome}`}
                >
                  {statoOptionsForRow(r.stato).map((s) => (
                    <option key={s} value={s}>
                      {statoLabel(s)}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          <Button type="button" onClick={save} disabled={saving} variant="primary" className="mt-4">
            <Save className="h-4 w-4" /> {saving ? "Salvataggio…" : "Salva presenze"}
          </Button>
        </>
      )}
    </div>
  );
}
