import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  adminEvents, adminCreateEvent, adminUpdateEvent, adminDeleteEvent,
  adminEventTypes, adminAddEventType,
} from "../../lib/api";
import { formatEventDateTimeIt } from "../../lib/format";
import { AttachmentEditor } from "../../components/admin/AttachmentEditor";
import { MemberMultiSelect } from "../../components/admin/MemberSelect";
import { RoleGroupPicker, roleGroupsSummary } from "../../components/admin/RoleGroupPicker";
import EventPresenzePanel from "../../components/admin/EventPresenzePanel";
import { Plus, Pencil, Trash2, UserCheck, Calendar, Users } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import { AdminEmptyState, AdminFormModal, AdminPageHeader } from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const TIPI_DEFAULT = ["Rto", "Riunione", "Allenamento", "Corso", "Sociale", "Raduno"];

const empty = () => ({
  date: new Date().toISOString().slice(0, 10),
  orario: "09:00",
  orarioFine: "",
  titolo: "",
  descrizione: "",
  luogo: "",
  tipo: "Riunione",
  invitedMemberIds: [],
  invitedRoleGroups: [],
  inviteMode: "all",
  portalOnly: false,
  attachments: [],
});

function normalizeEvent(e) {
  const invitedMemberIds = e.invitedMemberIds || e.relatedMemberIds || [];
  const invitedRoleGroups = e.invitedRoleGroups || [];
  let inviteMode = "all";
  if (invitedRoleGroups.length) inviteMode = "roles";
  else if (invitedMemberIds.length) inviteMode = "manual";
  return {
    ...e,
    date: (e.date || "").slice(0, 10),
    orario: (e.orario || "09:00").slice(0, 5),
    orarioFine: (e.orarioFine || "").slice(0, 5),
    attachments: e.attachments || [],
    invitedMemberIds,
    invitedRoleGroups,
    inviteMode,
    portalOnly: !!e.portalOnly,
  };
}

const inputCls = "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";
const Field = ({ label, hint, children, className = "" }) => (
  <label className={`block ${className}`}>
    <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
    {hint && <span className="block text-xs text-slate-400 mb-1">{hint}</span>}
    {children}
  </label>
);

function EventEditForm({
  editing,
  setEditing,
  activeTab,
  setActiveTab,
  tipi,
  newTipo,
  setNewTipo,
  onAddTipo,
  addingTipo,
}) {
  return (
    <div data-testid="admin-event-form">
      {editing.id && (
        <div className="flex gap-1 mb-6 border-b border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab("details")}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === "details"
                ? "border-navy-600 text-navy-700"
                : "border-transparent text-slate-500 hover:text-navy-600"
            }`}
          >
            Dettagli
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("presenze")}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors inline-flex items-center gap-1.5 ${
              activeTab === "presenze"
                ? "border-navy-600 text-navy-700"
                : "border-transparent text-slate-500 hover:text-navy-600"
            }`}
            data-testid="event-tab-presenze"
          >
            <UserCheck className="h-4 w-4" /> Presenze
          </button>
        </div>
      )}

      {(activeTab === "details" || !editing.id) && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Titolo*">
              <input
                data-testid="event-titolo"
                value={editing.titolo}
                onChange={(e) => setEditing({ ...editing, titolo: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="Data*">
              <input
                data-testid="event-date"
                type="date"
                value={editing.date}
                onChange={(e) => setEditing({ ...editing, date: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="Orario inizio*">
              <input
                data-testid="event-orario"
                type="time"
                value={editing.orario || "09:00"}
                onChange={(e) => setEditing({ ...editing, orario: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="Orario fine" hint="Opzionale. Se vuoto, durata default 2 ore in calendario.">
              <input
                data-testid="event-orario-fine"
                type="time"
                value={editing.orarioFine || ""}
                onChange={(e) => setEditing({ ...editing, orarioFine: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="Luogo">
              <input
                data-testid="event-luogo"
                value={editing.luogo}
                onChange={(e) => setEditing({ ...editing, luogo: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="Tipo" className="md:col-span-2">
              <select
                data-testid="event-tipo"
                value={editing.tipo}
                onChange={(e) => setEditing({ ...editing, tipo: e.target.value })}
                className={inputCls}
              >
                {tipi.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
                {editing.tipo && !tipi.includes(editing.tipo) && (
                  <option value={editing.tipo}>{editing.tipo}</option>
                )}
              </select>
              <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2 mt-2 min-w-0">
                <input
                  data-testid="event-new-tipo"
                  value={newTipo}
                  onChange={(e) => setNewTipo(e.target.value)}
                  placeholder="Nuovo tipo…"
                  className={`${inputCls} flex-1 min-w-0`}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={onAddTipo}
                  disabled={addingTipo || !newTipo.trim()}
                  data-testid="event-add-tipo"
                  className="w-full sm:w-auto shrink-0"
                >
                  {addingTipo ? "Aggiunta…" : "Aggiungi tipo"}
                </Button>
              </div>
              <p className="text-xs text-slate-500 mt-1.5">I tipi restano disponibili per i prossimi eventi.</p>
            </Field>
          </div>

          <Field label="Descrizione">
            <textarea
              data-testid="event-descrizione"
              rows={3}
              value={editing.descrizione}
              onChange={(e) => setEditing({ ...editing, descrizione: e.target.value })}
              className={inputCls}
            />
          </Field>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!editing.portalOnly}
              onChange={(e) => setEditing({ ...editing, portalOnly: !e.target.checked })}
              data-testid="event-public"
            />
            <span className="text-sm flex items-center gap-1">
              Visibile al pubblico
            </span>
          </label>

          <div className="mb-4 space-y-3">
            <span className="block text-sm font-medium text-slate-700">Invitati</span>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="inviteMode"
                checked={editing.inviteMode === "all"}
                onChange={() => setEditing({
                  ...editing,
                  inviteMode: "all",
                  invitedMemberIds: [],
                  invitedRoleGroups: [],
                })}
                data-testid="event-invite-all"
              />
              <span className="text-sm flex items-center gap-1">
                <Users className="h-4 w-4" /> Tutti gli associati con profilo
              </span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="inviteMode"
                checked={editing.inviteMode === "roles"}
                onChange={() => setEditing({
                  ...editing,
                  inviteMode: "roles",
                  invitedMemberIds: [],
                })}
                data-testid="event-invite-roles"
              />
              <span className="text-sm">Filtra per ruolo / qualifica</span>
            </label>
            {editing.inviteMode === "roles" && (
              <RoleGroupPicker
                value={editing.invitedRoleGroups || []}
                onChange={(invitedRoleGroups) => setEditing({ ...editing, invitedRoleGroups })}
                label="Gruppi invitati"
                hint="AE, AA, AB, AFR, OA, OT, CDS, Collaboratori, ORS"
              />
            )}
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="inviteMode"
                checked={editing.inviteMode === "manual"}
                onChange={() => setEditing({
                  ...editing,
                  inviteMode: "manual",
                  invitedRoleGroups: [],
                })}
                data-testid="event-invite-manual"
              />
              <span className="text-sm">Selezione manuale associati</span>
            </label>
            {editing.inviteMode === "manual" && (
              <MemberMultiSelect
                value={editing.invitedMemberIds || []}
                onChange={(invitedMemberIds) => setEditing({ ...editing, invitedMemberIds })}
                label="Associati invitati"
                searchOnly
              />
            )}
          </div>

          <AttachmentEditor
            value={editing.attachments || []}
            onChange={(attachments) => setEditing({ ...editing, attachments })}
            label="Allegati evento"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.jpg,.jpeg,.png,.webp,.gif,.mp4,.webm,.mov"
            hint="Visibili sul calendario e nella scheda evento. PDF, Office, immagini, ZIP (max 10 MB). Video MP4/WebM/MOV (max 50 MB). Il materiale dedicato per Utility si gestisce da Utility → Materiale eventi."
          />
        </div>
      )}

      {editing.id && activeTab === "presenze" && (
        <EventPresenzePanel
          eventId={editing.id}
          invitedCount={
            editing.inviteMode === "manual" ? (editing.invitedMemberIds || []).length : 0
          }
        />
      )}
    </div>
  );
}

export default function AdminEventsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [activeTab, setActiveTab] = useState("details");
  const [saving, setSaving] = useState(false);
  const [tipi, setTipi] = useState(TIPI_DEFAULT);
  const [newTipo, setNewTipo] = useState("");
  const [addingTipo, setAddingTipo] = useState(false);

  const load = () => adminEvents().then(setItems);
  const loadTipi = () => adminEventTypes().then((list) => setTipi(list?.length ? list : TIPI_DEFAULT));

  useEffect(() => {
    load();
    loadTipi();
  }, []);

  const openEdit = (e, tab = "details") => {
    setEditing(normalizeEvent(e));
    setActiveTab(tab);
  };

  useEffect(() => {
    if (searchParams.get("new") === "1") {
      setEditing(empty());
      setActiveTab("details");
      setSearchParams({}, { replace: true });
      return;
    }
    const editId = searchParams.get("edit");
    if (editId && items.length) {
      const ev = items.find((e) => e.id === editId);
      if (ev) {
        openEdit(ev);
        setSearchParams({}, { replace: true });
      }
    }
  }, [searchParams, setSearchParams, items]);

  const closeEdit = () => setEditing(null);

  const addTipo = async () => {
    const name = newTipo.trim();
    if (!name) return;
    setAddingTipo(true);
    try {
      const updated = await adminAddEventType(name);
      setTipi(updated);
      const normalized = name.trim().replace(/\s+/g, " ");
      const tipo =
        updated.find((t) => t.toLowerCase() === normalized.toLowerCase())
        || (normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase());
      setEditing((prev) => (prev ? { ...prev, tipo } : prev));
      setNewTipo("");
    } catch (err) {
      alert(err?.response?.data?.detail || "Impossibile aggiungere il tipo");
    } finally {
      setAddingTipo(false);
    }
  };

  const save = async () => {
    if (!editing?.titolo || !editing?.date) return alert("Titolo e data sono obbligatori");
    if (editing.inviteMode === "manual" && !(editing.invitedMemberIds || []).length) {
      return alert("Seleziona almeno un associato oppure usa «Tutti» o filtri per ruolo.");
    }
    if (editing.inviteMode === "roles" && !(editing.invitedRoleGroups || []).length) {
      return alert("Seleziona almeno un gruppo ruolo oppure cambia modalità invitati.");
    }
    setSaving(true);
    try {
      const {
        inviteMode,
        utilityMaterial: _utilityMaterial,
        ...rest
      } = editing;
      const payload = {
        ...rest,
        invitedMemberIds: inviteMode === "manual" ? (editing.invitedMemberIds || []) : [],
        invitedRoleGroups: inviteMode === "roles" ? (editing.invitedRoleGroups || []) : [],
        orarioFine: editing.orarioFine || "",
        portalOnly: !!editing.portalOnly,
        attachments: editing.attachments || [],
      };
      if (editing.id) {
        await adminUpdateEvent(editing.id, payload);
        setEditing(normalizeEvent({ ...payload, id: editing.id }));
        load();
      } else {
        const created = await adminCreateEvent(payload);
        setEditing(normalizeEvent(created));
        setActiveTab("presenze");
        load();
      }
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id, titolo) => {
    if (!window.confirm(`Eliminare "${titolo}"?`)) return;
    await adminDeleteEvent(id);
    if (editing?.id === id) setEditing(null);
    load();
  };

  const invitedCount = (e) => (e.invitedMemberIds || e.relatedMemberIds || []).length;
  const inviteLabel = (e) => {
    const roles = roleGroupsSummary(e.invitedRoleGroups);
    if (roles) return roles;
    const n = invitedCount(e);
    return n ? `${n} invitati` : "Tutti";
  };
  const hideFooter = editing?.id && activeTab === "presenze";

  return (
    <div data-testid="admin-events">
      <AdminPageHeader
        title="Eventi"
        description={`${items.length} eventi in calendario.`}
      >
        <Button
          onClick={() => { setEditing(empty()); setActiveTab("details"); }}
          variant="primary"
          data-testid="admin-events-new"
        >
          <Plus className="h-4 w-4" /> Nuovo evento
        </Button>
      </AdminPageHeader>

      {editing && (
        <AdminFormModal
          open
          title={editing.id ? "Modifica evento" : "Nuovo evento"}
          onClose={closeEdit}
          onSave={save}
          saving={saving}
          saveLabel={editing.id ? "Salva modifiche" : "Salva evento"}
          hideFooter={hideFooter}
          testid="admin-event-modal"
          maxWidth="max-w-4xl"
        >
          <EventEditForm
            editing={editing}
            setEditing={setEditing}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            tipi={tipi}
            newTipo={newTipo}
            setNewTipo={setNewTipo}
            onAddTipo={addTipo}
            addingTipo={addingTipo}
          />
        </AdminFormModal>
      )}

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {items.length === 0 ? (
          <div className="p-4">
            <AdminEmptyState icon={SITE_ICONS.events} title="Nessun evento." />
          </div>
        ) : (
          <>
            <ul className="divide-y divide-slate-100 lg:hidden">
              {items.map((e) => (
                <li key={e.id} className="p-4" data-testid={`event-row-${e.id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-navy-700 break-words">{e.titolo}</div>
                      <div className="text-sm text-slate-600 mt-1">
                        {formatEventDateTimeIt(e.date, e.orario, e.orarioFine)}
                      </div>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        <span className="text-xs bg-slate-100 px-2 py-0.5 rounded">{e.tipo}</span>
                        {e.portalOnly ? (
                          <span className="text-xs bg-amber-50 text-amber-800 px-2 py-0.5 rounded font-medium">Solo associati</span>
                        ) : (
                          <span className="text-xs bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded font-medium">Pubblico</span>
                        )}
                      </div>
                      {(e.luogo || invitedCount(e)) && (
                        <div className="text-xs text-slate-500 mt-1.5 break-words">
                          {e.luogo || "—"}
                          {" · "}
                          {inviteLabel(e)}
                        </div>
                      )}
                    </div>
                    <div className="flex shrink-0">
                      <button type="button" onClick={() => openEdit(e, "details")} className="p-2 rounded text-navy-600 hover:bg-navy-50" data-testid={`event-edit-${e.id}`} title="Modifica">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button type="button" onClick={() => remove(e.id, e.titolo)} className="p-2 text-red-600 hover:bg-red-50 rounded" data-testid={`event-delete-${e.id}`}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>

            <div className="hidden lg:block min-w-0">
              <table className="w-full table-fixed">
                <thead>
                  <tr className="bg-slate-50 text-xs uppercase text-slate-500 text-left">
                    <th className="px-4 py-3 w-[18%]">Data</th>
                    <th className="px-4 py-3 w-[42%]">Evento</th>
                    <th className="px-4 py-3 w-[20%]">Visibilità</th>
                    <th className="px-4 py-3 w-[20%] text-right">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((e) => (
                    <tr key={e.id} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`event-row-desktop-${e.id}`}>
                      <td className="px-4 py-3 text-sm">{formatEventDateTimeIt(e.date, e.orario, e.orarioFine)}</td>
                      <td className="px-4 py-3 min-w-0">
                        <div className="font-medium text-navy-700 truncate">{e.titolo}</div>
                        <div className="text-xs text-slate-500 mt-0.5 truncate">
                          <span className="bg-slate-100 px-1.5 py-0.5 rounded mr-1.5">{e.tipo}</span>
                          {e.luogo || "—"}
                          {" · "}
                          {inviteLabel(e)}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {e.portalOnly ? (
                          <span className="text-xs bg-amber-50 text-amber-800 px-2 py-0.5 rounded font-medium">Solo associati</span>
                        ) : (
                          <span className="text-xs bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded font-medium">Pubblico</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <button type="button" onClick={() => openEdit(e, "details")} className="p-1.5 rounded text-navy-600 hover:bg-navy-50" data-testid={`event-edit-${e.id}`} title="Modifica">
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button type="button" onClick={() => remove(e.id, e.titolo)} className="p-1.5 text-red-600 hover:bg-red-50 rounded ml-1" data-testid={`event-delete-${e.id}`}>
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
