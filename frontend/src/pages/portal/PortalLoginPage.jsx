import { useState } from "react";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../../lib/brand";
import { useNavigate, Navigate, Link } from "react-router-dom";
import { portalLogin } from "../../lib/portal-api";
import { PORTAL_ROUTES as R } from "../../lib/appRoutes";
import { Lock, Hash } from "lucide-react";
import { Button } from "@/design-system";

export default function PortalLoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ codice: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (localStorage.getItem("aia_member_token")) {
    return <Navigate to={R.root} replace />;
  }

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await portalLogin(form.codice.trim(), form.password);
      localStorage.setItem("aia_member_token", res.token);
      localStorage.setItem("aia_member", JSON.stringify(res.member));
      navigate(R.root);
    } catch (err) {
      setError(err?.response?.data?.detail || "Credenziali non valide");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-canvas relative min-h-screen flex items-center justify-center bg-pattern-stadio p-4" data-testid="portal-login-page">
      <div className="absolute inset-0 z-0 opacity-25" aria-hidden="true">
        <img
          src="https://images.unsplash.com/photo-1551958219-acbc608c6377?q=85&w=2000&auto=format&fit=crop"
          alt=""
          className="w-full h-full object-cover"
        />
      </div>
      <div className="relative bg-white rounded-lg shadow-2xl w-full max-w-md p-8 sm:p-10 z-10">
        <div className="flex items-center gap-3 mb-8">
          <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.lg} />
          <div>
            <div className="font-display text-xl font-bold text-navy-700">Area Associati</div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500 font-medium">AIA Legnano</div>
          </div>
        </div>
        <p className="text-sm text-slate-600 mb-6">
          Accedi con il <strong>codice meccanografico</strong> e la password fornita dalla sezione
          (inizialmente <code className="text-navy-700">nome.cognome</code>).
        </p>
        <form onSubmit={submit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-sm">{error}</div>
          )}
          <label className="block">
            <span className="block text-sm font-medium text-slate-700 mb-1">Codice meccanografico</span>
            <div className="relative">
              <Hash className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                required
                value={form.codice}
                onChange={(e) => setForm({ ...form, codice: e.target.value })}
                className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:ring-2 focus:ring-navy-500"
                placeholder="es. 12345678"
              />
            </div>
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-slate-700 mb-1">Password</span>
            <div className="relative">
              <Lock className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                required
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:ring-2 focus:ring-navy-500"
              />
            </div>
          </label>
          <Button type="submit" disabled={loading} variant="primary" className="w-full justify-center">
            {loading ? "Accesso…" : "Accedi"}
          </Button>
        </form>
        <p className="text-center text-sm text-slate-500 mt-6">
          <Link to="/" className="text-navy-600 hover:underline">← Torna al sito</Link>
        </p>
      </div>
    </div>
  );
}
