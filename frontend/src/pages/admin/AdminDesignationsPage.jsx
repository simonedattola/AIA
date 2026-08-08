import { useEffect, useState, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  adminDesignations, adminCreateDesignation, adminUpdateDesignation, adminDeleteDesignation,
  adminMembers, adminSyncDesignationsAia, adminDesignationsSyncStatus,
} from "../../lib/api";
import { MemberSingleSelect } from "../../components/admin/MemberSelect";
import { formatDateTimeIt } from "../../lib/format";
import { displayDesignationGara, formatDesignationMeta } from "../../lib/designationsDisplay";
import DesignationsTableBody from "../../components/designations/DesignationsTableBody";
import DesignationFileImport from "../../components/admin/DesignationFileImport";
import { formatDateIt } from "../../lib/format";
import { Plus, Pencil, Trash2, RefreshCw, Loader2, ExternalLink, CalendarDays } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import { AdminEmptyState, AdminFormModal, AdminPageHeader } from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const ROLES = ["Arbitro", "Assistente 1", "Assistente 2"];

function formatImportResult(res) {
  if (!res?.ok) return res?.error || "Import non riuscito.";
  const parts = [`${res.inserted} nuove designazioni`];
  if (res.updated) parts.push(`${res.updated} già presenti (aggiornate)`);
  if (res.skippedDuplicates) parts.push(`${res.skippedDuplicates} duplicate evitate`);
  if (res.membersCreated) parts.push(`${res.membersCreated} nuovi associati`);
  return `${parts.join(" · ")}.`;
}

const empty = () => ({
  matchDate: new Date().toISOString().slice(0, 10),
  championship: "", girone: "", matchDay: "",
  matchHome: "", matchAway: "", matchLabel: "",
  role: "Arbitro", memberName: "", memberId: null, memberSlug: "",
  category: "", status: "published", source: "manual",
});

const inputCls = "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";
const Field = ({ label, children }) => (
  <label className="block">
    <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
    {children}
  </label>
);

function DesignationEditForm({ editing, setEditing, members, onMemberChange }) {
  return (
    <div data-testid="admin-designation-form">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Field label="Data*">
          <input data-testid="designation-date" type="date" value={(editing.matchDate || "").slice(0, 10)} onChange={(e) => setEditing({ ...editing, matchDate: e.target.value })} className={inputCls} />
        </Field>
        <Field label="Campionato">
          <input value={editing.championship || editing.category || ""} onChange={(e) => setEditing({ ...editing, championship: e.target.value, category: e.target.value })} className={inputCls} />
        </Field>
        <Field label="Girone">
          <input value={editing.girone || ""} onChange={(e) => setEditing({ ...editing, girone: e.target.value })} className={inputCls} />
        </Field>
        <Field label="Giornata">
          <input value={editing.matchDay || ""} onChange={(e) => setEditing({ ...editing, matchDay: e.target.value })} className={inputCls} />
        </Field>
        <Field label="Squadra casa">
          <input value={editing.matchHome || ""} onChange={(e) => setEditing({ ...editing, matchHome: e.target.value })} className={inputCls} />
        </Field>
        <Field label="Squadra ospite">
          <input value={editing.matchAway || ""} onChange={(e) => setEditing({ ...editing, matchAway: e.target.value })} className={inputCls} />
        </Field>
        <Field label="Ruolo">
          <select value={editing.role} onChange={(e) => setEditing({ ...editing, role: e.target.value })} className={inputCls} data-testid="designation-role">
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </Field>
        <Field label="Associato collegato">
          <MemberSingleSelect
            value={editing.memberId}
            onChange={onMemberChange}
            members={members}
            label=""
            testId="designation-member"
          />
          {editing.memberSlug && (
            <a href={`/arbitri/${editing.memberSlug}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs text-navy-600 mt-1 hover:underline">
              <ExternalLink className="h-3 w-3" /> Vedi profilo pubblico
            </a>
          )}
        </Field>
        <Field label="Stato">
          <select value={editing.status} onChange={(e) => setEditing({ ...editing, status: e.target.value })} className={inputCls} data-testid="designation-status">
            <option value="published">Pubblicata</option>
            <option value="pending_approval">In attesa</option>
          </select>
        </Field>
      </div>
    </div>
  );
}

export default function AdminDesignationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [members, setMembers] = useState([]);
  const [editing, setEditing] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncMsg, setSyncMsg] = useState("");
  const [saving, setSaving] = useState(false);

  const membersById = useMemo(
    () => Object.fromEntries(members.map((m) => [m.id, m])),
    [members]
  );

  const load = () => adminDesignations().then(setItems);
  const loadMembers = () => adminMembers({ memberRole: "arbitro" }).then((a) =>
    adminMembers({ memberRole: "assistente" }).then((b) => setMembers([...a, ...b]))
  );

  useEffect(() => {
    load();
    loadMembers();
    adminDesignationsSyncStatus().then(setSyncStatus).catch(() => {});
  }, []);

  useEffect(() => {
    if (searchParams.get("new") === "1") {
      setEditing(empty());
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const openEdit = (d) => setEditing({ ...d, memberId: d.memberId || null });
  const closeEdit = () => setEditing(null);

  const syncFromAia = async () => {
    if (!window.confirm(
      "Importare le designazioni da AIA FIGC (Sezione Legnano)?\n\nLe designazioni importate in precedenza verranno sostituite. Quelle inserite manualmente restano invariate."
    )) return;
    setSyncing(true);
    setSyncMsg("");
    try {
      const res = await adminSyncDesignationsAia({
        filterSection: "Legnano",
        replaceExisting: true,
      });
      if (res.ok === false) {
        setSyncMsg(res.error || "Nessuna designazione importata.");
        return;
      }
      setSyncMsg(
        `Importate ${res.inserted} designazioni (${res.pagesFetched} pagine AIA)` +
        (res.membersCreated ? ` · ${res.membersCreated} nuovi associati` : "") +
        (res.updated ? ` · ${res.updated} aggiornate` : "") +
        (res.removed ? ` · ${res.removed} rimosse (non più su AIA)` : "") +
        (res.membersBackfilled ? ` · ${res.membersBackfilled} collegamenti aggiornati` : "") +
        "."
      );
      if (res.errors?.length) {
        setSyncMsg((m) => `${m} ${res.errors.length} avvisi.`);
      }
      adminDesignationsSyncStatus().then(setSyncStatus);
      await loadMembers();
      load();
    } catch (e) {
      setSyncMsg(e?.response?.data?.detail || "Sincronizzazione fallita.");
    } finally {
      setSyncing(false);
    }
  };

  const save = async () => {
    if (!editing?.matchLabel && !(editing?.matchHome && editing?.matchAway)) {
      return alert("Indica la gara (oppure squadra casa e ospite)");
    }
    setSaving(true);
    try {
      const payload = {
        ...editing,
        matchDate: editing.matchDate.length === 10 ? `${editing.matchDate}T15:00:00+00:00` : editing.matchDate,
        matchLabel: editing.matchLabel || `${editing.matchHome} - ${editing.matchAway}`,
        category: editing.championship || editing.category || "",
      };
      if (editing.id) await adminUpdateDesignation(editing.id, payload);
      else await adminCreateDesignation(payload);
      setEditing(null);
      load();
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id, label) => {
    if (!window.confirm(`Eliminare "${label}"?`)) return;
    await adminDeleteDesignation(id);
    if (editing?.id === id) setEditing(null);
    load();
  };

  const onMemberChange = (id) => {
    if (!id) return setEditing({ ...editing, memberId: null, memberSlug: "", memberName: "" });
    const m = members.find((mm) => mm.id === id);
    setEditing({
      ...editing,
      memberId: id,
      memberSlug: m?.slug || "",
      memberName: m ? `${m.firstName} ${m.lastName}` : "",
    });
  };

  const memberLabel = (d) => {
    if (d.memberId && membersById[d.memberId]) {
      const m = membersById[d.memberId];
      return `${m.firstName} ${m.lastName}`;
    }
    return d.memberName || "—";
  };

  const formProps = {
    editing,
    setEditing,
    members,
    onMemberChange,
  };

  return (
    <div data-testid="admin-designations">
      <AdminPageHeader
        title="Designazioni"
        description={`Designazioni stagione attuale. ${items.length} in elenco · ${items.filter((d) => d.status === "pending_approval").length} in attesa. Sul profilo pubblico degli associati resta lo storico completo.`}
      >
        <div className="flex flex-wrap items-center gap-2">
          <DesignationFileImport
            onImported={(res) => {
              setSyncMsg(formatImportResult(res));
              loadMembers();
              load();
            }}
          />
          <Button
            onClick={syncFromAia}
            disabled={syncing}
            variant="outline"
            className="disabled:opacity-50"
            data-testid="admin-designations-sync-aia"
          >
            {syncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {syncing ? "Sincronizzazione…" : "Sync AIA FIGC"}
          </Button>
          <Button onClick={() => setEditing(empty())} variant="primary" data-testid="admin-designations-new">
            <Plus className="h-4 w-4" /> Nuova designazione
          </Button>
        </div>
      </AdminPageHeader>

      {(syncMsg || syncStatus?.at) && (
        <div className="mb-6 p-4 rounded-lg border border-slate-200 bg-slate-50 text-sm text-slate-700" data-testid="designations-sync-status">
          {syncMsg && <p className="font-medium text-navy-700">{syncMsg}</p>}
          {syncStatus?.at && (
            <p className="mt-1 text-slate-500">
              Ultimo sync: {formatDateTimeIt(syncStatus.at)}
              {syncStatus.inserted != null && ` · ${syncStatus.inserted} designazioni`}
              {syncStatus.membersCreated > 0 && ` · ${syncStatus.membersCreated} associati creati`}
              {syncStatus.membersBackfilled > 0 && ` · ${syncStatus.membersBackfilled} collegati`}
            </p>
          )}
        </div>
      )}

      {editing && (
        <AdminFormModal
          open
          title={editing.id ? "Modifica designazione" : "Nuova designazione"}
          onClose={closeEdit}
          onSave={save}
          saving={saving}
          testid="admin-designation-modal"
          maxWidth="max-w-4xl"
        >
          <DesignationEditForm {...formProps} />
        </AdminFormModal>
      )}

      {items.length === 0 && !editing ? (
        <AdminEmptyState icon={SITE_ICONS.designations} title="Nessuna designazione. Importa da file o usa Sync AIA FIGC." />
      ) : items.length > 0 ? (
        <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm bg-white">
          <ul className="divide-y divide-slate-100 lg:hidden" data-testid="admin-designations-mobile-list">
            {items.map((d) => (
              <li key={d.id} className="p-4" data-testid={`designation-row-${d.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="inline-flex items-center gap-1 text-sm text-slate-700">
                        <CalendarDays className="h-4 w-4 text-gold-400 shrink-0" />
                        {formatDateIt(d.matchDate, { short: true })}
                      </span>
                      <span className="text-xs bg-navy-50 text-navy-700 px-2 py-0.5 rounded font-medium">{d.role}</span>
                    </div>
                    <p className="text-sm font-medium text-navy-700 break-words">{displayDesignationGara(d)}</p>
                    <p className="text-xs text-slate-500 mt-1 break-words">{formatDesignationMeta(d)}</p>
                    <p className="text-sm mt-1.5">
                      {d.memberSlug ? (
                        <Link to={`/arbitri/${d.memberSlug}`} target="_blank" className="text-navy-600 hover:underline font-medium break-words">
                          {memberLabel(d)}
                        </Link>
                      ) : (
                        <span className="break-words">{memberLabel(d)}</span>
                      )}
                      {!d.memberId && d.memberName && (
                        <span className="ml-1 text-[10px] text-amber-600">non collegato</span>
                      )}
                    </p>
                  </div>
                  <div className="flex shrink-0">
                    <button type="button" onClick={() => openEdit(d)} className="p-2 rounded text-navy-600 hover:bg-navy-50" data-testid={`designation-edit-${d.id}`} title="Modifica">
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button type="button" onClick={() => remove(d.id, displayDesignationGara(d))} className="p-2 text-red-600 hover:bg-red-50 rounded" data-testid={`designation-delete-${d.id}`}>
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <div className="hidden lg:block overflow-x-auto">
            <DesignationsTableBody
              designations={items}
              tableTestId="admin-designations-table"
              rowTestIdPrefix="designation-row-desktop"
              renderNominativo={(d) => (
                <>
                  {d.memberSlug ? (
                    <Link to={`/arbitri/${d.memberSlug}`} target="_blank" className="text-navy-600 hover:underline font-medium">
                      {memberLabel(d)}
                    </Link>
                  ) : (
                    <span>{memberLabel(d)}</span>
                  )}
                  {!d.memberId && d.memberName && (
                    <span className="block text-[10px] text-amber-600">non collegato</span>
                  )}
                </>
              )}
              renderActions={(d) => (
                <>
                  <button
                    type="button"
                    onClick={() => openEdit(d)}
                    className="p-1.5 rounded text-navy-600 hover:bg-navy-50"
                    data-testid={`designation-edit-${d.id}`}
                    title="Modifica"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => remove(d.id, displayDesignationGara(d))}
                    className="p-1.5 text-red-600 hover:bg-red-50 rounded ml-1"
                    data-testid={`designation-delete-${d.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </>
              )}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
