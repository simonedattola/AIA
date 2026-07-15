import { Fragment, useEffect, useState, useMemo } from "react";
import { adminMessages, adminUpdateMessage, adminDeleteMessage } from "../../lib/api";
import { formatDateTimeIt } from "../../lib/format";
import { Trash2, Mail, ChevronDown, ChevronUp, Inbox } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import {
  AdminPageHeader,
  AdminTableWrap,
  adminTableHead,
  AdminFilterTabs,
  AdminBadge,
  AdminEmptyState,
} from "../../components/admin/admin-ui";

export default function AdminMessagesPage() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(null);
  const [filter, setFilter] = useState("all");

  const load = () => adminMessages().then(setItems);
  useEffect(() => {
    load();
  }, []);

  const newCount = items.filter((m) => m.status === "new").length;
  const filtered = useMemo(() => {
    if (filter === "new") return items.filter((m) => m.status === "new");
    if (filter === "read") return items.filter((m) => m.status !== "new");
    return items;
  }, [items, filter]);

  const setStatus = async (id, status) => {
    await adminUpdateMessage(id, { status });
    load();
  };

  const remove = async (id, name) => {
    if (!window.confirm(`Eliminare il messaggio di ${name}?`)) return;
    await adminDeleteMessage(id);
    load();
  };

  return (
    <div data-testid="admin-messages">
      <AdminPageHeader
        title="Messaggi dal sito"
        description="Richieste inviate dal modulo Contatti. I messaggi nuovi sono evidenziati in oro."
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
              <th className="px-4 py-3">Nome</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Oggetto</th>
              <th className="px-4 py-3">Data</th>
              <th className="px-4 py-3">Stato</th>
              <th className="px-4 py-3 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((m) => (
              <Fragment key={m.id}>
                <tr
                  className={`border-t border-slate-100 hover:bg-slate-50/80 ${m.status === "new" ? "bg-gold-50/30" : ""}`}
                  data-testid={`message-${m.id}`}
                >
                  <td className="px-4 py-3.5 font-medium text-navy-700">{m.name}</td>
                  <td className="px-4 py-3.5">
                    <a href={`mailto:${m.email}`} className="text-slate-600 hover:text-navy-600 inline-flex items-center gap-1.5">
                      <Mail className="h-3.5 w-3.5 shrink-0" />
                      {m.email}
                    </a>
                  </td>
                  <td className="px-4 py-3.5 text-slate-600">{m.subject || "—"}</td>
                  <td className="px-4 py-3.5 text-slate-600 whitespace-nowrap">{formatDateTimeIt(m.createdAt)}</td>
                  <td className="px-4 py-3.5">
                    {m.status === "new" ? (
                      <AdminBadge variant="warning">Nuovo</AdminBadge>
                    ) : (
                      <AdminBadge variant="draft">Letto</AdminBadge>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-1 justify-end">
                      <button
                        type="button"
                        onClick={() => {
                          setOpen(open === m.id ? null : m.id);
                          if (m.status === "new") setStatus(m.id, "read");
                        }}
                        className="p-2 text-slate-500 hover:bg-slate-100 rounded"
                      >
                        {open === m.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </button>
                      <button
                        type="button"
                        onClick={() => remove(m.id, m.name)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                        data-testid={`message-delete-${m.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
                {open === m.id && (
                  <tr className="border-t border-slate-100">
                    <td colSpan={6} className="px-4 py-4 bg-slate-50/80 text-sm text-slate-700 whitespace-pre-line">
                      {m.body}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <AdminEmptyState icon={SITE_ICONS.messagesSite} title="Nessun messaggio in questa vista." />
        )}
      </AdminTableWrap>
    </div>
  );
}
