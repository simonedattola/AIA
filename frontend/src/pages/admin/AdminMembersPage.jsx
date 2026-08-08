import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  adminMembers, adminCreateMember, adminUpdateMember, adminDeleteMember, adminUpload,
} from "../../lib/api";
import { toast, apiErrorMessage } from "../../lib/toast";
import {
  AIA_QUALIFICHE,
  ORGANIGRAMMA_KINDS,
  ROLE_FILTERS,
  normalizeMember,
  memberRoleLabel,
  canHaveMaxCategory,
  defaultPortalPassword,
  seniorityYears,
  yearStartFromSeniority,
  isSectionPresident,
  matchesRoleFilter,
} from "../../lib/memberRoles";
import { Plus, Pencil, Trash2, Save, X, Upload, Search, Loader2, Filter, User as UserIcon, ExternalLink, Award } from "lucide-react";
import { Link } from "react-router-dom";
import MediaImage from "../../components/MediaImage";
import MemberPresenzePanel from "../../components/admin/MemberPresenzePanel";
import MemberFileImport from "../../components/admin/MemberFileImport";
import { AdminEmptyState, AdminPageHeader } from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const empty = () => ({
  firstName: "",
  lastName: "",
  role: "",
  memberRole: "arbitro",
  observerType: "",
  organigrammaKind: "",
  boardTitle: "",
  isPresident: false,
  category: "",
  yearStart: null,
  seniorityYears: "",
  meccanografico: "",
  portalPassword: "",
  photoUrl: "",
  bio: "",
  chiSiamoText: "",
  presidentLongBio: "",
  email: "",
  phone: "",
  notes: "",
  awards: [],
});

function withFormFields(m) {
  const n = normalizeMember(m);
  const years = seniorityYears(n.yearStart);
  return {
    ...n,
    seniorityYears: years == null ? "" : String(years),
    portalPassword: n.portalPassword || defaultPortalPassword(n.firstName, n.lastName),
  };
}

function memberRoleFromAia(code) {
  const map = { AE: "arbitro", AA: "assistente", AB: "arbitro", AFR: "arbitro", OA: "osservatore", OT: "osservatore" };
  return map[code] || (code ? "arbitro" : "");
}

export default function AdminMembersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [q, setQ] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminMembers({});
      setItems(data.map(normalizeMember));
    } catch (e) {
      toast.error(apiErrorMessage(e, "Impossibile caricare associati"));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (searchParams.get("new") === "1") {
      setEditing(empty());
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const validate = (m) => {
    if (!m.firstName?.trim()) return "Il nome è obbligatorio";
    if (!m.lastName?.trim()) return "Il cognome è obbligatorio";
    if (m.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(m.email)) return "Email non valida";
    const years = m.seniorityYears === "" || m.seniorityYears == null ? null : Number(m.seniorityYears);
    if (years != null && (Number.isNaN(years) || years < 0 || years > 120)) return "Anzianità non valida";
    if (m.organigrammaKind && !m.boardTitle?.trim()) {
      return "Indica l'incarico in organigramma (es. Segretario, Area Informatica)";
    }
    const code = String(m.role || "").trim().toUpperCase();
    if (["AE", "AA", "AB", "AFR"].includes(code) && !m.meccanografico?.trim()) {
      return "Il codice meccanografico è obbligatorio per l'accesso all'area associati";
    }
    return null;
  };

  const save = async () => {
    const err = validate(editing);
    if (err) return toast.error(err);
    setSaving(true);
    try {
      const code = String(editing.role || "").trim().toUpperCase();
      const organigrammaKind = (editing.organigrammaKind || "").trim().toLowerCase();
      const boardTitle = organigrammaKind ? (editing.boardTitle || "").trim() : "";
      const memberRole = code
        ? memberRoleFromAia(code)
        : organigrammaKind === "cds"
          ? "consiglio_direttivo"
          : editing.memberRole || "arbitro";
      const yearStart = yearStartFromSeniority(editing.seniorityYears);
      const draft = {
        ...editing,
        firstName: editing.firstName.trim(),
        lastName: editing.lastName.trim(),
        role: code,
        memberRole,
        organigrammaKind,
        boardTitle,
        observerType: code === "OT" ? "ot" : code === "OA" ? "oa" : "",
        category: canHaveMaxCategory({ role: code }) ? (editing.category || "").trim() : "",
        yearStart,
        bio: (editing.bio || "").trim(),
        chiSiamoText: (editing.chiSiamoText || "").trim(),
        presidentLongBio: (editing.presidentLongBio || "").trim(),
        bioHtml: "",
        isPresident: isSectionPresident({ organigrammaKind, boardTitle }),
        awards: (editing.awards || [])
          .filter((a) => (a.title || "").trim())
          .map((a, i) => ({
            ...a,
            title: a.title.trim(),
            sortOrder: i,
            year: a.year ? Number(a.year) : null,
          })),
      };
      delete draft.seniorityYears;
      delete draft.portalPassword;
      if (editing.id) {
        const upd = await adminUpdateMember(editing.id, draft);
        toast.success(`${upd.firstName} ${upd.lastName} aggiornato`);
      } else {
        const res = await adminCreateMember(draft);
        toast.success(`${res.firstName} ${res.lastName} creato`);
      }
      setEditing(null);
      load();
    } catch (e) {
      toast.error(apiErrorMessage(e, "Errore salvataggio"));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id, name) => {
    if (!window.confirm(`Eliminare ${name}?`)) return;
    try {
      await adminDeleteMember(id);
      toast.success(`${name} eliminato`);
      load();
    } catch (e) {
      toast.error(apiErrorMessage(e, "Errore eliminazione"));
    }
  };

  const uploadPhoto = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setUploadingPhoto(true);
    try {
      const res = await adminUpload(f);
      setEditing({ ...editing, photoUrl: res.url });
      toast.success("Foto caricata");
    } catch (err) {
      toast.error(apiErrorMessage(err, "Upload fallito"));
    } finally {
      setUploadingPhoto(false);
    }
  };

  const filtered = items.filter((m) => {
    if (!matchesRoleFilter(m, roleFilter)) return false;
    if (!q) return true;
    return `${m.firstName} ${m.lastName} ${m.category} ${m.boardTitle} ${m.role} ${m.meccanografico || ""}`
      .toLowerCase()
      .includes(q.toLowerCase());
  });

  return (
    <div data-testid="admin-members">
      <AdminPageHeader
        title="Anagrafica"
        description={`${items.length} persone · organigramma, arbitri e osservatori.`}
      >
        <div className="flex flex-wrap items-center gap-2">
          <MemberFileImport
            onImported={(res) => {
              toast.success(
                `${res.inserted} nuovi · ${res.updated} aggiornati` +
                (res.skippedDuplicates ? ` · ${res.skippedDuplicates} già presenti` : "")
              );
              load();
            }}
          />
          <Button onClick={() => setEditing(empty())} variant="primary" data-testid="admin-members-new">
            <Plus className="h-4 w-4" /> Nuovo profilo
          </Button>
        </div>
      </AdminPageHeader>

      {editing && (
        <MemberModal
          editing={editing}
          setEditing={setEditing}
          save={save}
          saving={saving}
          uploadPhoto={uploadPhoto}
          uploadingPhoto={uploadingPhoto}
        />
      )}

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex flex-col md:flex-row gap-3 items-stretch md:items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Cerca per nome, incarico, codice…"
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20"
              data-testid="admin-members-search"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            {ROLE_FILTERS.map((f) => (
              <button
                key={f.value || "all"}
                type="button"
                onClick={() => setRoleFilter(f.value)}
                className={`px-2.5 py-1 rounded text-xs font-medium ${
                  roleFilter === f.value ? "bg-navy-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="px-4 py-10 text-center text-slate-500">
            <Loader2 className="h-5 w-5 animate-spin inline mr-2" /> Caricamento…
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-4">
            <AdminEmptyState icon={UserIcon} title="Nessun profilo trovato." />
          </div>
        ) : (
          <>
            <ul className="divide-y divide-slate-100 lg:hidden" data-testid="admin-members-mobile-list">
              {filtered.map((m) => {
                const years = seniorityYears(m.yearStart);
                return (
                  <li key={m.id} className="p-4" data-testid={`member-row-${m.id}`}>
                    <div className="flex items-start gap-3">
                      {m.photoUrl ? (
                        <MediaImage src={m.photoUrl} alt="" className="w-11 h-11 rounded-full object-cover border border-slate-200 shrink-0" />
                      ) : (
                        <div className="w-11 h-11 rounded-full bg-navy-100 text-navy-600 flex items-center justify-center text-sm font-bold shrink-0">
                          {m.firstName[0]}{m.lastName[0]}
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-navy-700 break-words">{m.firstName} {m.lastName}</div>
                        <div className="text-sm text-slate-600 mt-0.5 break-words">{memberRoleLabel(m)}</div>
                        {m.boardTitle && <div className="text-xs text-slate-500 mt-0.5 break-words">{m.boardTitle}</div>}
                        <div className="text-xs text-slate-500 mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
                          {m.meccanografico && <span className="font-mono">{m.meccanografico}</span>}
                          {years != null && <span>{years === 1 ? "1 anno" : `${years} anni`}</span>}
                        </div>
                      </div>
                      <div className="flex shrink-0 gap-0.5">
                        {m.slug && (
                          <a href={`/arbitri/${m.slug}`} target="_blank" rel="noopener noreferrer" className="p-2 text-slate-500 hover:text-navy-600 rounded" title="Profilo pubblico">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                        <button type="button" onClick={() => setEditing(withFormFields({ ...m, awards: m.awards || [] }))} className="p-2 text-navy-600 hover:bg-navy-50 rounded" data-testid={`member-edit-${m.id}`}>
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button type="button" onClick={() => remove(m.id, `${m.firstName} ${m.lastName}`)} className="p-2 text-red-600 hover:bg-red-50 rounded">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>

            <div className="hidden lg:block overflow-x-auto">
              <table className="w-full table-fixed">
                <thead>
                  <tr className="bg-slate-50 text-xs uppercase text-slate-500 text-left">
                    <th className="px-4 py-3 w-[38%]">Nome</th>
                    <th className="px-4 py-3 w-[28%]">Ruolo / incarico</th>
                    <th className="px-4 py-3 w-[14%]">Mecc.</th>
                    <th className="px-4 py-3 w-[10%]">Anz.</th>
                    <th className="px-4 py-3 w-[10%] text-right">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((m) => {
                    const years = seniorityYears(m.yearStart);
                    return (
                      <tr key={m.id} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`member-row-desktop-${m.id}`}>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3 min-w-0">
                            {m.photoUrl ? (
                              <MediaImage src={m.photoUrl} alt="" className="w-9 h-9 rounded-full object-cover border border-slate-200 shrink-0" />
                            ) : (
                              <div className="w-9 h-9 rounded-full bg-navy-100 text-navy-600 flex items-center justify-center text-xs font-bold shrink-0">
                                {m.firstName[0]}{m.lastName[0]}
                              </div>
                            )}
                            <div className="min-w-0">
                              <div className="font-medium text-navy-700 truncate">{m.firstName} {m.lastName}</div>
                              {m.email && <div className="text-xs text-slate-400 truncate">{m.email}</div>}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm min-w-0">
                          <div className="truncate">{memberRoleLabel(m)}</div>
                          {m.boardTitle && <div className="text-xs text-slate-500 truncate">{m.boardTitle}</div>}
                        </td>
                        <td className="px-4 py-3 text-sm font-mono truncate">{m.meccanografico || "—"}</td>
                        <td className="px-4 py-3 text-sm">{years == null ? "—" : `${years}a`}</td>
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                          {m.slug && (
                            <a href={`/arbitri/${m.slug}`} target="_blank" rel="noopener noreferrer" className="p-1.5 text-slate-500 hover:text-navy-600 hover:bg-navy-50 rounded inline-block" title="Profilo pubblico">
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          )}
                          <button type="button" onClick={() => setEditing(withFormFields({ ...m, awards: m.awards || [] }))} className="p-1.5 text-navy-600 hover:bg-navy-50 rounded" data-testid={`member-edit-${m.id}`}>
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button type="button" onClick={() => remove(m.id, `${m.firstName} ${m.lastName}`)} className="p-1.5 text-red-600 hover:bg-red-50 rounded ml-1">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function MemberModal({ editing, setEditing, save, saving, uploadPhoto, uploadingPhoto }) {
  const set = (k) => (e) => {
    const next = { ...editing, [k]: e.target.value };
    if (k === "firstName" || k === "lastName") {
      next.portalPassword = defaultPortalPassword(
        k === "firstName" ? e.target.value : editing.firstName,
        k === "lastName" ? e.target.value : editing.lastName
      );
    }
    setEditing(next);
  };
  const code = String(editing.role || "").trim().toUpperCase();
  const hasOrg = !!(editing.organigrammaKind || "").trim();
  const showCategory = canHaveMaxCategory({ role: code });
  const presidentPreview = isSectionPresident({
    organigrammaKind: editing.organigrammaKind,
    boardTitle: editing.boardTitle,
  });
  const portalPassword = editing.portalPassword || defaultPortalPassword(editing.firstName, editing.lastName);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 overflow-y-auto" data-testid="member-modal">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[92vh] overflow-y-auto my-8">
        <div className="sticky top-0 bg-white border-b border-slate-200 p-5 flex items-center justify-between z-10">
          <h2 className="font-display text-xl font-bold text-navy-700">
            {editing.id ? "Modifica profilo" : "Nuovo profilo"}
          </h2>
          <button type="button" onClick={() => setEditing(null)} className="p-2 text-slate-400 hover:bg-slate-100 rounded">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div className="flex items-center gap-4">
            {editing.photoUrl ? (
              <MediaImage src={editing.photoUrl} alt="" className="w-20 h-20 rounded-lg object-cover border-2 border-slate-200" />
            ) : (
              <div className="w-20 h-20 rounded-lg bg-slate-100 border-2 border-dashed border-slate-300 flex items-center justify-center text-slate-400">
                <UserIcon className="h-8 w-8" />
              </div>
            )}
            <div>
              <input type="file" accept="image/*" onChange={uploadPhoto} className="hidden" id="member-photo" />
              <label htmlFor="member-photo" className="cursor-pointer inline-flex">
                <Button type="button" variant="outline" size="sm" className="text-sm pointer-events-none" tabIndex={-1}>
                  {uploadingPhoto ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}{" "}
                  {editing.photoUrl ? "Cambia foto" : "Carica foto"}
                </Button>
              </label>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Nome*">
              <input data-testid="member-firstName" value={editing.firstName} onChange={set("firstName")} className={I} />
            </Field>
            <Field label="Cognome*">
              <input data-testid="member-lastName" value={editing.lastName} onChange={set("lastName")} className={I} />
            </Field>

            <Field label="Qualifica AIA">
              <select
                data-testid="member-aia-code"
                value={code}
                onChange={(e) => {
                  const role = e.target.value;
                  setEditing({
                    ...editing,
                    role,
                    memberRole: memberRoleFromAia(role) || editing.memberRole,
                    observerType: role === "OT" ? "ot" : role === "OA" ? "oa" : "",
                    category: canHaveMaxCategory({ role }) ? editing.category : "",
                  });
                }}
                className={I}
              >
                {AIA_QUALIFICHE.map((r) => (
                  <option key={r.value || "none"} value={r.value}>{r.label}</option>
                ))}
              </select>
            </Field>

            <Field label="Organigramma">
              <select
                data-testid="member-organigramma"
                value={editing.organigrammaKind || ""}
                onChange={(e) => setEditing({ ...editing, organigrammaKind: e.target.value })}
                className={I}
              >
                {ORGANIGRAMMA_KINDS.map((r) => (
                  <option key={r.value || "none"} value={r.value}>{r.label}</option>
                ))}
              </select>
            </Field>

            {hasOrg && (
              <Field label="Incarico*">
                <input
                  data-testid="member-boardTitle"
                  value={editing.boardTitle || ""}
                  onChange={set("boardTitle")}
                  className={I}
                  placeholder="Es. Segretario, Area Informatica"
                />
              </Field>
            )}

            {showCategory && (
              <Field label="Categoria massima">
                <input value={editing.category || ""} onChange={set("category")} className={I} />
              </Field>
            )}

            <Field label="Anzianità (anni)">
              <input
                type="number"
                min="0"
                max="120"
                value={editing.seniorityYears ?? ""}
                onChange={set("seniorityYears")}
                className={I}
                placeholder="Es. 4"
              />
            </Field>

            <Field label="Codice meccanografico">
              <input
                value={editing.meccanografico || ""}
                onChange={set("meccanografico")}
                className={`${I} font-mono`}
                placeholder="es. 12345678"
              />
            </Field>
            <Field label="Password">
              <input
                value={portalPassword}
                readOnly
                className={`${I} font-mono bg-slate-50 text-slate-700`}
                data-testid="member-portal-password"
              />
            </Field>

            <Field label="Email">
              <input type="email" value={editing.email || ""} onChange={set("email")} className={I} />
            </Field>
            <Field label="Telefono">
              <input type="tel" value={editing.phone || ""} onChange={set("phone")} className={I} />
            </Field>
          </div>

          <Field label="Biografia">
            <textarea
              rows={5}
              value={editing.bio || ""}
              onChange={set("bio")}
              className={I}
              placeholder="Percorso, esperienze, ruolo in sezione…"
            />
          </Field>

          {presidentPreview && (
            <>
              <Field label='Testo card "Chi siamo" (Presidente)'>
                <textarea
                  rows={5}
                  value={editing.chiSiamoText || ""}
                  onChange={set("chiSiamoText")}
                  className={I}
                  placeholder="Testo di presentazione del Presidente in evidenza nella pagina Chi siamo…"
                />
              </Field>
              <Field label="Testo lungo profilo Presidente">
                <textarea
                  rows={9}
                  value={editing.presidentLongBio || ""}
                  onChange={set("presidentLongBio")}
                  className={I}
                  placeholder="Racconto esteso del percorso e della visione del Presidente…"
                />
              </Field>
            </>
          )}

          <AwardsEditor awards={editing.awards || []} onChange={(awards) => setEditing({ ...editing, awards })} />

          {editing.id && <MemberPresenzePanel memberId={editing.id} />}

          <Field label="Note private (solo admin)">
            <textarea rows={3} value={editing.notes || ""} onChange={set("notes")} className={I} />
          </Field>

          {editing.slug && (
            <p className="text-sm text-slate-600">
              Profilo:{" "}
              <Link to={`/arbitri/${editing.slug}`} target="_blank" className="text-navy-600 hover:underline font-medium">
                /arbitri/{editing.slug}
              </Link>
            </p>
          )}
        </div>

        <div className="sticky bottom-0 bg-white border-t border-slate-200 p-5 flex justify-end gap-3">
          <Button type="button" onClick={() => setEditing(null)} variant="outline">Annulla</Button>
          <Button type="button" onClick={save} disabled={saving} variant="primary" className="disabled:opacity-50" data-testid="member-save">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Salva
          </Button>
        </div>
      </div>
    </div>
  );
}

function AwardsEditor({ awards, onChange }) {
  const add = () => onChange([...awards, { id: `award-${Date.now()}`, title: "", year: new Date().getFullYear(), description: "", sortOrder: awards.length }]);
  const update = (idx, patch) => {
    const next = [...awards];
    next[idx] = { ...next[idx], ...patch };
    onChange(next);
  };
  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
      <div className="flex items-center justify-between mb-3">
        <span className="font-medium text-navy-700 flex items-center gap-2">
          <Award className="h-5 w-5 text-gold-500" /> Premi e riconoscimenti
        </span>
        <button type="button" onClick={add} className="text-sm text-navy-600 hover:underline">+ Aggiungi</button>
      </div>
      {awards.map((a, idx) => (
        <div key={a.id || idx} className="bg-white border border-slate-200 rounded-md p-3 mb-2 grid grid-cols-1 md:grid-cols-12 gap-2">
          <input className={`${I} md:col-span-5`} placeholder="Titolo*" value={a.title || ""} onChange={(e) => update(idx, { title: e.target.value })} />
          <input className={`${I} md:col-span-2`} type="number" placeholder="Anno" value={a.year || ""} onChange={(e) => update(idx, { year: e.target.value })} />
          <input className={`${I} md:col-span-4`} placeholder="Descrizione" value={a.description || ""} onChange={(e) => update(idx, { description: e.target.value })} />
          <button type="button" onClick={() => onChange(awards.filter((_, i) => i !== idx))} className="md:col-span-1 text-red-600 text-sm">×</button>
        </div>
      ))}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-slate-700 mb-1">{label}</span>
      {children}
    </label>
  );
}

const I = "w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:border-navy-600 focus:outline-none focus:ring-2 focus:ring-navy-600/20";
