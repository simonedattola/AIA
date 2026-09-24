import axios from "axios";
import { PORTAL_ROUTES } from "./appRoutes";

const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");
const PORTAL_BASE = BACKEND_URL ? `${BACKEND_URL}/api/portal` : "/api/portal";

const portalApi = axios.create({ baseURL: PORTAL_BASE });

portalApi.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("aia_member_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

portalApi.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      const path = window.location.pathname;
      if (path.startsWith("/area-associati") && !path.includes("/login")) {
        localStorage.removeItem("aia_member_token");
        localStorage.removeItem("aia_member");
        window.location.href = PORTAL_ROUTES.login;
      }
    }
    return Promise.reject(err);
  }
);

export const portalLogin = (codice, password) =>
  portalApi.post("/login", { codice, password }).then((r) => r.data);

export const portalMe = () => portalApi.get("/me").then((r) => r.data);
export const portalUpdateMe = (data) => portalApi.put("/me", data).then((r) => r.data);
export const portalUploadFoto = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return portalApi.post("/upload-foto", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};
export const portalDeleteFoto = () => portalApi.delete("/upload-foto").then((r) => r.data);
export const portalSubmitTestimonial = (data) =>
  portalApi.post("/testimonianza", data).then((r) => r.data);
export const portalDashboard = () => portalApi.get("/dashboard").then((r) => r.data);
export const portalCalendario = () =>
  portalApi.get("/calendario").then((r) => {
    const data = r.data;
    if (Array.isArray(data)) {
      return { eventi: data, stagione: "", presenti: 0, assenti: 0 };
    }
    return {
      eventi: data?.eventi ?? [],
      stagione: data?.stagione ?? "",
      presenti: data?.presenti ?? 0,
      assenti: data?.assenti ?? 0,
    };
  });
export const portalSetPresenza = (eventId, stato) =>
  portalApi.put(`/calendario/${eventId}/presenza`, { stato }).then((r) => r.data);
export const portalStorico = (season) =>
  portalApi.get("/storico", { params: season ? { season } : {} }).then((r) => r.data);
export const portalDocumenti = (params) => portalApi.get("/documenti", { params }).then((r) => r.data);
export const portalUtility = () => portalApi.get("/utility").then((r) => r.data);
export const portalComunicazioni = () => portalApi.get("/comunicazioni").then((r) => r.data);
export const portalComunicazione = (id) => portalApi.get(`/comunicazioni/${id}`).then((r) => r.data);
export const portalComunicazioneLetta = (id) => portalApi.put(`/comunicazioni/${id}/letta`).then((r) => r.data);
export const portalComunicazioneRisposta = (id, testo) =>
  portalApi.post(`/comunicazioni/${id}/risposte`, { testo }).then((r) => r.data);
export const portalNews = () => portalComunicazioni();
export const portalPremi = () => portalApi.get("/premi").then((r) => r.data);
export const portalMedia = () => portalApi.get("/media").then((r) => r.data);

/** Scarica una foto taggata come file (Content-Disposition: attachment). */
export async function portalMediaDownload(imageId, fallbackName = "foto-aia-legnano.jpg") {
  try {
    const res = await portalApi.get(`/media/${encodeURIComponent(imageId)}/download`, {
      responseType: "blob",
    });
    const cd = res.headers?.["content-disposition"] || "";
    const match = /filename\*?=(?:UTF-8''|")?([^";]+)/i.exec(cd);
    const rawName = match ? decodeURIComponent(match[1].replace(/"/g, "").trim()) : "";
    const filename = rawName || fallbackName;
    const blob = res.data;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    return filename;
  } catch (err) {
    const data = err?.response?.data;
    if (data instanceof Blob) {
      try {
        const text = await data.text();
        const parsed = JSON.parse(text);
        const detail = parsed?.detail;
        const e = new Error(typeof detail === "string" ? detail : "Download non riuscito");
        e.response = { data: { detail: e.message } };
        throw e;
      } catch (inner) {
        if (inner?.response) throw inner;
      }
    }
    throw err;
  }
}

export const portalGalleryMine = () => portalApi.get("/gallery/mine").then((r) => r.data);
export const portalGalleryCategories = () =>
  portalApi.get("/gallery/categories").then((r) => r.data);
export const portalGalleryUpload = (file, { caption = "", category = "" } = {}) => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("caption", caption);
  if (category) fd.append("category", category);
  return portalApi.post("/gallery/upload", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};
export const portalConversazioni = () => portalApi.get("/messaggi/conversazioni").then((r) => r.data);
export const portalConversazione = (chatId) =>
  portalApi.get(`/messaggi/conversazioni/${encodeURIComponent(chatId)}`).then((r) => r.data);
export const portalEliminaConversazione = (chatId) =>
  portalApi.delete(`/messaggi/conversazioni/${encodeURIComponent(chatId)}`).then((r) => r.data);
export const portalInviaMessaggioChat = (chatId, payload) =>
  portalApi
    .post(
      `/messaggi/conversazioni/${encodeURIComponent(chatId)}`,
      typeof payload === "string" ? { testo: payload } : payload
    )
    .then((r) => r.data);
export const portalUploadAllegatoMessaggio = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return portalApi.post("/messaggi/allegati", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};
export const portalModificaMessaggio = (msgId, testo) =>
  portalApi.put(`/messaggi/${encodeURIComponent(msgId)}`, { testo }).then((r) => r.data);
export const portalEliminaMessaggio = (msgId) =>
  portalApi.delete(`/messaggi/${encodeURIComponent(msgId)}`).then((r) => r.data);
export const portalReazioneMessaggio = (msgId, emoji) =>
  portalApi.post(`/messaggi/${encodeURIComponent(msgId)}/reazioni`, { emoji }).then((r) => r.data);
export const portalContattoChat = (chatId) =>
  portalApi.get(`/messaggi/conversazioni/${encodeURIComponent(chatId)}/contatto`).then((r) => r.data);
export const portalInfoGruppo = (chatId) =>
  portalApi.get(`/messaggi/conversazioni/${encodeURIComponent(chatId)}/gruppo`).then((r) => r.data);
export const portalAggiornaGruppo = (gruppoId, data) =>
  portalApi.put(`/messaggi/gruppi/${encodeURIComponent(gruppoId)}`, data).then((r) => r.data);
export const portalEsciGruppo = (gruppoId) =>
  portalApi.post(`/messaggi/gruppi/${encodeURIComponent(gruppoId)}/esci`).then((r) => r.data);
export const portalCreaGruppo = (data) => portalApi.post("/messaggi/gruppi", data).then((r) => r.data);
export const portalAssociatiMessaggi = () => portalApi.get("/messaggi/associati").then((r) => r.data);
