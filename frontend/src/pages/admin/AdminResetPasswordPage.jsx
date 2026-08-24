import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../../lib/brand";
import { adminResetPassword } from "../../lib/api";
import { apiErrorMessage } from "../../lib/toast";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { Lock, ArrowLeft } from "lucide-react";
import { Button } from "@/design-system";

export default function AdminResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = useMemo(() => (searchParams.get("token") || "").trim(), [searchParams]);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!token) {
    return (
      <div className="app-canvas min-h-screen flex items-center justify-center bg-pattern-stadio p-4">
        <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-10 text-center space-y-4">
          <p className="text-sm text-slate-700">Link non valido o incompleto.</p>
          <Link to={R.forgotPassword} className="text-navy-700 font-medium text-sm hover:underline">
            Richiedi un nuovo link
          </Link>
        </div>
      </div>
    );
  }

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("La password deve avere almeno 8 caratteri.");
      return;
    }
    if (password !== confirm) {
      setError("Le password non coincidono.");
      return;
    }
    setLoading(true);
    try {
      await adminResetPassword(token, password);
      navigate(R.login, { replace: true, state: { resetOk: true } });
    } catch (err) {
      setError(apiErrorMessage(err, "Impossibile reimpostare la password."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-canvas min-h-screen flex items-center justify-center bg-pattern-stadio p-4" data-testid="admin-reset-password-page">
      <div className="relative bg-white rounded-lg shadow-2xl w-full max-w-md p-10 z-10">
        <div className="flex items-center gap-3 mb-6">
          <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.lg} />
          <div>
            <div className="font-display text-xl font-bold text-navy-700">Nuova password</div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500 font-medium">Pannello amministrativo</div>
          </div>
        </div>

        <form onSubmit={submit} className="space-y-5">
          <p className="text-sm text-slate-600">Scegli una password sicura (minimo 8 caratteri).</p>
          {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-sm">{error}</div>}
          <label className="block">
            <span className="block text-sm font-medium text-slate-700 mb-1.5">Nuova password</span>
            <div className="relative">
              <Lock className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                required
                type="password"
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none"
                data-testid="admin-reset-password"
              />
            </div>
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-slate-700 mb-1.5">Conferma password</span>
            <div className="relative">
              <Lock className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                required
                type="password"
                minLength={8}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none"
              />
            </div>
          </label>
          <Button disabled={loading} type="submit" variant="primary" className="w-full justify-center">
            {loading ? "Salvataggio…" : "Salva password"}
          </Button>
          <Link to={R.login} className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-navy-700">
            <ArrowLeft className="h-4 w-4" /> Torna al login
          </Link>
        </form>
      </div>
    </div>
  );
}
