import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "./auth";

export async function getSession() {
  return getServerSession(authOptions);
}

export async function requireSession() {
  const session = await getSession();
  if (!session?.user?.id) redirect("/login");
  return session;
}

export async function requireAdminOrObserver() {
  const session = await requireSession();
  const ruolo = session.user.ruolo;
  if (ruolo !== "ADMIN" && ruolo !== "OSSERVATORE") {
    redirect("/dashboard");
  }
  return session;
}

export function isStaff(ruolo?: string) {
  return ruolo === "ADMIN" || ruolo === "OSSERVATORE";
}

export function canMessage(ruolo?: string) {
  return ruolo === "ADMIN" || ruolo === "OSSERVATORE" || ruolo === "CONSIGLIO";
}
