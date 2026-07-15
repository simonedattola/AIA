import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;

  const [documenti, quiz, rto, preferiti] = await Promise.all([
    prisma.documentoTecnico.findMany({ orderBy: { createdAt: "desc" }, include: { rto: true } }),
    prisma.quiz.findMany({ orderBy: { createdAt: "desc" } }),
    prisma.rTO.findMany({ orderBy: { data: "desc" } }),
    prisma.preferito.findMany({ where: { userId: auth.userId } }),
  ]);

  return NextResponse.json({ documenti, quiz, rto, preferiti });
}
