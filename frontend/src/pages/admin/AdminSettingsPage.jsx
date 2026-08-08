import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminSettings, adminPutSettings } from "../../lib/api";
import { Save, CheckCircle2 } from "lucide-react";
import { AdminPageHeader } from "../../components/admin/admin-ui";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { Button } from "@/design-system";

export default function AdminSettingsPage() {
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => { adminSettings().then(setForm); }, []);

  const save = async () => {
    setSaving(true);
    try {
      await adminPutSettings(form);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } finally {
      setSaving(false);
    }
  };

  if (!form) return <div>Caricamento…</div>;

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div data-testid="admin-settings">
      <AdminPageHeader
        title="Impostazioni sito"
        description={
          <>
            Contatti, social e testi globali (footer, statistiche). Homepage e menu di navigazione si gestiscono da{" "}
            <Link to={R.pagine} className="text-navy-600 font-medium hover:underline">Pagine</Link>.
          </>
        }
      >
        <Button onClick={save} disabled={saving} variant="primary" className="disabled:opacity-50" data-testid="settings-save">
          <Save className="h-4 w-4"/> {saved ? "Salvato!" : (saving ? "Salvataggio…" : "Salva")}
        </Button>
      </AdminPageHeader>

      {saved && <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 p-3 rounded mb-5 flex items-center gap-2"><CheckCircle2 className="h-4 w-4"/> Impostazioni aggiornate.</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-w-0">
        <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 min-w-0 overflow-hidden">
          <h2 className="font-display font-bold text-navy-700 mb-5">Identità sezione</h2>
          <Field label="Nome sito"><input value={form.siteName || ""} onChange={set("siteName")} className={inputCls} data-testid="settings-siteName"/></Field>
          <Field label="Tagline"><input value={form.tagline || ""} onChange={set("tagline")} className={inputCls}/></Field>
          <Field label="Testo footer (descrizione sezione)"><textarea rows={3} value={form.footerTagline || ""} onChange={set("footerTagline")} className={inputCls}/></Field>
          <Field label="Anno fondazione"><input value={form.foundedYear || ""} onChange={set("foundedYear")} className={inputCls}/></Field>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 min-w-0 overflow-hidden">
          <h2 className="font-display font-bold text-navy-700 mb-5">Contatti</h2>
          <Field label="Indirizzo"><input value={form.address || ""} onChange={set("address")} className={inputCls} data-testid="settings-address"/></Field>
          <Field label="Telefono"><input value={form.phone || ""} onChange={set("phone")} className={inputCls}/></Field>
          <Field label="Email"><input type="email" value={form.email || ""} onChange={set("email")} className={inputCls}/></Field>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 min-w-0 overflow-hidden">
          <h2 className="font-display font-bold text-navy-700 mb-5">Social</h2>
          <Field label="URL Facebook"><input value={form.facebookUrl || ""} onChange={set("facebookUrl")} className={inputCls}/></Field>
          <Field label="URL Instagram"><input value={form.instagramUrl || ""} onChange={set("instagramUrl")} className={inputCls}/></Field>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 min-w-0 overflow-hidden">
          <h2 className="font-display font-bold text-navy-700 mb-5">SEO & Link esterni</h2>
          <Field label="Embed mappa (iframe src)"><input value={form.mapEmbedUrl || ""} onChange={set("mapEmbedUrl")} className={inputCls}/></Field>
          <Field label="URL portale formazione (AIA)"><input value={form.formationPortalUrl || ""} onChange={set("formationPortalUrl")} className={inputCls}/></Field>
        </div>
      </div>
    </div>
  );
}

const inputCls = "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";
const Field = ({ label, children }) => (<label className="block mb-4 last:mb-0"><span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>{children}</label>);
