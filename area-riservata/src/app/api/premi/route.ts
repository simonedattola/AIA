import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const traguardi = await prisma.traguardo.findMany({
    where: { userId: auth.userId },
    orderBy: { data: "desc" },
  });
  return NextResponse.json(traguardi);
}
