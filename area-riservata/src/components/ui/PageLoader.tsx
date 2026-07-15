export function PageLoader({ label = "Caricamento..." }: { label?: string }) {
  return <p className="py-12 text-center text-slate-500">{label}</p>;
}

export function PageError({ message = "Impossibile caricare i dati. Riprova." }: { message?: string }) {
  return <p className="py-12 text-center text-red-600">{message}</p>;
}
