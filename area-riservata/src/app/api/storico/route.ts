import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";
import { currentSeason } from "@/lib/utils";

export async function GET(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const { searchParams } = new URL(req.url);
  const stagione = searchParams.get("stagione") || currentSeason();

  const gare = await prisma.gara.findMany({
    where: { userId: auth.userId, stagione },
    orderBy: { dataGara: "desc" },
  });

  const allGare = await prisma.gara.findMany({
    where: { userId: auth.userId },
    orderBy: { dataGara: "asc" },
  });

  const categorie = Array.from(new Set(allGare.map((g) => g.categoria)));
  const perMese: Record<string, number> = {};
  for (const g of allGare) {
    const key = `${g.dataGara.getFullYear()}-${String(g.dataGara.getMonth() + 1).padStart(2, "0")}`;
    perMese[key] = (perMese[key] || 0) + 1;
  }
  const chartData = Object.entries(perMese)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([mese, totale]) => ({ mese, totale }));

  return NextResponse.json({
    gare,
    stats: {
      totale: allGare.length,
      stagione: gare.length,
      categorie,
      mediaMese: allGare.length > 0 ? (allGare.length / Math.max(1, Object.keys(perMese).length)).toFixed(1) : "0",
    },
    chartData,
    stagioni: Array.from(new Set(allGare.map((g) => g.stagione))).sort().reverse(),
  });
}
