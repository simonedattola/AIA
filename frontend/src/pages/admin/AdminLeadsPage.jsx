import { Fragment, useEffect, useState, useMemo } from "react";
import { adminLeads, adminUpdateLead, adminDeleteLead } from "../../lib/api";
import { formatDateTimeIt, contactPreferenceLabel } from "../../lib/format";
import { Trash2, Mail, Phone, ChevronDown, ChevronUp } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import {
  AdminEmptyState,
  AdminPageHeader,
  AdminTableWrap,
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

        <table className="w-full text-sm">
          <thead>
            <tr className={adminTableHead}>
              <th className="px-4 py-3">Candidato</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Telefono</th>
              <th className="px-4 py-3">Data</th>
              <th className="px-4 py-3">Stato</th>
              <th className="px-4 py-3 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((l) => (
              <Fragment key={l.id}>
                <tr
                  className={`border-t border-slate-100 hover:bg-slate-50/80 ${l.status === "new" ? "bg-gold-50/30" : ""}`}
                  data-testid={`lead-${l.id}`}
                >
                  <td className="px-4 py-3.5">
                    <div className="font-medium text-navy-700">
                      {l.firstName} {l.lastName}
                    </div>
                    {l.age && <div className="text-xs text-slate-500 mt-0.5">{l.age} anni</div>}
                  </td>
                  <td className="px-4 py-3.5">
                    <a href={`mailto:${l.email}`} className="text-slate-600 hover:text-navy-600 inline-flex items-center gap-1.5">
                      <Mail className="h-3.5 w-3.5 shrink-0" />
                      {l.email}
                    </a>
                  </td>
                  <td className="px-4 py-3.5 text-slate-600">
                    {l.phone ? (
                      <a href={`tel:${l.phone}`} className="hover:text-navy-600 inline-flex items-center gap-1.5">
                        <Phone className="h-3.5 w-3.5 shrink-0" />
                        {l.phone}
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-slate-600 whitespace-nowrap">{formatDateTimeIt(l.createdAt)}</td>
                  <td className="px-4 py-3.5">
                    {l.status === "new" ? (
                      <AdminBadge variant="warning">Nuova</AdminBadge>
                    ) : l.status === "contacted" ? (
                      <AdminBadge variant="success">Contattata</AdminBadge>
                    ) : (
                      <AdminBadge variant="draft">Archiviata</AdminBadge>
                    )}
                  </td>
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
                        data-testid={`lead-delete-${l.id}`}
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
                          <p className="mt-1 text-slate-600 whitespace-pre-line">{l.message}</p>
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <AdminEmptyState icon={SITE_ICONS.leads} title="Nessuna candidatura in questa vista." />
        )}
      </AdminTableWrap>
    </div>
  );
}
