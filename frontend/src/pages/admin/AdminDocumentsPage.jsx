import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  adminDocuments,
  adminCreateDocument,
  adminUpdateDocument,
  adminDeleteDocument,
  adminUploadAttachment,
  adminDocumentSections,
  adminAddDocumentSection,
} from "../../lib/api";
import { formatFileSize } from "../../lib/format";
import { mediaUrl } from "../../lib/media";
import { DEFAULT_DOCUMENT_SECTIONS } from "../../lib/documents";
import { Plus, Pencil, Trash2, Upload } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import {
  AdminPageHeader,
  AdminTableWrap,
  AdminMobileList,
  AdminDesktopOnly,
  adminTableHead,
  AdminField,
  adminInputCls,
  AdminEmptyState,
  AdminBadge,
  AdminFormModal,
} from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const empty = (sections) => ({
  title: "",
  description: "",
  fileUrl: "",
  fileSize: "",
  category: sections[3] || DEFAULT_DOCUMENT_SECTIONS[3],
  sortOrder: 0,
});

function DocumentEditForm({
  editing,
  setEditing,
  sections,
  newSection,
  setNewSection,
  addingSection,
  onAddSection,
  uploading,
  onFile,
}) {
  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AdminField label="Titolo*">
          <input value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} className={adminInputCls} />
        </AdminField>
        <AdminField label="Sezione">
          <select value={editing.category} onChange={(e) => setEditing({ ...editing, category: e.target.value })} className={adminInputCls}>
            {sections.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
            {editing.category && !sections.includes(editing.category) && (
              <option value={editing.category}>{editing.category}</option>
            )}
          </select>
          <div className="mt-2 flex gap-2">
            <input
              value={newSection}
              onChange={(e) => setNewSection(e.target.value)}
              placeholder="Oppure nuova sezione…"
              className={`${adminInputCls} text-sm`}
            />
            <Button type="button" onClick={onAddSection} disabled={addingSection} variant="outline" size="sm" className="text-sm shrink-0 px-3">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </AdminField>
        <AdminField label="URL file*">
          <input value={editing.fileUrl} onChange={(e) => setEditing({ ...editing, fileUrl: e.target.value })} className={adminInputCls} placeholder="https://..." />
        </AdminField>
        <AdminField label="Carica file">
          <input
            type="file"
            className="hidden"
            id="admin-document-file"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.jpg,.jpeg,.png,.webp,.gif"
            onChange={onFile}
            disabled={uploading}
          />
          <label htmlFor="admin-document-file" className="cursor-pointer block">
            <Button type="button" variant="outline" size="sm" className="text-sm w-full justify-center pointer-events-none" tabIndex={-1}>
              <Upload className="h-4 w-4" /> {uploading ? "Caricamento…" : "Scegli file"}
            </Button>
          </label>
        </AdminField>
        <AdminField label="Dimensione">
          <input
            readOnly
            value={editing.fileSize}
            className={`${adminInputCls} bg-slate-50 text-slate-600`}
            placeholder="Compilata automaticamente al caricamento"
          />
        </AdminField>
      </div>
      <AdminField label="Descrizione">
        <textarea rows={2} value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} className={adminInputCls} />
      </AdminField>
    </div>
  );
}

export default function AdminDocumentsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [sections, setSections] = useState(DEFAULT_DOCUMENT_SECTIONS);
  const [editing, setEditing] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newSection, setNewSection] = useState("");
  const [addingSection, setAddingSection] = useState(false);

  const loadSections = () =>
    adminDocumentSections()
      .then((list) => setSections(list?.length ? list : DEFAULT_DOCUMENT_SECTIONS))
      .catch(() => setSections(DEFAULT_DOCUMENT_SECTIONS));

  const load = () => adminDocuments().then(setItems);
  useEffect(() => {
    load();
    loadSections();
  }, []);

  useEffect(() => {
    if (searchParams.get("new") === "1" && sections.length) {
      setEditing(empty(sections));
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, sections]);

  const closeEdit = () => setEditing(null);

  const addSection = async () => {
    const name = newSection.trim();
    if (!name) return;
    setAddingSection(true);
    try {
      const updated = await adminAddDocumentSection(name);
      setSections(updated);
      if (editing) setEditing({ ...editing, category: name });
      setNewSection("");
    } catch (err) {
      alert(err?.response?.data?.detail || "Impossibile aggiungere la sezione");
    } finally {
      setAddingSection(false);
    }
  };

  const save = async () => {
    if (!editing?.title || !editing?.fileUrl) return alert("Titolo e file obbligatori");
    setSaving(true);
    try {
      if (editing.id) await adminUpdateDocument(editing.id, editing);
      else await adminCreateDocument(editing);
      setEditing(null);
      load();
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id, title) => {
    if (!window.confirm(`Eliminare «${title}»?`)) return;
    await adminDeleteDocument(id);
    if (editing?.id === id) setEditing(null);
    load();
  };

  const onFile = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setUploading(true);
    try {
      const res = await adminUploadAttachment(f);
      const bytes = res.fileSize ?? f.size;
      setEditing((prev) => ({
        ...prev,
        fileUrl: res.fileUrl || res.url || "",
        fileSize: formatFileSize(bytes),
      }));
    } catch (err) {
      alert(err?.response?.data?.detail || "Caricamento file non riuscito");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const formProps = {
    editing,
    setEditing,
    sections,
    newSection,
    setNewSection,
    addingSection,
    onAddSection: addSection,
    uploading,
    onFile,
  };

  return (
    <div data-testid="admin-documents">
      <AdminPageHeader
        title="Documenti"
        description="PDF e file scaricabili dall'area associati."
      >
        <Button type="button" onClick={() => setEditing(empty(sections))} variant="primary">
          <Plus className="h-4 w-4" /> Nuovo documento
        </Button>
      </AdminPageHeader>

      {editing && (
        <AdminFormModal
          open
          title={editing.id ? "Modifica documento" : "Nuovo documento"}
          onClose={closeEdit}
          onSave={save}
          saving={saving || uploading}
          testid="admin-document-modal"
        >
          <DocumentEditForm {...formProps} />
        </AdminFormModal>
      )}

      <AdminTableWrap>
        {items.length === 0 ? (
          <AdminEmptyState icon={SITE_ICONS.documents} title="Nessun documento." />
        ) : (
          <>
            <AdminMobileList>
              {items.map((d) => (
                <li key={d.id} className="p-4" data-testid={`document-row-${d.id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-navy-700 break-words">{d.title}</div>
                      <div className="mt-1.5">
                        <AdminBadge variant="info">{d.category}</AdminBadge>
                      </div>
                      <a
                        href={mediaUrl(d.fileUrl)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 block text-xs text-slate-500 hover:text-navy-600 break-all"
                      >
                        {d.fileUrl}
                      </a>
                    </div>
                    <div className="flex shrink-0">
                      <button
                        type="button"
                        onClick={() => setEditing(d)}
                        className="p-2 rounded text-navy-600 hover:bg-navy-50"
                        title="Modifica"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => remove(d.id, d.title)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </AdminMobileList>

            <AdminDesktopOnly>
              <table className="w-full table-fixed text-sm">
                <thead>
                  <tr className={adminTableHead}>
                    <th className="px-4 py-3 w-[32%]">Titolo</th>
                    <th className="px-4 py-3 w-[18%]">Sezione</th>
                    <th className="px-4 py-3 w-[36%]">File</th>
                    <th className="px-4 py-3 w-[14%] text-right">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((d) => (
                    <tr
                      key={d.id}
                      className="border-t border-slate-100 hover:bg-slate-50/80"
                      data-testid={`document-row-desktop-${d.id}`}
                    >
                      <td className="px-4 py-3 font-medium text-navy-700 min-w-0">
                        <div className="truncate">{d.title}</div>
                      </td>
                      <td className="px-4 py-3 min-w-0">
                        <AdminBadge variant="info">{d.category}</AdminBadge>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 min-w-0">
                        <a
                          href={mediaUrl(d.fileUrl)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-navy-600 truncate block"
                        >
                          {d.fileUrl}
                        </a>
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => setEditing(d)}
                          className="p-2 rounded text-navy-600 hover:bg-navy-50"
                          title="Modifica"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => remove(d.id, d.title)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded ml-1"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </AdminDesktopOnly>
          </>
        )}
      </AdminTableWrap>
    </div>
  );
}
