import { ROLE_FILTERS } from "../../lib/memberRoles";

const chipBase =
  "px-2.5 py-1 rounded-full text-xs font-medium border transition-colors";
const chipOff = "border-slate-200 bg-white text-slate-600 hover:border-navy-300 hover:text-navy-700";
const chipOn = "border-navy-600 bg-navy-50 text-navy-800";

/** Multi-select chip picker for AE/AA/… CDS/Collaboratori/ORS. */
export function RoleGroupPicker({ value = [], onChange, label = "Gruppi ruolo", hint }) {
  const selected = new Set(value || []);
  const options = ROLE_FILTERS.filter((f) => f.value);

  const toggle = (code) => {
    const next = new Set(selected);
    if (next.has(code)) next.delete(code);
    else next.add(code);
    onChange(Array.from(next));
  };

  return (
    <div data-testid="role-group-picker">
      <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
      {hint && <span className="block text-xs text-slate-400 mb-2">{hint}</span>}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            data-testid={`role-group-${opt.value}`}
            className={`${chipBase} ${selected.has(opt.value) ? chipOn : chipOff}`}
            onClick={() => toggle(opt.value)}
            aria-pressed={selected.has(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function roleGroupsSummary(groups) {
  const list = (groups || []).filter(Boolean);
  if (!list.length) return "";
  const labels = ROLE_FILTERS.filter((f) => list.includes(f.value)).map((f) => f.label);
  return labels.length ? labels.join(", ") : list.join(", ");
}
