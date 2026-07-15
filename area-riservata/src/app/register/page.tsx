import { redirect } from "next/navigation";

/** Registrazione solo da admin (codice meccanografico in anagrafica associati). */
export default function RegisterPage() {
  redirect("/login");
}
