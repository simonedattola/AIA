import { useRef, useState } from "react";
import { Upload, FileSpreadsheet, Loader2, Download, AlertCircle, CheckCircle2 } from "lucide-react";
import { adminImportDesignationsFile, adminDesignationsImportTemplate } from "../../lib/api";
import { AdminFormModal } from "./admin-ui";
import { Button } from "@/design-system";

function formatImportResult(res) {
  if (!res?.ok) return res?.error || "Import non riuscito.";
  const parts = [
    res.dryRun
      ? `Anteprima: ${res.parsed} designazioni riconosciute`
      : `${res.inserted} nuove designazioni`,
  ];
  if (!res.dryRun && res.updated) parts.push(`${res.updated} già presenti (aggiornate, non duplicate)`);
  if (res.skippedDuplicates) parts.push(`${res.skippedDuplicates} già in archivio`);
  if (res.membersCreated) parts.push(`${res.membersCreated} nuovi associati`);
  if (res.fileType) parts.push(`file ${res.fileType}`);
  return `${parts.join(" · ")}.`;
}

export default function DesignationFileImport({ onImported }) {
  const inputRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const reset = () => {
    setFile(null);
    setPreview(null);
    setMsg("");
    setError("");
    if (inputRef.current) inputRef.current.value = "";
  };

  const close = () => {
    setOpen(false);
    reset();
  };

  const downloadTemplate = async () => {
    try {
      const blob = await adminDesignationsImportTemplate();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "designazioni_modello.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Impossibile scaricare il modello.");
    }
  };

  const runImport = async (dryRun) => {
    if (!file) return setError("Seleziona un file.");
    setImporting(true);
    setError("");
    setMsg("");
    try {
      const res = await adminImportDesignationsFile(file, { dryRun });
      if (dryRun) {
        setPreview(res);
        setMsg(formatImportResult(res));
      } else {
        setMsg(formatImportResult(res));
        setPreview(null);
        onImported?.(res);
        setTimeout(close, 1500);
      }
    } catch (e) {
      setError(e?.response?.data?.detail || "Import fallito.");
      setPreview(null);
    } finally {
      setImporting(false);
    }
  };

  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={() => setOpen(true)}
        data-testid="admin-designations-import-file"
      >
        <Upload className="h-4 w-4" /> Importa da file
      </Button>

      {open && (
        <AdminFormModal
          open
          title="Importa designazioni da file"
          onClose={close}
          hideFooter
          testid="admin-designations-import-modal"
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4 text-sm text-slate-700">
            <p>
              Carica il file interno della sezione: il sistema riconosce automaticamente tabelle e colonne
              (anche con ordine diverso), estrae le designazioni e le pubblica senza creare duplicati.
            </p>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" size="sm" onClick={downloadTemplate}>
                <Download className="h-4 w-4" /> Scarica esempio CSV
              </Button>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 space-y-1">
              <p className="font-medium text-slate-700">Formati accettati</p>
              <p>CSV, Excel (.xlsx), PDF con tabella, Word (.docx) con tabella.</p>
              <p>
                Servono almeno <strong>data</strong>, <strong>gara</strong> (o squadre casa/ospite), <strong>ruolo</strong> e <strong>nominativo</strong>.
                Le colonne possono chiamarsi in modi diversi e stare in qualsiasi ordine.
              </p>
              <p>Le designazioni già presenti vengono aggiornate, non duplicate.</p>
            </div>

            <label className="block">
              <span className="block font-medium text-slate-700 mb-1.5">File</span>
              <input
                ref={inputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  setPreview(null);
                  setMsg("");
                  setError("");
                }}
                className="block w-full text-sm"
                data-testid="designations-import-input"
              />
            </label>

            {error && (
              <p className="flex items-start gap-2 text-red-600" data-testid="designations-import-error">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" /> {error}
              </p>
            )}
            {msg && (
              <p className="flex items-start gap-2 text-navy-700 font-medium" data-testid="designations-import-msg">
                {preview?.dryRun ? (
                  <FileSpreadsheet className="h-4 w-4 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
                )}
                {msg}
              </p>
            )}

            {preview?.columnMaps?.length > 0 && (
              <p className="text-xs text-slate-500">
                Colonne riconosciute automaticamente dal file.
              </p>
            )}

            {preview?.preview?.length > 0 && (
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase">
                    <tr>
                      <th className="px-2 py-2 text-left">Data</th>
                      <th className="px-2 py-2 text-left">Gara</th>
                      <th className="px-2 py-2 text-left">Ruolo</th>
                      <th className="px-2 py-2 text-left">Nominativo</th>
                      <th className="px-2 py-2 text-left">Anagrafica</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview.map((row, i) => (
                      <tr key={i} className="border-t border-slate-100">
                        <td className="px-2 py-1.5 whitespace-nowrap">{row.matchDate}</td>
                        <td className="px-2 py-1.5">{row.matchLabel}</td>
                        <td className="px-2 py-1.5">{row.role}</td>
                        <td className="px-2 py-1.5">{row.memberName}</td>
                        <td className="px-2 py-1.5">
                          {row.linked ? (
                            <span className="text-emerald-700">Collegato</span>
                          ) : row.wouldCreate ? (
                            <span className="text-amber-700">Nuovo in anagrafica</span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {preview.parsed > preview.preview.length && (
                  <p className="px-2 py-1.5 text-xs text-slate-500 border-t border-slate-100">
                    … e altre {preview.parsed - preview.preview.length} righe
                  </p>
                )}
              </div>
            )}

            {preview?.warnings?.length > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 max-h-32 overflow-y-auto">
                {preview.warnings.map((w, i) => (
                  <p key={i}>{w}</p>
                ))}
              </div>
            )}

            <div className="flex flex-wrap justify-end gap-2 pt-2 border-t border-slate-200">
              <Button type="button" variant="outline" onClick={close} disabled={importing}>
                Annulla
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => runImport(true)}
                disabled={importing || !file}
                data-testid="designations-import-preview"
              >
                {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
                Anteprima
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={() => runImport(false)}
                disabled={importing || !file}
                data-testid="designations-import-confirm"
              >
                {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                Importa e pubblica
              </Button>
            </div>
          </div>
        </AdminFormModal>
      )}
    </>
  );
}
