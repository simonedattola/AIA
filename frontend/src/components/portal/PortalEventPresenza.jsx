import { Check, HelpCircle, Loader2, Lock, X } from "lucide-react";

export const PRESENZA_OPTIONS = [
  { value: "PRESENTE", label: "Presente", icon: Check },
  { value: "ASSENTE", label: "Assente", icon: X },
  { value: "IN_DUBBIO", label: "In dubbio", icon: HelpCircle },
];

export const PRESENZA_CONFIRM_OPTIONS = PRESENZA_OPTIONS.filter((p) => p.value !== "IN_DUBBIO");

export const PRESENZA_STATO_LABEL = {
  PRESENTE: "Presente",
  ASSENTE: "Assente",
  IN_DUBBIO: "In dubbio",
  NON_RISPOSTO: "Da confermare",
};

function isPresenzaLocked(stato) {
  return stato === "PRESENTE" || stato === "ASSENTE";
}

function PresenzaButtons({ options, saving, onSelect }) {
  return (
    <>
      {options.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          disabled={saving}
          onClick={() => onSelect(value)}
          className="w-full inline-flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-medium border transition-colors disabled:opacity-60 border-slate-200 bg-white text-slate-700 hover:border-navy-300"
        >
          {saving ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
          ) : (
            <Icon className="h-3.5 w-3.5 shrink-0" />
          )}
          {label}
        </button>
      ))}
    </>
  );
}

export function PortalPresenzaPanel({ event, saving, onSetStato }) {
  const stato = event.mioStato || "NON_RISPOSTO";
  const locked = isPresenzaLocked(stato);

  if (locked) {
    const cfg = PRESENZA_OPTIONS.find((p) => p.value === stato);
    const Icon = cfg?.icon || Lock;
    return (
      <div className="h-full flex flex-col items-center justify-center text-center px-3 py-4 bg-slate-50/80">
        <Lock className="h-4 w-4 text-slate-400 mb-2 shrink-0" aria-hidden />
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-semibold border ${
            stato === "PRESENTE"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-red-50 text-red-800 border-red-200"
          }`}
        >
          <Icon className="h-3.5 w-3.5 shrink-0" />
          {PRESENZA_STATO_LABEL[stato] || stato}
        </span>
        <p className="text-[10px] text-slate-500 mt-2 leading-snug">Confermata</p>
      </div>
    );
  }

  if (stato === "IN_DUBBIO") {
    return (
      <div className="h-full flex flex-col justify-center gap-1.5 p-3 bg-slate-50/80">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-0.5 text-center">
          Presenza
        </p>
        <span className="inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-semibold border bg-amber-50 text-amber-900 border-amber-200">
          <HelpCircle className="h-3.5 w-3.5 shrink-0" />
          In dubbio
        </span>
        <p className="text-[10px] text-slate-500 text-center leading-snug">Conferma presente o assente</p>
        <PresenzaButtons
          options={PRESENZA_CONFIRM_OPTIONS}
          saving={saving}
          onSelect={(value) => onSetStato(event.id, value)}
        />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col justify-center gap-1.5 p-3 bg-slate-50/80">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-0.5 text-center">
        Presenza
      </p>
      <PresenzaButtons
        options={PRESENZA_OPTIONS}
        saving={saving}
        onSelect={(value) => onSetStato(event.id, value)}
      />
    </div>
  );
}
