import { Component } from "react";
import { Link } from "react-router-dom";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { AlertCircle } from "lucide-react";
import { Button } from "@/design-system";

export default class AdminErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Admin area render error:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="app-canvas min-h-screen flex items-center justify-center bg-background p-6">
          <div className="max-w-md w-full rounded-xl border border-amber-200 bg-amber-50 text-amber-950 p-6 space-y-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden />
              <div>
                <h1 className="font-display font-bold text-lg text-navy-800">Errore nel pannello admin</h1>
                <p className="text-sm mt-2 text-amber-900/90">
                  Si è verificato un errore imprevisto durante il caricamento di questa pagina.
                  Prova a ricaricare o torna al login.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="primary" onClick={() => window.location.reload()}>
                Ricarica pagina
              </Button>
              <Button to={R.login} variant="outline">
                Torna al login
              </Button>
              <Link to="/" className="inline-flex items-center px-3 py-2 text-sm text-navy-700 hover:underline">
                Vai al sito pubblico
              </Link>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
