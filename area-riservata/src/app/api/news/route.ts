import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;

  const user = await prisma.user.findUnique({ where: { id: auth.userId } });
  if (!user) return NextResponse.json({ error: "Utente non trovato" }, { status: 404 });

  const nomeCompleto = `${user.nome} ${user.cognome}`;

  const [newsTecniche, successi, newsCategoria] = await Promise.all([
    prisma.newsTecnica.findMany({
      where: {
        OR: [
          { citazioni: { contains: user.nome } },
          { citazioni: { contains: nomeCompleto } },
        ],
      },
      orderBy: { createdAt: "desc" },
    }),
    prisma.successoPersonale.findMany({
      where: { userId: auth.userId },
      orderBy: { data: "desc" },
    }),
    user.categoria
      ? prisma.newsTecnica.findMany({
          where: { categoria: user.categoria },
          orderBy: { createdAt: "desc" },
        })
      : Promise.resolve([]),
  ]);

  const feed = [
    ...newsTecniche.map((n) => ({ ...n, tipo: "news" as const })),
    ...successi.map((s) => ({
      id: s.id,
      titolo: s.titolo,
      contenuto: s.contenuto,
      createdAt: s.data,
      tipo: "successo" as const,
    })),
    ...newsCategoria.map((n) => ({ ...n, tipo: "categoria" as const })),
  ].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  const seen = new Set<string>();
  const unique = feed.filter((item) => {
    if (seen.has(item.id)) return false;
    seen.add(item.id);
    return true;
  });

  return NextResponse.json(unique);
}
