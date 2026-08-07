import { AlertCircle, ArrowRight, Inbox, Loader2, Save, X } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button, Card, PageTitle, SubsectionTitle } from "@/design-system";

export function AdminLoading({ label = "Caricamento…" }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-slate-500" data-testid="admin-loading">
      <Loader2 className="h-5 w-5 animate-spin" />
      <span>{label}</span>
    </div>
  );
}

export function AdminPageHeader({ title, description, children }) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
      <div className="min-w-0">
        <PageTitle className="text-3xl mb-1">{title}</PageTitle>
        {description && <p className="text-slate-600 text-sm">{description}</p>}
      </div>
      {children && <div className="flex flex-wrap items-center gap-2 shrink-0">{children}</div>}
    </header>
  );
}

export function AdminAlert({ variant = "info", title, children, action }) {
  const styles = {
    info: "bg-navy-50 border-navy-200 text-navy-800",
    warning: "bg-amber-50 border-amber-200 text-amber-900",
    success: "bg-emerald-50 border-emerald-200 text-emerald-800",
  };
  return (
    <div className={`rounded-lg border p-4 mb-6 flex flex-col sm:flex-row sm:items-center gap-3 ${styles[variant] || styles.info}`}>
      <div className="flex gap-3 flex-1 min-w-0">
        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 opacity-80" />
        <div>
          {title && <p className="font-semibold text-sm">{title}</p>}
          {children && <div className="text-sm mt-0.5 opacity-90">{children}</div>}
        </div>
      </div>
      {action}
    </div>
  );
}

export function AdminPanel({ children, className = "" }) {
  return (
    <Card padding="none" radius="lg" className={className}>
      {children}
    </Card>
  );
}

export function AdminTableWrap({ children }) {
  return (
    <AdminPanel className="overflow-hidden">
      <div className="overflow-x-auto">{children}</div>
    </AdminPanel>
  );
}

export const adminTableHead = "bg-slate-50 text-xs uppercase text-slate-500 text-left tracking-wide";

export function AdminStatCard({ icon, label, value, sub, href, highlight, testid }) {
  return (
    <Card
      as={Link}
      to={href}
      interactive
      padding="default"
      className={cn(
        "block transition-shadow",
        highlight ? "border-gold-400 ring-2 ring-gold-400/20 hover:border-gold-400" : "hover:border-navy-300"
      )}
      data-testid={testid}
    >
      <div className="flex items-center justify-between mb-3">
        <div
          className={`w-10 h-10 rounded-md flex items-center justify-center ${
            highlight ? "bg-gold-100 text-gold-700" : "bg-navy-50 text-navy-600"
          }`}
        >
          {icon}
        </div>
        <ArrowRight className="h-4 w-4 text-slate-300" />
      </div>
      <SubsectionTitle as="div" className="font-bold">
        {value ?? 0}
      </SubsectionTitle>
      <div className="text-sm text-slate-600 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </Card>
  );
}

export function AdminQuickLink({ to, children, primary }) {
  return (
    <Button to={to} variant={primary ? "primary" : "outline"} size="sm">
      {children}
    </Button>
  );
}

export const adminInputCls =
  "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";

export function AdminField({ label, children, hint }) {
  return (
    <label className="block mb-4 last:mb-0">
      <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
      {hint && <span className="block text-xs text-slate-400 mb-1">{hint}</span>}
      {children}
    </label>
  );
}

/** Modale creazione/modifica — stesso pattern della pagina Associati. */
export function AdminFormModal({
  open,
  title,
  onClose,
  onSave,
  saveLabel = "Salva",
  saving = false,
  saveDisabled = false,
  children,
  maxWidth = "max-w-3xl",
  testid,
  hideFooter = false,
  footer,
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 overflow-y-auto"
      data-testid={testid}
      role="dialog"
      aria-modal="true"
      aria-labelledby={testid ? `${testid}-title` : undefined}
    >
      <div className={`bg-white rounded-lg ${maxWidth} w-full max-h-[92vh] flex flex-col my-8 shadow-xl`}>
        <div className="sticky top-0 bg-white border-b border-slate-200 p-5 flex items-center justify-between z-10 shrink-0 rounded-t-lg">
          <h2
            id={testid ? `${testid}-title` : undefined}
            className="font-display text-xl font-bold text-navy-700"
          >
            {title}
          </h2>
          <button type="button" onClick={onClose} className="p-2 text-slate-400 hover:bg-slate-100 rounded" aria-label="Chiudi">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-6 space-y-5 flex-1 overflow-y-auto">{children}</div>
        {!hideFooter && (
          <div className="sticky bottom-0 bg-white border-t border-slate-200 p-5 flex justify-end gap-3 shrink-0 rounded-b-lg">
            {footer ?? (
              <>
                <Button type="button" onClick={onClose} variant="outline">
                  Annulla
                </Button>
                <Button
                  type="button"
                  onClick={onSave}
                  disabled={saving || saveDisabled}
                  variant="primary"
                  className="disabled:opacity-50"
                >
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}{" "}
                  {saveLabel}
                </Button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/** Stato vuoto in card — stessa dimensione del portale associati. */
export function AdminEmptyState({ icon: Icon = Inbox, title = "Nessun elemento", children, className }) {
  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center gap-3 px-6 py-10 text-center min-h-[9.5rem]",
        className
      )}
    >
      <Icon className="h-10 w-10 text-slate-300 shrink-0" aria-hidden />
      <p className="text-slate-600 text-sm max-w-md">{title}</p>
      {children && <p className="text-slate-500 text-sm max-w-md">{children}</p>}
    </div>
  );
}

export function AdminSearchBar({ value, onChange, placeholder = "Cerca…", testid }) {
  return (
    <div className="relative w-full max-w-sm">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`${adminInputCls} pl-9`}
        data-testid={testid}
      />
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">⌕</span>
    </div>
  );
}

export function AdminFilterTabs({ tabs, active, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => onChange(t.id)}
          className={`px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors ${
            active === t.id
              ? "bg-navy-600 text-white"
              : "bg-white border border-slate-200 text-slate-700 hover:border-navy-400"
          }`}
        >
          {t.label}
          {t.count != null && <span className="ml-1.5 opacity-80">({t.count})</span>}
        </button>
      ))}
    </div>
  );
}

const BADGE_STYLES = {
  success: "bg-emerald-50 text-emerald-700",
  draft: "bg-slate-100 text-slate-600",
  warning: "bg-amber-50 text-amber-800",
  info: "bg-navy-50 text-navy-700",
  portal: "bg-violet-50 text-violet-700",
};

export function AdminBadge({ variant = "info", children }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${BADGE_STYLES[variant] || BADGE_STYLES.info}`}>
      {children}
    </span>
  );
}
