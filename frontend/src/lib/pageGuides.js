/** Guida semplice per ogni pagina — pensata per utenti non tecnici. */

export const PAGE_GUIDES = {
  home: {
    title: "Homepage",
    edit: "Modifica le sezioni: intestazione in cima, news, eventi e invito al corso arbitri. La galleria in fondo si gestisce da Galleria.",
  },
  "chi-siamo": {
    title: "Chi siamo",
    edit: "Modifica titolo, storia e organigramma. I nomi nell'organigramma arrivano da Anagrafica; qui puoi cambiare titoli e testi introduttivi.",
  },
  designazioni: {
    title: "Designazioni",
    edit: "Modifica titolo e testi. La tabella designazioni si aggiorna automaticamente da AIA FIGC.",
  },
  arbitri: {
    title: "Arbitri",
    edit: "Modifica titolo e testi. L'elenco arbitri si aggiorna da Anagrafica.",
  },
  news: {
    title: "News & Successi",
    edit: "Modifica titolo e testi. Gli articoli si pubblicano da Articoli.",
  },
  eventi: {
    title: "Eventi",
    edit: "Modifica titolo e testi. Gli eventi si inseriscono da Eventi.",
  },
  contatti: {
    title: "Contatti",
    edit: "Modifica titoli e testi del modulo. Indirizzo e telefono sono in Impostazioni.",
  },
  "diventa-arbitro": {
    title: "Diventa Arbitro",
    edit: "Pagina del corso arbitri: modifica le sezioni, incluso il modulo di iscrizione.",
  },
};

export function guideForSlug(slug) {
  return (
    PAGE_GUIDES[slug] || {
      title: "Pagina personalizzata",
      edit: "Aggiungi e modifica le sezioni per comporre la pagina. Alcune sezioni si aggiornano da sole con i dati del sito.",
    }
  );
}
