import { useEffect, useState, useMemo } from "react";
import { fetchMembers } from "../lib/api";
import { PageHeader } from "./NewsListPage";
import { Search, Users, X } from "lucide-react";
import { Link } from "react-router-dom";
import MediaImage from "../components/MediaImage";
import { Card, CardTitle, FilterPill } from "@/design-system";

const KINDS = [
  { key: "", label: "Tutti" },
  { key: "associato", label: "Arbitri" },
  { key: "tutor", label: "Tutor" },
];

export default function AssociatiPage() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [kind, setKind] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = { limit: 500 };
    if (kind) params.kind = kind;
    fetchMembers(params).then((d) => {
      setItems(d);
      setLoading(false);
    });
  }, [kind]);

  const filtered = useMemo(() => {
    const s = search.trim().toLowerCase();
    if (!s) return items;
    return items.filter((m) =>
      `${m.firstName} ${m.lastName} ${m.category} ${m.role}`.toLowerCase().includes(s)
    );
  }, [items, search]);

  return (
    <div data-testid="associati-page">
      <PageHeader
        eyebrow="Sezione Legnano"
        title="Associati"
        description="Arbitri, assistenti e tutor della sezione. Gli osservatori (OA/OT) sono nell'organigramma in Chi siamo."
      />

      <section className="site-section bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-200">
            <div className="flex items-center gap-2">
              {KINDS.map((k) => (
                <FilterPill
                  key={k.key || "all"}
                  active={kind === k.key}
                  onClick={() => setKind(k.key)}
                  data-testid={`associati-filter-${k.key || "all"}`}
                >
                  {k.label}
                </FilterPill>
              ))}
            </div>
            <div className="relative w-full md:w-80">
              <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cerca per nome o categoria…"
                className="w-full pl-9 pr-9 py-2 border border-slate-300 rounded-md text-sm focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none"
                data-testid="associati-search"
              />
              {search && (
                <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          <div className="text-sm text-slate-500 mb-6">
            <Users className="h-4 w-4 inline mr-1" /> {filtered.length} associati visualizzati
          </div>

          {loading ? (
            <p className="text-slate-500">Caricamento…</p>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {filtered.map((m) => (
                <Card
                  key={m.id}
                  as={Link}
                  to={`/associati/${m.slug}`}
                  interactive
                  padding="default"
                  className="hover:border-navy-600 block"
                  data-testid={`member-card-${m.slug}`}
                >
                  {m.photoUrl ? (
                    <MediaImage src={m.photoUrl} alt="" className="w-14 h-14 rounded-full object-cover border-2 border-slate-200 mb-4"/>
                  ) : (
                    <div className="w-14 h-14 rounded-full bg-navy-600 text-white flex items-center justify-center font-display font-bold text-lg mb-4">
                      {m.firstName[0]}{m.lastName[0]}
                    </div>
                  )}
                  <CardTitle as="h3" className="text-lg leading-tight">
                    {m.firstName} {m.lastName}
                  </CardTitle>
                  <div className="mt-2 text-xs uppercase tracking-wider text-gold-500 font-semibold">{m.role}</div>
                  <div className="text-sm text-slate-600 mt-1">{m.category}</div>
                  {m.yearStart && (
                    <div className="text-xs text-slate-400 mt-2">In sezione dal {m.yearStart}</div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
