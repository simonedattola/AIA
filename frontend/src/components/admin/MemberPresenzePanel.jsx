import { useEffect, useState } from "react";
import { adminPresenzeAssociato } from "../../lib/api";
import { formatDateIt } from "../../lib/format";
import { Calendar, UserCheck } from "lucide-react";
import { AdminEmptyState } from "./admin-ui";

function statoBadge(stato) {
  const s = (stato || "NON_RISPOSTO").toUpperCase();
  const cls =
    s === "PRESENTE"
      ? "bg-emerald-50 text-emerald-800"
      : s === "ASSENTE"
        ? "bg-red-50 text-red-700"
        : s === "IN_DUBBIO"
          ? "bg-amber-50 text-amber-800"
          : "bg-slate-100 text-slate-600";
  const label = s.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
  return <span className={`text-xs px-2 py-0.5 rounded font-medium ${cls}`}>{label}</span>;
}

export default function MemberPresenzePanel({ memberId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!memberId) return;
    setLoading(true);
    adminPresenzeAssociato(memberId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [memberId]);

  if (!memberId) return null;

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50" data-testid="member-presenze-panel">
      <div className="flex items-center gap-2 mb-3">
        <UserCheck className="h-5 w-5 text-navy-600" />
        <span className="font-medium text-navy-700">Presenze eventi</span>
        <span className="text-xs text-slate-400">(solo admin)</span>
      </div>
      {loading ? (
        <p className="text-sm text-slate-500">Caricamento…</p>
      ) : !data ? (
        <p className="text-sm text-slate-500">Impossibile caricare le presenze.</p>
      ) : (
        <>
          {data.stats && (
            <p className="text-sm text-slate-600 mb-3">
              Stagione {data.stats.stagione?.replace("-", "/")}:{" "}
              <strong>{data.stats.presenti}</strong> presenze ·{" "}
              <strong>{data.stats.assenti}</strong> assenze
            </p>
          )}
          {(data.eventi || []).length === 0 ? (
            <AdminEmptyState icon={Calendar} title="Nessun evento in calendario." />
          ) : (
            <div className="bg-white border border-slate-200 rounded-md overflow-x-auto max-h-56 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-50 text-xs uppercase text-slate-500 text-left">
                  <tr>
                    <th className="px-3 py-2">Data</th>
                    <th className="px-3 py-2">Evento</th>
                    <th className="px-3 py-2">Stato</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.eventi || []).map((ev) => (
                    <tr key={ev.eventId} className="border-t border-slate-100">
                      <td className="px-3 py-2 whitespace-nowrap text-slate-600">
                        {formatDateIt(ev.date, { short: true })}
                      </td>
                      <td className="px-3 py-2 text-navy-700">{ev.titolo}</td>
                      <td className="px-3 py-2">{statoBadge(ev.stato)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
