import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { requireAdminOrObserver } from "@/lib/session";
import { formatDateTime } from "@/lib/utils";

export default async function AdminEventiPage() {
  await requireAdminOrObserver();
  const eventi = await prisma.evento.findMany({ orderBy: { dataInizio: "desc" } });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-blue-900">Admin — Presenze eventi</h1>
      <ul className="space-y-3">
        {eventi.map((e) => (
          <li key={e.id} className="card flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="font-semibold">{e.titolo}</p>
              <p className="text-sm text-slate-600">
                {e.tipo} — {formatDateTime(e.dataInizio)}
              </p>
            </div>
            <Link href={`/admin/presenze/${e.id}`} className="btn-primary">
              Gestisci presenze
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
