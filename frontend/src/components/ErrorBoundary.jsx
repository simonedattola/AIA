"""React error boundary for unexpected UI failures."""
import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    if (typeof console !== "undefined") {
      console.error("UI error:", error, info?.componentStack);
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-[50vh] flex items-center justify-center p-8 bg-slate-50">
          <div className="max-w-md text-center space-y-3">
            <h1 className="font-display text-2xl text-navy-700">Qualcosa è andato storto</h1>
            <p className="text-slate-600 text-sm">
              Si è verificato un errore inatteso. Ricarica la pagina o torna alla home.
            </p>
            <div className="flex gap-3 justify-center pt-2">
              <button
                type="button"
                className="px-4 py-2 rounded bg-navy-700 text-white text-sm"
                onClick={() => window.location.assign("/")}
              >
                Vai alla home
              </button>
              <button
                type="button"
                className="px-4 py-2 rounded border border-slate-300 text-sm"
                onClick={() => window.location.reload()}
              >
                Ricarica
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
