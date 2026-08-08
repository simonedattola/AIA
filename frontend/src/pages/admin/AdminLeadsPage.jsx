import { Fragment, useEffect, useState, useMemo } from "react";
import { adminLeads, adminUpdateLead, adminDeleteLead } from "../../lib/api";
import { formatDateTimeIt, contactPreferenceLabel } from "../../lib/format";
import { Trash2, Mail, Phone, ChevronDown, ChevronUp } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import {
  AdminEmptyState,
  AdminPageHeader,
  AdminTableWrap,
  AdminMobileList,
  AdminDesktopOnly,
  adminTableHead,
  AdminFilterTabs,
  AdminBadge,
} from "../../components/admin/admin-ui";

export default function AdminLeadsPage() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(null);
  const [filter, setFilter] = useState("all");

  const load = () => adminLeads().then(setItems);
  useEffect(() => { load(); }, []);

  const newCount = items.filter((l) => l.status === "new").length;
  const filtered = useMemo(() => {
    if (filter === "new") return items.filter((l) => l.status === "new");
    if (filter === "read") return items.filter((l) => l.status !== "new");
    return items;
  }, [items, filter]);

  const setStatus = async (id, status) => {
    await adminUpdateLead(id, { status });
    load();
  };

  const remove = async (id, name) => {
    if (!window.confirm(`Eliminare la candidatura di ${name}?`)) return;
    await adminDeleteLead(id);
    load();
  };

  const statusBadge = (l) => {
    if (l.status === "new") return <AdminBadge variant="warning">Nuova</AdminBadge>;
    if (l.status === "contacted") return <AdminBadge variant="success">Contattata</AdminBadge>;
    return <AdminBadge variant="draft">Archiviata</AdminBadge>;
  };

  const detailPanel = (l) => (
    <div className="mt-3 pt-3 border-t border-slate-100 text-sm space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <strong className="text-slate-700">Stato:</strong>
        <select
          value={l.status}
          onChange={(e) => setStatus(l.id, e.target.value)}
          className="px-2.5 py-1.5 border border-slate-300 rounded text-xs bg-white"
          data-testid={`lead-status-${l.id}`}
        >
          <option value="new">Nuova</option>
          <option value="contacted">Contattata</option>
          <option value="archived">Archiviata</option>
        </select>
      </div>
      <div>
        <strong className="text-slate-700">Preferenza contatto:</strong>{" "}
        {contactPreferenceLabel(l.contactPreference)}
      </div>
      {l.message && (
        <div>
          <strong className="text-slate-700">Messaggio:</strong>
          <p className="mt-1 text-slate-600 whitespace-pre-line break-words">{l.message}</p>
        </div>
      )}
    </div>
  );

  const actions = (l) => (
    <div className="flex items-center gap-1 shrink-0">
      <button
        type="button"
        onClick={() => setOpen(open === l.id ? null : l.id)}
        className="p-2 text-slate-500 hover:bg-slate-100 rounded"
      >
        {open === l.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      <button
        type="button"
        onClick={() => remove(l.id, `${l.firstName} ${l.lastName}`)}
        className="p-2 text-red-600 hover:bg-red-50 rounded"
        data-testid={`lead-delete-${l.id}`}
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );

  return (
    <div data-testid="admin-leads">
      <AdminPageHeader
        title="Candidature Corso Arbitri"
        description="Richieste dal modulo corso arbitri. Le candidature nuove sono evidenziate in oro."
      />

      <AdminTableWrap>
        <div className="p-4 border-b border-slate-200">
          <AdminFilterTabs
            active={filter}
            onChange={setFilter}
            tabs={[
              { id: "all", label: "Tutti", count: items.length },
              { id: "new", label: "Nuovi", count: newCount },
              { id: "read", label: "Letti", count: items.length - newCount },
            ]}
          />
        </div>

        {filtered.length === 0 ? (
          <AdminEmptyState icon={SITE_ICONS.leads} title="Nessuna candidatura in questa vista." />
        ) : (
          <>
            <AdminMobileList>
              {filtered.map((l) => (
                <li
                  key={l.id}
                  className={`p-4 ${l.status === "new" ? "bg-gold-50/30" : ""}`}
                  data-testid={`lead-${l.id}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-navy-700 break-words">
                        {l.firstName} {l.lastName}
                      </div>
                      {l.age && <div className="text-xs text-slate-500 mt-0.5">{l.age} anni</div>}
                      <div className="mt-2 space-y-1 text-sm text-slate-600 min-w-0">
                        <a
                          href={`mailto:${l.email}`}
                          className="hover:text-navy-600 inline-flex items-center gap-1.5 min-w-0 max-w-full"
                        >
                          <Mail className="h-3.5 w-3.5 shrink-0" />
                          <span className="break-words">{l.email}</span>
                        </a>
                        {l.phone && (
                          <a href={`tel:${l.phone}`} className="hover:text-navy-600 inline-flex items-center gap-1.5">
                            <Phone className="h-3.5 w-3.5 shrink-0" />
                            {l.phone}
                          </a>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mt-2">
                        {statusBadge(l)}
                        <span className="text-xs text-slate-500">{formatDateTimeIt(l.createdAt)}</span>
                      </div>
                    </div>
                    {actions(l)}
                  </div>
                  {open === l.id && detailPanel(l)}
                </li>
              ))}
            </AdminMobileList>

            <AdminDesktopOnly>
              <table className="w-full table-fixed text-sm">
                <thead>
                  <tr className={adminTableHead}>
                    <th className="px-4 py-3 w-[22%]">Candidato</th>
                    <th className="px-4 py-3 w-[24%]">Email</th>
                    <th className="px-4 py-3 w-[16%]">Telefono</th>
                    <th className="px-4 py-3 w-[16%]">Data</th>
                    <th className="px-4 py-3 w-[12%]">Stato</th>
                    <th className="px-4 py-3 w-[10%] text-right">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((l) => (
                    <Fragment key={l.id}>
                      <tr
                        className={`border-t border-slate-100 hover:bg-slate-50/80 ${l.status === "new" ? "bg-gold-50/30" : ""}`}
                        data-testid={`lead-desktop-${l.id}`}
                      >
                        <td className="px-4 py-3.5 min-w-0">
                          <div className="font-medium text-navy-700 truncate">
                            {l.firstName} {l.lastName}
                          </div>
                          {l.age && <div className="text-xs text-slate-500 mt-0.5">{l.age} anni</div>}
                        </td>
                        <td className="px-4 py-3.5 min-w-0">
                          <a
                            href={`mailto:${l.email}`}
                            className="text-slate-600 hover:text-navy-600 inline-flex items-center gap-1.5 min-w-0 max-w-full"
                          >
                            <Mail className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate">{l.email}</span>
                          </a>
                        </td>
                        <td className="px-4 py-3.5 text-slate-600 min-w-0">
                          {l.phone ? (
                            <a href={`tel:${l.phone}`} className="hover:text-navy-600 inline-flex items-center gap-1.5">
                              <Phone className="h-3.5 w-3.5 shrink-0" />
                              <span className="truncate">{l.phone}</span>
                            </a>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="px-4 py-3.5 text-slate-600 truncate">{formatDateTimeIt(l.createdAt)}</td>
                        <td className="px-4 py-3.5">{statusBadge(l)}</td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-1 justify-end">
                            <button
                              type="button"
                              onClick={() => setOpen(open === l.id ? null : l.id)}
                              className="p-2 text-slate-500 hover:bg-slate-100 rounded"
                            >
                              {open === l.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            </button>
                            <button
                              type="button"
                              onClick={() => remove(l.id, `${l.firstName} ${l.lastName}`)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded"
                              data-testid={`lead-delete-desktop-${l.id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                      {open === l.id && (
                        <tr className="border-t border-slate-100">
                          <td colSpan={6} className="px-4 py-4 bg-slate-50/80 text-sm space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <strong className="text-slate-700">Stato:</strong>
                              <select
                                value={l.status}
                                onChange={(e) => setStatus(l.id, e.target.value)}
                                className="px-2.5 py-1.5 border border-slate-300 rounded text-xs bg-white"
                                data-testid={`lead-status-desktop-${l.id}`}
                              >
                                <option value="new">Nuova</option>
                                <option value="contacted">Contattata</option>
                                <option value="archived">Archiviata</option>
                              </select>
                            </div>
                            <div>
                              <strong className="text-slate-700">Preferenza contatto:</strong>{" "}
                              {contactPreferenceLabel(l.contactPreference)}
                            </div>
                            {l.message && (
                              <div>
                                <strong className="text-slate-700">Messaggio:</strong>
                                <p className="mt-1 text-slate-600 whitespace-pre-line break-words">{l.message}</p>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </Fragment>
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
