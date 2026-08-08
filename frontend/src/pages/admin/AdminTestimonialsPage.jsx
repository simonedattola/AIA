import { useEffect, useState, useMemo } from "react";
import { adminTestimonials, adminCreateTestimonial, adminUpdateTestimonial, adminDeleteTestimonial, adminUpload } from "../../lib/api";
import { MemberSingleSelect } from "../../components/admin/MemberSelect";
import { Plus, Pencil, Trash2, Upload } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import {
  AdminEmptyState,
  AdminFormModal,
  AdminPageHeader,
  AdminTableWrap,
  AdminMobileList,
  AdminDesktopOnly,
  adminTableHead,
  AdminFilterTabs,
  AdminBadge,
} from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const empty = () => ({ name: "", role: "", quote: "", photoUrl: "", sortOrder: 0, memberId: null, status: "published" });

const cls = "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";
const F = ({ label, children }) => (
  <label className="block mb-4">
    <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
    {children}
  </label>
);

function TestimonialEditForm({ editing, setEditing, onUploadPhoto }) {
  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <F label="Nome*">
          <input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} className={cls} />
        </F>
        <F label="Ruolo/qualifica">
          <input
            value={editing.role}
            onChange={(e) => setEditing({ ...editing, role: e.target.value })}
            className={cls}
            placeholder="Arbitra promossa al nazionale..."
          />
        </F>
        <F label="URL foto">
          <input value={editing.photoUrl} onChange={(e) => setEditing({ ...editing, photoUrl: e.target.value })} className={cls} />
        </F>
        <F label="Ordine">
          <input
            type="number"
            value={editing.sortOrder}
            onChange={(e) => setEditing({ ...editing, sortOrder: Number(e.target.value) })}
            className={cls}
          />
        </F>
      </div>
      <F label="Citazione*">
        <textarea rows={4} value={editing.quote} onChange={(e) => setEditing({ ...editing, quote: e.target.value })} className={cls} />
      </F>
      <MemberSingleSelect
        value={editing.memberId}
        onChange={(memberId) => setEditing({ ...editing, memberId })}
        label="Collega al profilo associato"
      />
      <div className="mt-2">
        <input type="file" accept="image/*" onChange={onUploadPhoto} className="hidden" id="test-photo" />
        <label htmlFor="test-photo" className="cursor-pointer inline-flex">
          <Button type="button" variant="outline" className="pointer-events-none" tabIndex={-1}>
            <Upload className="h-4 w-4" /> Carica foto
          </Button>
        </label>
      </div>
    </div>
  );
}

export default function AdminTestimonialsPage() {
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [filter, setFilter] = useState("all");
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = () => adminTestimonials().then(setItems);
  useEffect(() => { load(); }, []);

  const pendingCount = items.filter((t) => t.status === "pending").length;
  const approvedCount = items.length - pendingCount;
  const filtered = useMemo(() => {
    if (filter === "pending") return items.filter((t) => t.status === "pending");
    if (filter === "approved") return items.filter((t) => t.status !== "pending");
    return items;
  }, [items, filter]);

  const closeEdit = () => setEditing(null);

  const save = async () => {
    if (!editing?.name || !editing?.quote) return alert("Nome e citazione obbligatori");
    setSaving(true);
    try {
      const payload = { ...editing, status: editing.status || "published" };
      if (editing.id) await adminUpdateTestimonial(editing.id, payload);
      else await adminCreateTestimonial(payload);
      setEditing(null);
      load();
    } finally {
      setSaving(false);
    }
  };

  const approve = async (t) => {
    await adminUpdateTestimonial(t.id, { ...t, status: "published" });
    load();
  };

  const remove = async (id, name) => {
    if (!window.confirm(`Eliminare la testimonianza di ${name}?`)) return;
    await adminDeleteTestimonial(id);
    if (editing?.id === id) setEditing(null);
    load();
  };

  const uploadPhoto = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setUploading(true);
    try {
      const res = await adminUpload(f);
      setEditing((prev) => ({ ...prev, photoUrl: res.url }));
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div data-testid="admin-testimonials">
      <AdminPageHeader
        title="Testimonianze"
        description="Citazioni sul sito e proposte dagli associati. Quelle in attesa di approvazione sono evidenziate in oro."
      >
        <Button type="button" onClick={() => setEditing(empty())} variant="primary">
          <Plus className="h-4 w-4" /> Nuova testimonianza
        </Button>
      </AdminPageHeader>

      {editing && (
        <AdminFormModal
          open
          title={editing.id ? "Modifica testimonianza" : "Nuova testimonianza"}
          onClose={closeEdit}
          onSave={save}
          saving={saving || uploading}
          testid="admin-testimonial-modal"
        >
          <TestimonialEditForm editing={editing} setEditing={setEditing} onUploadPhoto={uploadPhoto} />
        </AdminFormModal>
      )}

      <AdminTableWrap>
        <div className="p-4 border-b border-slate-200">
          <AdminFilterTabs
            active={filter}
            onChange={setFilter}
            tabs={[
              { id: "all", label: "Tutti", count: items.length },
              { id: "pending", label: "In attesa di approvazione", count: pendingCount },
              { id: "approved", label: "Approvate", count: approvedCount },
            ]}
          />
        </div>

        {filtered.length === 0 ? (
          <AdminEmptyState icon={SITE_ICONS.testimonials} title="Nessuna testimonianza in questa vista." />
        ) : (
          <>
            <AdminMobileList>
              {filtered.map((t) => (
                <li
                  key={t.id}
                  className={`p-4 ${t.status === "pending" ? "bg-gold-50/30" : ""}`}
                  data-testid={`testimonial-${t.id}`}
                >
                  <div className="flex items-start gap-3">
                    {t.photoUrl ? (
                      <img
                        src={t.photoUrl}
                        alt=""
                        className="w-10 h-10 rounded-full object-cover border border-slate-200 shrink-0"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-navy-100 text-navy-600 flex items-center justify-center text-sm font-bold shrink-0">
                        {t.name?.[0]}
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-navy-700 break-words">{t.name}</div>
                      {t.role && <div className="text-sm text-slate-600 mt-0.5 break-words">{t.role}</div>}
                      <p className="text-sm text-slate-600 italic mt-1.5 line-clamp-3 break-words">{t.quote}</p>
                      <div className="mt-2">
                        {t.status === "pending" ? (
                          <AdminBadge variant="warning">In attesa</AdminBadge>
                        ) : (
                          <AdminBadge variant="success">Approvata</AdminBadge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col shrink-0 gap-1 items-end">
                      {t.status === "pending" && (
                        <Button
                          type="button"
                          onClick={() => approve(t)}
                          variant="primary"
                          size="sm"
                          className="text-xs py-1 px-2.5"
                        >
                          Approva
                        </Button>
                      )}
                      <div className="flex">
                        <button
                          type="button"
                          onClick={() => setEditing(t)}
                          className="p-2 rounded text-navy-600 hover:bg-navy-50"
                          title="Modifica"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => remove(t.id, t.name)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </AdminMobileList>

            <AdminDesktopOnly>
              <table className="w-full table-fixed text-sm">
                <thead>
                  <tr className={adminTableHead}>
                    <th className="px-4 py-3 w-[22%]">Nome</th>
                    <th className="px-4 py-3 w-[16%]">Ruolo</th>
                    <th className="px-4 py-3 w-[34%]">Citazione</th>
                    <th className="px-4 py-3 w-[12%]">Stato</th>
                    <th className="px-4 py-3 w-[16%] text-right">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((t) => (
                    <tr
                      key={t.id}
                      className={`border-t border-slate-100 ${
                        t.status === "pending" ? "bg-gold-50/30 hover:bg-gold-50/50" : "hover:bg-slate-50/80"
                      }`}
                      data-testid={`testimonial-desktop-${t.id}`}
                    >
                      <td className="px-4 py-3.5 min-w-0">
                        <div className="flex items-center gap-3 min-w-0">
                          {t.photoUrl ? (
                            <img
                              src={t.photoUrl}
                              alt=""
                              className="w-10 h-10 rounded-full object-cover border border-slate-200 shrink-0"
                            />
                          ) : (
                            <div className="w-10 h-10 rounded-full bg-navy-100 text-navy-600 flex items-center justify-center text-sm font-bold shrink-0">
                              {t.name?.[0]}
                            </div>
                          )}
                          <div className="font-medium text-navy-700 truncate">{t.name}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3.5 text-slate-600 min-w-0">
                        <div className="truncate">{t.role || "—"}</div>
                      </td>
                      <td className="px-4 py-3.5 text-slate-600 italic min-w-0">
                        <span className="line-clamp-2 break-words">{t.quote}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        {t.status === "pending" ? (
                          <AdminBadge variant="warning">In attesa</AdminBadge>
                        ) : (
                          <AdminBadge variant="success">Approvata</AdminBadge>
                        )}
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1 justify-end">
                          {t.status === "pending" && (
                            <Button
                              type="button"
                              onClick={() => approve(t)}
                              variant="primary"
                              size="sm"
                              className="text-xs py-1 px-2.5"
                            >
                              Approva
                            </Button>
                          )}
                          <button
                            type="button"
                            onClick={() => setEditing(t)}
                            className="p-2 rounded text-navy-600 hover:bg-navy-50"
                            title="Modifica"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => remove(t.id, t.name)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
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
