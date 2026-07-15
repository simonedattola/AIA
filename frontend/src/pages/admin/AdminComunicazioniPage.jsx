import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  adminComunicazioni,
  adminCreaComunicazione,
  adminDeleteComunicazione,
} from "../../lib/api";
import { Plus, Trash2, Users, Eye } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import ComunicazioneLetturePanel from "../../components/admin/ComunicazioneLetturePanel";
import { formatDateIt } from "../../lib/format";
import { AttachmentEditor } from "../../components/admin/AttachmentEditor";
import { MemberMultiSelect } from "../../components/admin/MemberSelect";
import { AttachmentList } from "../../components/AttachmentList";
import { AdminEmptyState, AdminFormModal, AdminPageHeader, adminInputCls } from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const emptyForm = () => ({
  title: "",
  bodyHtml: "",
  allMembers: true,
  memberIds: [],
  allowReplies: true,
  attachments: [],
});

function ComunicazioneForm({ form, setForm }) {
  return (
    <div className="space-y-4">
      <label className="block">
        <span className="block text-sm font-medium text-slate-700 mb-1.5">Titolo *</span>
        <input
          required
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          className={adminInputCls}
        />
      </label>
      <label className="block">
        <span className="block text-sm font-medium text-slate-700 mb-1.5">Testo *</span>
        <textarea
          required
          rows={6}
          value={form.bodyHtml}
          onChange={(e) => setForm({ ...form, bodyHtml: e.target.value })}
          className={adminInputCls}
          placeholder="Puoi usare HTML semplice (&lt;p&gt;, &lt;strong&gt;, …)"
        />
      </label>
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={form.allowReplies}
          onChange={(e) => setForm({ ...form, allowReplies: e.target.checked })}
        />
        <span className="text-sm">Consenti risposte dagli associati</span>
      </label>
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={form.allMembers}
          onChange={(e) => setForm({ ...form, allMembers: e.target.checked })}
        />
        <span className="text-sm flex items-center gap-1">
          <Users className="h-4 w-4" /> Tutti gli associati con profilo
        </span>
      </label>
      {!form.allMembers && (
        <MemberMultiSelect
          value={form.memberIds}
          onChange={(memberIds) => setForm({ ...form, memberIds })}
          label="Destinatari"
          searchOnly
        />
      )}
      <AttachmentEditor
        value={form.attachments}
        onChange={(attachments) => setForm({ ...form, attachments })}
      />
    </div>
  );
}

export default function AdminComunicazioniPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [composing, setComposing] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [msg, setMsg] = useState("");
  const [sending, setSending] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [lettureExpanded, setLettureExpanded] = useState(null);

  const load = () => adminComunicazioni().then(setItems);

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (searchParams.get("new") === "1") {
      setComposing(true);
      setForm(emptyForm());
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const submit = async () => {
    if (!form.title.trim() || !form.bodyHtml.trim()) return alert("Titolo e testo obbligatori");
    setSending(true);
    setMsg("");
    try {
      const res = await adminCreaComunicazione({
        title: form.title,
        bodyHtml: form.bodyHtml,
        allMembers: form.allMembers,
        memberIds: form.allMembers ? [] : form.memberIds,
        allowReplies: form.allowReplies,
        attachments: form.attachments,
      });
      setMsg(`Comunicazione inviata a ${res.destinatari} associati.`);
      setForm(emptyForm());
      setComposing(false);
      load();
    } catch (err) {
      alert(err?.response?.data?.detail || "Errore invio");
    } finally {
      setSending(false);
    }
  };

  const remove = async (id, title) => {
    if (!window.confirm(`Eliminare «${title}»?`)) return;
    await adminDeleteComunicazione(id);
    load();
  };

  return (
    <div>
      <AdminPageHeader
        title="Comunicazioni interne"
        description="Invia avvisi all'area associati. Il registro mostra chi ha aperto ogni comunicazione."
      >
        <Button type="button" onClick={() => { setComposing(true); setMsg(""); }} variant="primary">
          <Plus className="h-4 w-4" /> Nuova comunicazione
        </Button>
      </AdminPageHeader>

      {msg && (
        <p className="text-sm text-navy-700 bg-navy-50 border border-navy-100 p-3 rounded-lg mb-6">{msg}</p>
      )}

      {composing && (
        <AdminFormModal
          open
          title="Nuova comunicazione"
          onClose={() => setComposing(false)}
          onSave={submit}
          saving={sending}
          saveLabel="Invia comunicazione"
          testid="admin-comunicazione-modal"
          maxWidth="max-w-2xl"
        >
          <ComunicazioneForm form={form} setForm={setForm} />
        </AdminFormModal>
      )}

      <h2 className="font-display text-xl font-bold text-navy-700 mb-4">Inviate</h2>
      <div className="space-y-4">
        {items.map((c) => (
          <article key={c.id} className="bg-white rounded-lg border border-slate-200 p-5">
            <div className="flex justify-between gap-4">
              <div>
                <h3 className="font-semibold text-navy-800">{c.title}</h3>
                <p className="text-xs text-slate-500 mt-1">
                  {formatDateIt(c.createdAt?.slice(0, 10))} ·{" "}
                  {c.allMembers ? "Tutti" : `${(c.memberIds || []).length} destinatari`} ·{" "}
                  {c.letteCount ?? 0}/{c.destinatariCount ?? 0} hanno aperto ·{" "}
                  {c.risposteCount || 0} risposte
                </p>
              </div>
              <div className="flex gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => {
                    setLettureExpanded(lettureExpanded === c.id ? null : c.id);
                    if (lettureExpanded !== c.id) setExpanded(null);
                  }}
                  className={`p-2 rounded ${lettureExpanded === c.id ? "bg-navy-100 text-navy-700" : "text-navy-600 hover:bg-navy-50"}`}
                  title="Registro letture"
                  aria-label="Registro letture"
                >
                  <Eye className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setExpanded(expanded === c.id ? null : c.id);
                    if (expanded !== c.id) setLettureExpanded(null);
                  }}
                  className={`p-2 rounded ${expanded === c.id ? "bg-navy-100 text-navy-700" : "text-navy-600 hover:bg-navy-50"}`}
                  title="Contenuto e risposte"
                  aria-label="Contenuto e risposte"
                >
                  <SITE_ICONS.messagesChat className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => remove(c.id, c.title)}
                  className="text-red-600 hover:bg-red-50 p-2 rounded"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
            {lettureExpanded === c.id && (
              <ComunicazioneLetturePanel comunicazioneId={c.id} />
            )}
            {expanded === c.id && (
              <div className="mt-4 border-t pt-4">
                <div
                  className="prose-aia text-sm mb-4"
                  dangerouslySetInnerHTML={{ __html: c.bodyHtml || "" }}
                />
                <AttachmentList attachments={c.attachments} className="mb-4" />
                {(c.risposte || []).length > 0 && (
                  <ul className="space-y-2">
                    <li className="text-xs font-semibold text-slate-500 uppercase">Risposte</li>
                    {(c.risposte || []).map((r) => (
                      <li key={r.id} className="bg-slate-50 rounded p-3 text-sm">
                        <strong>{r.memberName}</strong>
                        <span className="text-xs text-slate-400 ml-2">
                          {formatDateIt(r.createdAt?.slice(0, 10))}
                        </span>
                        <p className="mt-1">{r.testo}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </article>
        ))}
        {items.length === 0 && (
          <AdminEmptyState icon={SITE_ICONS.comunicazioni} title="Nessuna comunicazione inviata." />
        )}
      </div>
    </div>
  );
}
