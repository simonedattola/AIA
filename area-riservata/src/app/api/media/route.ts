import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const media = await prisma.media.findMany({
    where: { userId: auth.userId },
    orderBy: { createdAt: "desc" },
  });
  const preferiti = await prisma.preferito.findMany({
    where: { userId: auth.userId, tipo: "MEDIA" },
  });
  return NextResponse.json({ media, preferiti });
}
