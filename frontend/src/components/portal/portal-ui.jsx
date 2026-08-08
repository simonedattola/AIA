import { Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { PageTitle } from "@/design-system";

/** Stato vuoto in card — dimensione uniforme in tutto il portale. */
export function PortalEmptyState({ icon: Icon, children, className }) {
  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center gap-3 px-6 py-10 text-center min-h-[9.5rem]",
        className
      )}
    >
      {Icon && <Icon className="h-10 w-10 text-slate-300 shrink-0" aria-hidden />}
      <p className="text-slate-600 text-sm max-w-md">{children}</p>
    </div>
  );
}

export function PortalSearchBar({ value, onChange, placeholder = "Cerca…", testid }) {
  return (
    <div className="relative w-full max-w-md mb-6">
      <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-navy-400 focus:ring-2 focus:ring-navy-400/20"
        data-testid={testid}
      />
    </div>
  );
}

export function PortalPageHeader({ title, description, children }) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6 sm:mb-8">
      <div className="min-w-0">
        <PageTitle className="text-2xl sm:text-3xl font-bold tracking-tight mb-1">{title}</PageTitle>
        {description && <p className="text-slate-600 text-sm">{description}</p>}
      </div>
      {children && <div className="flex flex-wrap items-center gap-2 shrink-0 w-full sm:w-auto">{children}</div>}
    </header>
  );
}
