import { useEffect, useState } from "react";

import { useSearchParams } from "react-router-dom";

import {

  portalComunicazioni,

  portalComunicazione,

  portalComunicazioneRisposta,

} from "../../lib/portal-api";

import { formatDateIt } from "../../lib/format";

import { AttachmentList } from "../../components/AttachmentList";

import { ArrowLeft, MessageCircle, Send } from "lucide-react";

import { Button, CardTitle, SubsectionTitle } from "@/design-system";

import { PORTAL_ICONS } from "../../components/portal/portalNavItems";

import { PortalEmptyState, PortalPageHeader } from "../../components/portal/portal-ui";



const ComunicazioniIcon = PORTAL_ICONS.comunicazioni;



export default function PortalComunicazioniPage() {

  const [searchParams, setSearchParams] = useSearchParams();

  const [items, setItems] = useState([]);

  const [selected, setSelected] = useState(null);

  const [reply, setReply] = useState("");

  const [loading, setLoading] = useState(false);



  const loadList = () => portalComunicazioni().then(setItems);



  useEffect(() => {

    loadList();

  }, []);



  useEffect(() => {

    const id = searchParams.get("id");

    if (id) openDetail(id);
  }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps



  const openDetail = async (id) => {

    setLoading(true);

    try {

      const detail = await portalComunicazione(id);

      setSelected(detail);

      setSearchParams({ id });

      loadList();

    } finally {

      setLoading(false);

    }

  };



  const closeDetail = () => {

    setSelected(null);

    setSearchParams({});

    loadList();

  };



  const inviaRisposta = async (e) => {

    e.preventDefault();

    if (!selected || !reply.trim()) return;

    await portalComunicazioneRisposta(selected.id, reply.trim());

    setReply("");

    const updated = await portalComunicazione(selected.id);

    setSelected(updated);

    loadList();

  };



  if (selected) {

    const allowReplies = selected.allowReplies !== false;

    return (

      <div>

        <button

          type="button"

          onClick={closeDetail}

          className="inline-flex items-center gap-1 text-sm text-navy-600 hover:underline mb-4"

        >

          <ArrowLeft className="h-4 w-4" /> Tutte le comunicazioni

        </button>

        <article className="bg-white rounded-lg border border-slate-200 p-6">

          <CardTitle as="h1" className="text-2xl text-navy-800">{selected.title}</CardTitle>

          <p className="text-xs text-slate-500 mt-2">

            {formatDateIt(selected.createdAt?.slice(0, 10))} · da {selected.authorName || "Sezione"}

          </p>

          <div

            className="prose-aia text-sm mt-4"

            dangerouslySetInnerHTML={{ __html: selected.bodyHtml || "" }}

          />

          <AttachmentList attachments={selected.attachments} className="mt-4" />

        </article>



        {(selected.risposte?.length > 0 || allowReplies) && (

          <section className="mt-6 bg-white rounded-lg border border-slate-200 p-6">

            <SubsectionTitle as="h2" className="font-semibold flex items-center gap-2 mb-4">

              <MessageCircle className="h-5 w-5" />

              Risposte ({selected.risposte?.length || 0})

            </SubsectionTitle>

            <ul className="space-y-3 mb-4 max-h-64 overflow-y-auto">

              {(selected.risposte || []).map((r) => (

                <li key={r.id} className="bg-slate-50 rounded-md p-3 text-sm">

                  <div className="font-medium text-navy-700">{r.memberName}</div>

                  <div className="text-xs text-slate-400">{formatDateIt(r.createdAt?.slice(0, 10))}</div>

                  <p className="mt-1 text-slate-700">{r.testo}</p>

                </li>

              ))}

            </ul>

            {allowReplies && (

              <form onSubmit={inviaRisposta} className="flex gap-2">

                <input

                  value={reply}

                  onChange={(e) => setReply(e.target.value)}

                  placeholder="Scrivi una risposta…"

                  className="flex-1 border border-slate-300 rounded-full px-4 py-2 text-sm"

                />

                <Button type="submit" variant="primary" className="rounded-full px-4">

                  <Send className="h-4 w-4" />

                </Button>

              </form>

            )}

          </section>

        )}

      </div>

    );

  }



  return (

    <div>

      <PortalPageHeader

        title="Comunicazioni interne"

        description="Messaggi dalla sezione riservati agli associati."

      />

      {loading && <p className="text-sm text-slate-500">Caricamento…</p>}

      <div className="space-y-3">

        {items.map((c) => (

          <button

            key={c.id}

            type="button"

            onClick={() => openDetail(c.id)}

            className={`w-full text-left bg-white rounded-lg border p-5 hover:border-navy-300 transition-colors ${

              c.letta ? "border-slate-200" : "border-gold-300 bg-gold-50/30"

            }`}

          >

            <div className="flex items-start gap-3">

              {!c.letta && <span className="mt-1.5 h-2.5 w-2.5 rounded-full bg-gold-500 shrink-0" />}

              <div className="flex-1 min-w-0">

                <CardTitle as="h2" className={c.letta ? "text-navy-800" : "text-navy-900"}>{c.title}</CardTitle>

                <p className="text-xs text-slate-500 mt-1">{formatDateIt(c.createdAt?.slice(0, 10))}</p>

                {c.risposteCount > 0 && (

                  <p className="text-xs text-navy-600 mt-2">{c.risposteCount} risposte</p>

                )}

                {(c.attachments?.length > 0) && (

                  <p className="text-xs text-slate-500 mt-1">{c.attachments.length} allegat{c.attachments.length === 1 ? "o" : "i"}</p>

                )}

              </div>

            </div>

          </button>

        ))}

        {items.length === 0 && !loading && (

          <PortalEmptyState icon={ComunicazioniIcon}>

            Nessuna comunicazione al momento.

          </PortalEmptyState>

        )}

      </div>

    </div>

  );

}

