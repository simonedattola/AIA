/** Password predefinita: nome.cognome (minuscolo, senza accenti). */
export function defaultPassword(nome: string, cognome: string): string {
  const norm = (s: string) =>
    s
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  return `${norm(nome)}.${norm(cognome)}`;
}
