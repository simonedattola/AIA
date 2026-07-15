import { useEffect, useState } from "react";
import { adminMembers } from "../../lib/api";

function memberHaystack(m) {
  return `${m.firstName} ${m.lastName} ${m.category || ""} ${m.meccanografico || ""} ${m.slug || ""}`.toLowerCase();
}

function filterMembers(members, q, { excludeIds = [], limit = 8, requireQuery = false } = {}) {
  const s = q.trim().toLowerCase();
  if (requireQuery && !s) return [];
  return members
    .filter((m) => {
      if (excludeIds.includes(m.id)) return false;
      if (!s) return !requireQuery;
      return memberHaystack(m).includes(s);
    })
    .slice(0, limit);
}

/** Multi-select associati. Con searchOnly: solo barra di ricerca + risultati al volo. */
export function MemberMultiSelect({
  value = [],
  onChange,
  label = "Associati collegati",
  hint = "",
  searchOnly = false,
  members: membersProp,
}) {
  const [members, setMembers] = useState([]);
  const [q, setQ] = useState("");

  useEffect(() => {
    if (membersProp) {
      setMembers(membersProp);
      return;
    }
    adminMembers().then(setMembers).catch(() => {});
  }, [membersProp]);

  const selected = Array.isArray(value) ? value : [];
  const toggle = (id) => {
    if (selected.includes(id)) onChange(selected.filter((x) => x !== id));
    else onChange([...selected, id]);
  };

  const addFromSearch = (id) => {
    if (!selected.includes(id)) onChange([...selected, id]);
    setQ("");
  };

  const filtered = filterMembers(members, q, { requireQuery: searchOnly });
  const searchResults = searchOnly
    ? filtered.filter((m) => !selected.includes(m.id)).slice(0, 8)
    : filtered;

  const inputCls = searchOnly
    ? "w-full px-2 py-1.5 border border-slate-300 rounded-md text-xs focus:border-navy-600 focus:outline-none"
    : "w-full px-3 py-2 border border-slate-300 rounded-md text-sm mb-2 focus:border-navy-600 focus:outline-none";

  return (
    <div>
      <span className={`block font-medium text-slate-700 ${searchOnly ? "text-xs mb-1" : "text-sm mb-1.5"}`}>
        {label}
      </span>
      {hint && !searchOnly && <p className="text-xs text-slate-500 mb-2">{hint}</p>}
      {selected.length > 0 && (
        <div className={`flex flex-wrap gap-1.5 ${searchOnly ? "mb-1.5" : "mb-2"}`}>
          {selected.map((id) => {
            const m = members.find((x) => x.id === id);
            if (!m) return null;
            return (
              <button
                key={id}
                type="button"
                onClick={() => toggle(id)}
                className="inline-flex items-center gap-1 px-2 py-1 bg-navy-50 text-navy-700 rounded text-xs font-medium hover:bg-navy-100"
              >
                {m.firstName} {m.lastName} ×
              </button>
            );
          })}
        </div>
      )}
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Cerca associato…"
        className={inputCls}
      />
      {searchOnly ? (
        q.trim() && (
          <div className="mt-1.5 border border-slate-200 rounded-md divide-y divide-slate-100 overflow-hidden bg-white shadow-sm">
            {searchResults.length === 0 ? (
              <p className="px-2 py-1.5 text-xs text-slate-500">Nessun risultato</p>
            ) : (
              searchResults.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => addFromSearch(m.id)}
                  className="w-full text-left px-2 py-1.5 hover:bg-slate-50 text-xs"
                >
                  <span className="text-navy-700 font-medium">
                    {m.firstName} {m.lastName}
                  </span>
                  {m.category && <span className="text-slate-400 ml-1">{m.category}</span>}
                </button>
              ))
            )}
          </div>
        )
      ) : (
        <div className="max-h-40 overflow-y-auto border border-slate-200 rounded-md divide-y divide-slate-100">
          {filtered.length === 0 ? (
            <p className="px-3 py-2 text-sm text-slate-500">Nessun associato</p>
          ) : (
            filtered.map((m) => (
              <label
                key={m.id}
                className="flex items-center gap-2 px-3 py-2 hover:bg-slate-50 cursor-pointer text-sm"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(m.id)}
                  onChange={() => toggle(m.id)}
                  className="rounded border-slate-300 text-navy-600"
                />
                <span className="text-navy-700 font-medium">
                  {m.firstName} {m.lastName}
                </span>
                {m.category && <span className="text-xs text-slate-400">{m.category}</span>}
              </label>
            ))
          )}
        </div>
      )}
      {!searchOnly && (
        <p className="text-xs text-slate-400 mt-1">Compaiono nel profilo pubblico dell&apos;associato.</p>
      )}
    </div>
  );
}

/** Select singolo associato con ricerca. */
export function MemberSingleSelect({
  value,
  onChange,
  label = "Associato collegato",
  members: membersProp,
  testId,
}) {
  const [members, setMembers] = useState([]);
  const [q, setQ] = useState("");

  useEffect(() => {
    if (membersProp) {
      setMembers(membersProp);
      return;
    }
    adminMembers().then(setMembers).catch(() => {});
  }, [membersProp]);

  const selected = value ? members.find((m) => m.id === value) : null;
  const results = filterMembers(members, q, { excludeIds: value ? [value] : [], requireQuery: true });

  const pick = (id) => {
    onChange(id);
    setQ("");
  };

  return (
    <div data-testid={testId}>
      {label ? (
        <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
      ) : null}
      {selected && (
        <div className="mb-2">
          <button
            type="button"
            onClick={() => onChange(null)}
            className="inline-flex items-center gap-1 px-2 py-1 bg-navy-50 text-navy-700 rounded text-xs font-medium hover:bg-navy-100"
          >
            {selected.firstName} {selected.lastName} ×
          </button>
        </div>
      )}
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={selected ? "Cerca per sostituire…" : "Cerca associato…"}
        className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:border-navy-600 focus:outline-none"
      />
      {q.trim() && (
        <div className="mt-1.5 border border-slate-200 rounded-md divide-y divide-slate-100 overflow-hidden bg-white shadow-sm">
          {results.length === 0 ? (
            <p className="px-3 py-2 text-sm text-slate-500">Nessun risultato</p>
          ) : (
            results.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => pick(m.id)}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 text-sm"
              >
                <span className="text-navy-700 font-medium">
                  {m.firstName} {m.lastName}
                </span>
                {m.category && <span className="text-xs text-slate-400 ml-1">{m.category}</span>}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
