import { useState, useEffect } from "react";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../../lib/brand";
import { useNavigate, Navigate } from "react-router-dom";
import { adminLogin } from "../../lib/api";
import { apiErrorMessage } from "../../lib/toast";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { Shield, Lock, Mail } from "lucide-react";
import { Button } from "@/design-system";
import { AdminLoading } from "../../components/admin/admin-ui";

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState({ ready: false, hasToken: false });

  useEffect(() => {
    setSession({ ready: true, hasToken: !!localStorage.getItem("aia_token") });
  }, []);

  if (!session.ready) {
    return (
      <div className="app-canvas min-h-screen flex items-center justify-center bg-pattern-stadio p-4">
        <AdminLoading label="Caricamento…" />
      </div>
    );
  }

  if (session.hasToken) {
    return <Navigate to={R.dashboard} replace />;
  }

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await adminLogin(form.email, form.password);
      localStorage.setItem("aia_token", res.token);
      localStorage.setItem("aia_admin", JSON.stringify(res.admin));
      navigate(R.dashboard);
    } catch (err) {
      setError(apiErrorMessage(err, "Credenziali non valide"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-canvas min-h-screen flex items-center justify-center bg-pattern-stadio p-4" data-testid="admin-login-page">
      <div className="absolute inset-0 z-0 opacity-25">
        <img src="https://images.unsplash.com/photo-1551958219-acbc608c6377?q=85&w=2000&auto=format&fit=crop" alt="" className="w-full h-full object-cover"/>
      </div>
      <div className="relative bg-white rounded-lg shadow-2xl w-full max-w-md p-10 z-10">
        <div className="flex items-center gap-3 mb-8">
          <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.lg} />
          <div>
            <div className="font-display text-xl font-bold text-navy-700">AIA Legnano</div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500 font-medium">Pannello amministrativo</div>
          </div>
        </div>

        <div className="flex items-center gap-2 px-4 py-3 bg-gold-50 border border-gold-200 rounded-md text-sm text-gold-800 mb-6">
          <Shield className="h-4 w-4 flex-shrink-0" />
          Accesso riservato agli amministratori autorizzati.
        </div>

        <form onSubmit={submit} className="space-y-5" data-testid="admin-login-form">
          {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-sm" data-testid="admin-login-error">{error}</div>}
          <label className="block">
            <span className="block text-sm font-medium text-slate-700 mb-1.5">Email</span>
            <div className="relative">
              <Mail className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                data-testid="admin-login-email"
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none"
              />
            </div>
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-slate-700 mb-1.5">Password</span>
            <div className="relative">
              <Lock className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                data-testid="admin-login-password"
                required
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none"
              />
            </div>
          </label>
          <Button
            disabled={loading}
            type="submit"
            variant="primary"
            className="w-full justify-center"
            data-testid="admin-login-submit"
          >
            {loading ? "Accesso in corso…" : "Accedi"}
          </Button>
        </form>
      </div>
    </div>
  );
}
