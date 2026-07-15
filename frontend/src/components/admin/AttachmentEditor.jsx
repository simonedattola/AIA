import { useRef, useState } from "react";
import { Paperclip, Trash2, Loader2 } from "lucide-react";
import { adminUploadAttachment } from "../../lib/api";
import { formatFileSize } from "../../lib/format";

function newId() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

const DEFAULT_ACCEPT = ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.jpg,.jpeg,.png,.webp,.gif";

export function AttachmentEditor({
  value = [],
  onChange,
  label = "Allegati",
  accept = DEFAULT_ACCEPT,
  hint = "PDF, Office, immagini, ZIP (max 10 MB). Video MP4/WebM/MOV (max 50 MB).",
}) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const uploadFiles = async (files) => {
    if (!files.length) return;
    setUploading(true);
    setError("");
    const added = [];
    try {
      for (const file of files) {
        const res = await adminUploadAttachment(file);
        added.push({
          id: res.id || newId(),
          fileName: res.fileName || file.name,
          fileUrl: res.fileUrl || res.url || res.path,
          fileSize: res.fileSize ?? file.size,
          mimeType: res.mimeType || file.type || "",
        });
      }
      onChange([...(value || []), ...added]);
    } catch (err) {
      setError(err?.response?.data?.detail || "Errore caricamento file");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const remove = (id) => onChange((value || []).filter((a) => a.id !== id));

  return (
    <div className="mb-4">
      <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
      {(value || []).length > 0 && (
        <ul className="space-y-2 mb-3">
          {(value || []).map((a) => (
            <li
              key={a.id}
              className="flex items-center gap-2 text-sm bg-slate-50 border border-slate-200 rounded-md px-3 py-2"
            >
              <Paperclip className="h-4 w-4 text-slate-500 shrink-0" />
              <span className="flex-1 truncate">{a.fileName}</span>
              {a.fileSize > 0 && (
                <span className="text-xs text-slate-400 shrink-0">{formatFileSize(a.fileSize)}</span>
              )}
              <button
                type="button"
                onClick={() => remove(a.id)}
                className="p-1 text-red-600 hover:bg-red-50 rounded shrink-0"
                aria-label="Rimuovi allegato"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="flex items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept}
          className="hidden"
          onChange={(e) => uploadFiles(Array.from(e.target.files || []))}
        />
        <button
          type="button"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50"
        >
          {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Paperclip className="h-4 w-4" />}
          {uploading ? "Caricamento…" : "Aggiungi file"}
        </button>
        <span className="text-xs text-slate-500">{hint}</span>
      </div>
      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
    </div>
  );
}
