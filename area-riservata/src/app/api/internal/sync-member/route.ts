import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { defaultPassword } from "@/lib/password";

const schema = z.object({
  codiceMeccanografico: z.string().min(1),
  nome: z.string().min(1),
  cognome: z.string().min(1),
  email: z.string().email().optional().or(z.literal("")),
  telefono: z.string().optional(),
  categoria: z.string().optional(),
  memberRole: z.string().optional(),
  foto: z.string().optional(),
});

function mapRuolo(memberRole?: string): string {
  const r = (memberRole || "arbitro").toLowerCase();
  if (r === "consiglio_direttivo") return "CONSIGLIO";
  if (r === "osservatore") return "OSSERVATORE";
  return "ASSOCIATO";
}

export async function POST(req: Request) {
  const secret = req.headers.get("x-portal-sync-secret");
  if (!secret || secret !== process.env.PORTAL_SYNC_SECRET) {
    return NextResponse.json({ error: "Non autorizzato" }, { status: 401 });
  }

  try {
    const body = schema.parse(await req.json());
    const codice = body.codiceMeccanografico.trim();
    const pwd = defaultPassword(body.nome, body.cognome);
    const passwordHash = await bcrypt.hash(pwd, 10);
    const ruolo = mapRuolo(body.memberRole);

    const user = await prisma.user.upsert({
      where: { codiceMeccanografico: codice },
      create: {
        codiceMeccanografico: codice,
        nome: body.nome.trim(),
        cognome: body.cognome.trim(),
        email: body.email || null,
        telefono: body.telefono || null,
        categoria: body.categoria || null,
        ruolo,
        foto: body.foto || null,
        passwordHash,
      },
      update: {
        nome: body.nome.trim(),
        cognome: body.cognome.trim(),
        email: body.email || null,
        telefono: body.telefono || null,
        categoria: body.categoria || null,
        ruolo,
        foto: body.foto || undefined,
      },
    });

    return NextResponse.json({
      id: user.id,
      codiceMeccanografico: user.codiceMeccanografico,
      defaultPasswordHint: pwd,
      created: true,
    });
  } catch (e) {
    if (e instanceof z.ZodError) {
      return NextResponse.json({ error: e.flatten() }, { status: 400 });
    }
    return NextResponse.json({ error: "Sync fallita" }, { status: 500 });
  }
}
