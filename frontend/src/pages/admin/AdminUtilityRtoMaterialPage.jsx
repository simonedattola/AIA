import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { adminUtilityEvent, adminUpdateUtilityEventMaterial } from "../../lib/api";
import { formatDateIt } from "../../lib/format";
import { AttachmentEditor } from "../../components/admin/AttachmentEditor";
import { AdminPageHeader } from "../../components/admin/admin-ui";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { ArrowLeft, Calendar, FolderOpen } from "lucide-react";

const FILE_ACCEPT = ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.jpg,.jpeg,.png,.webp,.gif,.mp4,.webm,.mov";

export default function AdminUtilityRtoMaterialPage() {
  const { eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [material, setMaterial] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    if (!eventId) return;
    setLoading(true);
    setError("");
    adminUtilityEvent(eventId)
      .then((res) => {
        setEvent(res);
        setMaterial(res.utilityMaterial || []);
      })
      .catch((err) => {
        setError(err?.response?.data?.detail || "Impossibile caricare l'evento");
        setEvent(null);
      })
      .finally(() => setLoading(false));
  }, [eventId]);

  useEffect(() => {
    load();
  }, [load]);

  const persistMaterial = async (next) => {
    setMaterial(next);
    setSaving(true);
    setError("");
    try {
      const res = await adminUpdateUtilityEventMaterial(eventId, next);
      setMaterial(res.utilityMaterial || next);
    } catch (err) {
      setError(err?.response?.data?.detail || "Salvataggio non riuscito");
      load();
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="text-sm text-slate-500">Caricamento…</p>;
  }

  if (!event) {
    return (
      <div>
        <p className="text-sm text-red-600 mb-4">{error || "Evento non trovato."}</p>
        <Link to={R.utility} className="text-sm text-navy-600 hover:underline inline-flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Torna a Utility
        </Link>
      </div>
    );
  }

  return (
    <div data-testid="admin-utility-rto-material-page">
      <Link
        to={R.utility}
        className="inline-flex items-center gap-1 text-sm text-navy-600 hover:underline mb-4"
      >
        <ArrowLeft className="h-4 w-4" /> Utility
      </Link>

      <AdminPageHeader
        title={event.titolo}
        description={
          <>
            <Calendar className="inline h-4 w-4 -mt-0.5 mr-1" />
            {formatDateIt(event.date, { short: true })}
            {event.tipo ? ` · ${event.tipo}` : ""}
            {event.descrizione ? ` · ${event.descrizione}` : ""}
          </>
        }
      />

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      {saving && <p className="text-sm text-slate-500 mb-4">Salvataggio…</p>}

      <div className="bg-white rounded-lg border border-slate-200 p-6 max-w-3xl">
        <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-4">
          <FolderOpen className="h-4 w-4" />
          Materiale evento ({material.length} file)
        </h2>
        <AttachmentEditor
          value={material}
          onChange={persistMaterial}
          label="Allegati"
          accept={FILE_ACCEPT}
          hint="PDF, Office, immagini, ZIP (max 10 MB). Video MP4/WebM/MOV (max 50 MB)."
        />
        {material.length === 0 && (
          <p className="text-sm text-slate-500">Nessun file caricato. Usa «Aggiungi file» per inserire il materiale.</p>
        )}
      </div>
    </div>
  );
}
