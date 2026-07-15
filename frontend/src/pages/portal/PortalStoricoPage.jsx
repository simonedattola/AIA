import { useEffect, useState } from "react";
import { portalStorico } from "../../lib/portal-api";
import DesignationsTable, { formatSeasonLabel } from "../../components/portal/DesignationsTable";
import { ClipboardList, TrendingUp } from "lucide-react";
import { Card } from "@/design-system";
import { PortalPageHeader } from "../../components/portal/portal-ui";

export default function PortalStoricoPage() {
  const [data, setData] = useState(null);
  const [season, setSeason] = useState("");

  useEffect(() => {
    portalStorico(season || undefined).then((res) => {
      setData(res);
      if (!season && res.seasonsAvailable?.[0]) {
        setSeason(res.seasonsAvailable[0]);
      }
    });
  }, [season]);

  if (!data) return <p className="text-slate-500">Caricamento…</p>;

  const stats = data.stats || {};
  const designations = data.designations || [];

  return (
    <div>
      <PortalPageHeader
        title="Storico arbitrale"
        description="Designazioni registrate nel database della sezione."
      />

      <div className="grid sm:grid-cols-2 gap-4 mb-8">
        <Card className="flex items-center gap-4">
          <ClipboardList className="h-8 w-8 text-navy-600 shrink-0" />
          <div>
            <div className="text-2xl font-bold text-navy-700">{stats.totaleDesignazioni ?? 0}</div>
            <div className="text-sm text-slate-600">
              Designazioni totali — stagione {formatSeasonLabel(stats.stagione)}
            </div>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <TrendingUp className="h-8 w-8 text-gold-500 shrink-0" />
          <div>
            <div className="text-lg font-bold text-navy-700 leading-snug">
              {stats.categoriaMassima || "—"}
            </div>
            <div className="text-sm text-slate-600">Categoria più alta arbitrata</div>
          </div>
        </Card>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <DesignationsTable
          designations={designations}
          seasonsAvailable={data.seasonsAvailable || []}
          season={season}
          onSeasonChange={setSeason}
        />
      </div>
    </div>
  );
}
