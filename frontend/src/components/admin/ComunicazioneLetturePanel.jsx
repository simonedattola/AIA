import { useCallback, useEffect, useState } from "react";
import { adminComunicazioneLetture } from "../../lib/api";
import { formatDateTimeIt } from "../../lib/format";
import { CheckCircle2, Eye } from "lucide-react";
import { AdminEmptyState } from "./admin-ui";

export default function ComunicazioneLetturePanel({ comunicazioneId }) {
  const [lettori, setLettori] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    if (!comunicazioneId) return;
    setLoading(true);
    setError("");
    adminComunicazioneLetture(comunicazioneId)
      .then((res) => {
        const visti = (res.associati || []).filter((r) => r.visto);
        setLettori(visti);
        setStats({ viste: res.viste ?? 0, totale: res.totale ?? 0 });
      })
      .catch(() => {
        setLettori([]);
        setStats(null);
        setError("Impossibile caricare il registro letture");
      })
      .finally(() => setLoading(false));
  }, [comunicazioneId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!comunicazioneId) return null;

  return (
    <div className="mt-4 border-t pt-4" data-testid="comunicazione-letture-panel">
      <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-2">
        <Eye className="h-4 w-4" />
        Chi ha letto
      </h4>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
      {!error && stats && (
        <p className="text-sm text-slate-600 mb-3">
          {stats.viste}/{stats.totale} associati hanno aperto la comunicazione.
        </p>
      )}
      {loading ? (
        <p className="text-sm text-slate-500">Caricamento…</p>
      ) : error ? null : lettori.length === 0 ? (
        <AdminEmptyState icon={Eye} title="Nessuno ha ancora aperto questa comunicazione." />
      ) : (
        <ul className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden bg-white">
          {lettori.map((r) => (
            <li
              key={r.memberId}
              className="flex items-center gap-3 px-4 py-2.5 text-sm"
              data-testid={`lettura-row-${r.memberId}`}
            >
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              <span className="font-medium text-navy-700 flex-1 min-w-0 truncate" title={r.nome}>
                {r.nome}
              </span>
              {r.readAt && (
                <span className="text-xs text-slate-500 shrink-0">
                  {formatDateTimeIt(r.readAt)}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
