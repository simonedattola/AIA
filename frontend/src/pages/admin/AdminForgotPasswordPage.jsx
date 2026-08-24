import { useState } from "react";
import { Link } from "react-router-dom";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../../lib/brand";
import { adminForgotPassword } from "../../lib/api";
import { apiErrorMessage } from "../../lib/toast";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { Mail, ArrowLeft } from "lucide-react";
import { Button } from "@/design-system";

export default function AdminForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await adminForgotPassword(email.trim());
      setDone(true);
    } catch (err) {
      setError(apiErrorMessage(err, "Impossibile inviare la richiesta. Riprova."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-canvas min-h-screen flex items-center justify-center bg-pattern-stadio p-4" data-testid="admin-forgot-password-page">
      <div className="relative bg-white rounded-lg shadow-2xl w-full max-w-md p-10 z-10">
        <div className="flex items-center gap-3 mb-6">
          <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.lg} />
          <div>
            <div className="font-display text-xl font-bold text-navy-700">Password dimenticata</div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500 font-medium">Pannello amministrativo</div>
          </div>
        </div>

        {done ? (
          <div className="space-y-4">
            <p className="text-sm text-slate-700 leading-relaxed">
              Se l&apos;indirizzo è registrato come amministratore, riceverai a breve un&apos;email con un link
              per scegliere una nuova password (controlla anche lo spam).
            </p>
            <Link to={R.login} className="inline-flex items-center gap-2 text-sm text-navy-700 hover:text-navy-900 font-medium">
              <ArrowLeft className="h-4 w-4" /> Torna al login
            </Link>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-5">
            <p className="text-sm text-slate-600">
              Inserisci l&apos;email amministrativa della sezione. Ti invieremo un link valido per un&apos;ora.
            </p>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-sm">{error}</div>
            )}
            <label className="block">
              <span className="block text-sm font-medium text-slate-700 mb-1.5">Email</span>
              <div className="relative">
                <Mail className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  required
                  type="email"
                  autoComplete="username"
                  placeholder="es. legnano@aia-figc.it"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none"
                  data-testid="admin-forgot-email"
                />
              </div>
            </label>
            <Button disabled={loading} type="submit" variant="primary" className="w-full justify-center">
              {loading ? "Invio in corso…" : "Invia link di reset"}
            </Button>
            <Link to={R.login} className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-navy-700">
              <ArrowLeft className="h-4 w-4" /> Torna al login
            </Link>
          </form>
        )}
      </div>
    </div>
  );
}
