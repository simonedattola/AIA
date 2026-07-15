import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  adminUtility,
  adminUpdateUtilityPolo,
  adminCreateUtilityItem,
  adminUpdateUtilityItem,
  adminDeleteUtilityItem,
  adminEvents,
} from "../../lib/api";
import { formatDateIt } from "../../lib/format";
import { UTILITY_SECTIONS } from "../../lib/utility";
import RichTextEditor from "./RichTextEditor";
import { Plus, Pencil, Trash2, FolderOpen, Calendar } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import {
  AdminEmptyState,
  AdminFormModal,
  AdminPageHeader,
  AdminTableWrap,
  adminTableHead,
  AdminFilterTabs,
  AdminField,
  adminInputCls,
} from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const TABS = [
  { id: "materiale_eventi", label: UTILITY_SECTIONS.materiale_eventi },
  { id: "polo", label: UTILITY_SECTIONS.polo },
  { id: "link_utili", label: UTILITY_SECTIONS.link_utili },
];

const emptyItem = () => ({
  title: "",
  description: "",
  url: "",
  fileUrl: "",
  section: "link_utili",
  sortOrder: 0,
});

function ItemEditForm({ editing, setEditing }) {
  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AdminField label="Titolo*">
          <input
            value={editing.title}
            onChange={(e) => setEditing({ ...editing, title: e.target.value })}
            className={adminInputCls}
          />
        </AdminField>
        <AdminField label="Ordine">
          <input
            type="number"
            value={editing.sortOrder}
            onChange={(e) => setEditing({ ...editing, sortOrder: Number(e.target.value) })}
            className={adminInputCls}
          />
        </AdminField>
        <AdminField label="URL*">
          <input
            value={editing.url}
            onChange={(e) => setEditing({ ...editing, url: e.target.value })}
            className={adminInputCls}
            placeholder="https://..."
          />
        </AdminField>
      </div>
      <AdminField label="Descrizione">
        <textarea
          rows={2}
          value={editing.description}
          onChange={(e) => setEditing({ ...editing, description: e.target.value })}
          className={adminInputCls}
        />
      </AdminField>
    </div>
  );
}

export default function AdminUtilityPage() {
  const [polo, setPolo] = useState({ bodyHtml: "" });
  const [items, setItems] = useState([]);
  const [events, setEvents] = useState([]);
  const [tab, setTab] = useState("materiale_eventi");
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);
  const [poloSaving, setPoloSaving] = useState(false);

  const load = () => {
    adminUtility().then((res) => {
      setPolo(res.polo || { bodyHtml: "" });
      setItems((res.items || []).filter((i) => i.section === "link_utili"));
    });
    adminEvents().then((list) => setEvents(list || []));
  };

  useEffect(() => { load(); }, []);

  const linkItems = useMemo(
    () => [...items].sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0)),
    [items]
  );

  const saveItem = async () => {
    if (!editing?.title?.trim()) return alert("Titolo obbligatorio");
    if (!editing.url?.trim()) return alert("URL obbligatorio");
    setSaving(true);
    try {
      const payload = { ...editing, section: "link_utili", fileUrl: "" };
      if (editing.id) await adminUpdateUtilityItem(editing.id, payload);
      else await adminCreateUtilityItem(payload);
      setEditing(null);
      load();
    } finally {
      setSaving(false);
    }
  };

  const removeItem = async (id, title) => {
    if (!window.confirm(`Eliminare "${title}"?`)) return;
    await adminDeleteUtilityItem(id);
    load();
  };

  const savePolo = async () => {
    setPoloSaving(true);
    try {
      await adminUpdateUtilityPolo({ bodyHtml: polo.bodyHtml || "" });
      load();
    } finally {
      setPoloSaving(false);
    }
  };

  return (
    <div data-testid="admin-utility-page">
      <AdminPageHeader
        title="Utility"
        description="Materiale allegato agli eventi, testo polo e link utili per gli associati."
      />

      <AdminFilterTabs tabs={TABS} active={tab} onChange={setTab} />

      <div className="mt-6">
      {tab === "materiale_eventi" && (
        <div>
          <AdminTableWrap>
            <table className="w-full min-w-[720px]">
              <thead>
                <tr className={adminTableHead}>
                  <th className="px-4 py-3 text-left">Data</th>
                  <th className="px-4 py-3 text-left">Evento</th>
                  <th className="px-4 py-3 text-left">Tipo</th>
                  <th className="px-4 py-3 text-left">Materiale</th>
                  <th className="px-4 py-3 text-right">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => (
                  <tr key={ev.id} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3 text-sm text-slate-600 whitespace-nowrap">
                      {formatDateIt(ev.date, { short: true })}
                    </td>
                    <td className="px-4 py-3 font-medium text-navy-700">{ev.titolo}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{ev.tipo || "—"}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {(ev.utilityMaterial || []).length} file
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        to={R.utilityEvento(ev.id)}
                        className="text-sm text-navy-600 hover:underline inline-flex items-center gap-1"
                      >
                        <FolderOpen className="h-4 w-4" /> Gestisci
                      </Link>
                    </td>
                  </tr>
                ))}
                {events.length === 0 && (
                  <tr>
                    <td colSpan={5} className="p-4">
                      <AdminEmptyState icon={SITE_ICONS.events} title="Nessun evento in calendario. Creane uno da Eventi." />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </AdminTableWrap>
        </div>
      )}

      {tab === "polo" && (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <AdminField label="Contenuto">
            <RichTextEditor
              value={polo.bodyHtml || ""}
              onChange={(html) => setPolo({ bodyHtml: html })}
            />
          </AdminField>
          <Button type="button" onClick={savePolo} disabled={poloSaving} variant="primary">
            {poloSaving ? "Salvataggio…" : "Salva informazioni polo"}
          </Button>
        </div>
      )}

      {tab === "link_utili" && (
        <>
          <div className="flex justify-end mb-4">
            <Button onClick={() => setEditing(emptyItem())} variant="primary">
              <Plus className="h-4 w-4" /> Aggiungi link
            </Button>
          </div>
          <AdminTableWrap>
            <table className="w-full min-w-[640px]">
              <thead>
                <tr className={adminTableHead}>
                  <th className="px-4 py-3 text-left">Titolo</th>
                  <th className="px-4 py-3 text-left">URL</th>
                  <th className="px-4 py-3 text-left">Ordine</th>
                  <th className="px-4 py-3 text-right">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {linkItems.map((item) => (
                  <tr key={item.id} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-navy-700">{item.title}</td>
                    <td className="px-4 py-3 text-sm text-slate-600 truncate max-w-xs">{item.url || "—"}</td>
                    <td className="px-4 py-3 text-sm">{item.sortOrder ?? 0}</td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => setEditing({ ...item })}
                        className="p-1.5 rounded text-navy-600 hover:bg-navy-50"
                        title="Modifica"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => removeItem(item.id, item.title)}
                        className="p-1.5 text-red-600 hover:bg-red-50 rounded ml-1"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
                {linkItems.length === 0 && (
                  <tr>
                    <td colSpan={4} className="p-4">
                      <AdminEmptyState icon={SITE_ICONS.utility} title="Nessun link in questa sezione." />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </AdminTableWrap>
        </>
      )}

      {editing && tab === "link_utili" && (
        <AdminFormModal
          open
          title={editing.id ? "Modifica link" : "Nuovo link"}
          onClose={() => setEditing(null)}
          onSave={saveItem}
          saving={saving}
        >
          <ItemEditForm editing={editing} setEditing={setEditing} />
        </AdminFormModal>
      )}
      </div>
    </div>
  );
}
