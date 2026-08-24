import { useRef, useState } from "react";
import { Upload, FileSpreadsheet, Loader2, Download, AlertCircle, CheckCircle2 } from "lucide-react";
import { adminImportMembersFile, adminMembersImportTemplate } from "../../lib/api";
import { AdminFormModal } from "./admin-ui";
import { Button } from "@/design-system";
import { memberRoleLabel } from "../../lib/memberRoles";

function formatImportResult(res) {
  if (!res?.ok) return res?.error || "Import non riuscito.";
  const parts = [
    res.dryRun
      ? `Anteprima: ${res.parsed} associati riconosciuti`
      : `${res.inserted} nuovi profili`,
  ];
  if (!res.dryRun && res.updated) parts.push(`${res.updated} già presenti (aggiornati)`);
  if (res.skippedDuplicates) parts.push(`${res.skippedDuplicates} già in anagrafica`);
  if (res.removeMissing && res.removed) {
    parts.push(
      res.dryRun
        ? `${res.removed} da eliminare (assenti dal file)`
        : `${res.removed} eliminati (assenti dal file)`
    );
  }
  if (res.fileType) parts.push(`file ${res.fileType}`);
  return `${parts.join(" · ")}.`;
}

export default function MemberFileImport({ onImported }) {
  const inputRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [removeMissing, setRemoveMissing] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const reset = () => {
    setFile(null);
    setPreview(null);
    setMsg("");
    setError("");
    setRemoveMissing(false);
    if (inputRef.current) inputRef.current.value = "";
  };

  const close = () => {
    setOpen(false);
    reset();
  };

  const downloadTemplate = async () => {
    try {
      const blob = await adminMembersImportTemplate();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "anagrafica_modello.csv";
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
      const res = await adminImportMembersFile(file, { dryRun, removeMissing });
      if (dryRun) {
        setPreview(res);
        setMsg(formatImportResult(res));
      } else {
        setMsg(formatImportResult(res));
        setPreview(res.removeMissing ? res : null);
        onImported?.(res);
        setTimeout(close, 1800);
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
        data-testid="admin-members-import-file"
      >
        <Upload className="h-4 w-4" /> Importa da file
      </Button>

      {open && (
        <AdminFormModal
          open
          title="Importa anagrafica da file"
          onClose={close}
          hideFooter
          testid="admin-members-import-modal"
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4 text-sm text-slate-700">
            <p>
              Carica l&apos;elenco associati in qualsiasi formato (CSV, Excel, PDF, Word).
              Il sistema riconosce le colonne automaticamente e non crea duplicati.
            </p>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" size="sm" onClick={downloadTemplate}>
                <Download className="h-4 w-4" /> Scarica esempio CSV
              </Button>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 space-y-1">
              <p className="font-medium text-slate-700">Cosa serve</p>
              <p>
                <strong>Obbligatorio:</strong> nome e cognome (oppure una colonna «nominativo»).
              </p>
              <p>Colonne utili: ruolo (AE/AA/AB/AFR/OA/OT), meccanografico, email, telefono, anno inizio, note.</p>
              <p>La categoria massima vale solo per AE e AA; altrimenti resta vuota.</p>
              <p>Profili già presenti (stesso nome, email o meccanografico) vengono aggiornati, non duplicati.</p>
            </div>

            <label className="block">
              <span className="block font-medium text-slate-700 mb-1.5">File</span>
              <input
                ref={inputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  setPreview(null);
                  setMsg("");
                  setError("");
                }}
                className="block w-full text-sm"
                data-testid="members-import-input"
              />
            </label>

            <label className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-950">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={removeMissing}
                onChange={(e) => setRemoveMissing(e.target.checked)}
                data-testid="members-import-remove-missing"
              />
              <span>
                <strong>Elimina chi non è nel file.</strong> Dopo l&apos;import, rimuove
                dall&apos;anagrafica gli associati assenti da questo elenco (usa l&apos;anteprima
                prima di confermare).
              </span>
            </label>

            {error && (
              <p className="flex items-start gap-2 text-red-600" data-testid="members-import-error">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" /> {error}
              </p>
            )}
            {msg && (
              <p className="flex items-start gap-2 text-navy-700 font-medium" data-testid="members-import-msg">
                {preview?.dryRun ? (
                  <FileSpreadsheet className="h-4 w-4 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
                )}
                {msg}
              </p>
            )}

            {preview?.preview?.length > 0 && (
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase">
                    <tr>
                      <th className="px-2 py-2 text-left">Nome</th>
                      <th className="px-2 py-2 text-left">Ruolo</th>
                      <th className="px-2 py-2 text-left">Categoria</th>
                      <th className="px-2 py-2 text-left">Mecc.</th>
                      <th className="px-2 py-2 text-left">Stato</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview.map((row, i) => (
                      <tr key={i} className="border-t border-slate-100">
                        <td className="px-2 py-1.5">{row.firstName} {row.lastName}</td>
                        <td className="px-2 py-1.5">{memberRoleLabel(row)}</td>
                        <td className="px-2 py-1.5">{row.category || "—"}</td>
                        <td className="px-2 py-1.5 font-mono">{row.meccanografico || "—"}</td>
                        <td className="px-2 py-1.5">
                          {row.existing ? (
                            <span className="text-amber-700">Già presente</span>
                          ) : (
                            <span className="text-emerald-700">Nuovo</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {preview.parsed > preview.preview.length && (
                  <p className="px-2 py-1.5 text-xs text-slate-500 border-t border-slate-100">
                    … e altri {preview.parsed - preview.preview.length}
                  </p>
                )}
              </div>
            )}

            {preview?.removedPreview?.length > 0 && (
              <div className="border border-red-200 rounded-lg overflow-hidden">
                <p className="px-2 py-2 text-xs font-semibold uppercase tracking-wide bg-red-50 text-red-800">
                  Da eliminare ({preview.removed})
                </p>
                <ul className="max-h-40 overflow-y-auto text-xs divide-y divide-red-100">
                  {preview.removedPreview.map((row) => (
                    <li key={row.id || row.slug} className="px-2 py-1.5 text-red-900">
                      {row.lastName} {row.firstName}
                      {row.meccanografico ? ` · ${row.meccanografico}` : ""}
                      {row.role ? ` · ${row.role}` : ""}
                    </li>
                  ))}
                </ul>
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
                data-testid="members-import-preview"
              >
                {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
                Anteprima
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={() => runImport(false)}
                disabled={importing || !file}
                data-testid="members-import-confirm"
              >
                {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {removeMissing ? "Importa e elimina assenti" : "Importa"}
              </Button>
            </div>
          </div>
        </AdminFormModal>
      )}
    </>
  );
}
