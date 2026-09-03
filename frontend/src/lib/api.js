import axios from "axios";
import { ADMIN_ROUTES } from "./appRoutes";

const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");
export const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

/** Dispatched on admin 401 so AdminLayout can redirect without a hard reload. */
export const ADMIN_UNAUTHORIZED_EVENT = "aia:admin-unauthorized";

/** List endpoints must always resolve to an array (avoids .filter/.map crashes in admin UI). */
export function asAdminList(data) {
  return Array.isArray(data) ? data : [];
}

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("aia_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      const path = window.location.pathname;
      const publicAdminPaths = [
        ADMIN_ROUTES.login,
        ADMIN_ROUTES.forgotPassword,
        ADMIN_ROUTES.resetPassword,
      ];
      if (
        path.startsWith("/amministrazione") &&
        !publicAdminPaths.some((p) => path === p || path.startsWith(`${p}?`))
      ) {
        localStorage.removeItem("aia_token");
        localStorage.removeItem("aia_admin");
        window.dispatchEvent(new CustomEvent(ADMIN_UNAUTHORIZED_EVENT));
      }
    }
    return Promise.reject(err);
  }
);

// ---- Public ----
export const fetchSettings = () => api.get("/public/settings").then((r) => r.data);
export const fetchNav = () => api.get("/public/nav").then((r) => r.data);
export const fetchArticles = (params = {}) => api.get("/public/articles", { params }).then((r) => r.data);
export const fetchArticle = (slug) => api.get(`/public/articles/${slug}`).then((r) => r.data);
export const fetchCategories = () => api.get("/public/categories").then((r) => r.data);
export const fetchEvents = (params = {}) => api.get("/public/events", { params }).then((r) => r.data);
export const fetchOfficials = () => api.get("/public/officials").then((r) => r.data);
export const fetchMembers = (params = {}) => api.get("/public/members", { params }).then((r) => r.data);
export const fetchChiSiamoMembers = () => api.get("/public/members", { params: { scope: "chi_siamo", limit: 100 } }).then((r) => r.data);
export const fetchMember = (slug, params = {}) =>
  api.get(`/public/members/${slug}`, { params }).then((r) => r.data);
export const fetchDesignations = (params = {}) => api.get("/public/designations", { params }).then((r) => r.data);
export const fetchStats = () => api.get("/public/stats").then((r) => r.data);
export const fetchPage = (slug) => api.get(`/public/pages/${slug}`).then((r) => r.data);
export const fetchTestimonials = () => api.get("/public/testimonials").then((r) => r.data);
export const fetchDocuments = (params = {}) => api.get("/public/documents", { params }).then((r) => r.data);
export const fetchDocumentSections = () => api.get("/public/document-sections").then((r) => r.data);
export const fetchAlbums = () => api.get("/public/albums").then((r) => r.data);
export const fetchAlbum = (slug) => api.get(`/public/albums/${slug}`).then((r) => r.data);
export const fetchGallery = () => api.get("/public/gallery").then((r) => r.data);
export const fetchInstagramWidget = (params = {}) =>
  api.get("/public/instagram/widget", { params }).then((r) => r.data);

export const submitLead = (data) => api.post("/public/forms/corso-arbitri", data).then((r) => r.data);
export const submitContact = (data) => api.post("/public/forms/contatti", data).then((r) => r.data);

// ---- Admin ----
export const adminLogin = (email, password) => api.post("/admin/login", { email, password }).then((r) => r.data);
export const adminForgotPassword = (email) =>
  api.post("/admin/forgot-password", { email }).then((r) => r.data);
export const adminResetPassword = (token, password) =>
  api.post("/admin/reset-password", { token, password }).then((r) => r.data);
export const adminMe = () => api.get("/admin/me").then((r) => r.data);
export const adminDashboard = () =>
  api.get("/admin/dashboard").then((r) => {
    const data = r.data && typeof r.data === "object" ? r.data : {};
    return {
      ...data,
      publicDesignations: asAdminList(data.publicDesignations),
    };
  });

export const adminArticles = () => api.get("/admin/articles").then((r) => asAdminList(r.data));
export const adminArticleCategories = () => api.get("/admin/article-categories").then((r) => asAdminList(r.data));
export const adminAddArticleCategory = (name) =>
  api.post("/admin/article-categories", { name }).then((r) => r.data);
export const adminArticle = (id) => api.get(`/admin/articles/${id}`).then((r) => r.data);
export const adminCreateArticle = (data) => api.post("/admin/articles", data).then((r) => r.data);
export const adminUpdateArticle = (id, data) => api.put(`/admin/articles/${id}`, data).then((r) => r.data);
export const adminDeleteArticle = (id) => api.delete(`/admin/articles/${id}`).then((r) => r.data);

export const adminEvents = () => api.get("/admin/events").then((r) => asAdminList(r.data));
export const adminEventTypes = () => api.get("/admin/event-types").then((r) => asAdminList(r.data));
export const adminAddEventType = (name) => api.post("/admin/event-types", { name }).then((r) => r.data);
export const adminCreateEvent = (data) => api.post("/admin/events", data).then((r) => r.data);
export const adminUpdateEvent = (id, data) => api.put(`/admin/events/${id}`, data).then((r) => r.data);
export const adminDeleteEvent = (id) => api.delete(`/admin/events/${id}`).then((r) => r.data);

export const adminAlbums = () => api.get("/admin/albums").then((r) => asAdminList(r.data));
export const adminCreateAlbum = (data) => api.post("/admin/albums", data).then((r) => r.data);
export const adminUpdateAlbum = (id, data) => api.put(`/admin/albums/${id}`, data).then((r) => r.data);
export const adminDeleteAlbum = (id) => api.delete(`/admin/albums/${id}`).then((r) => r.data);

export const adminMembers = (params = {}) => api.get("/admin/members", { params }).then((r) => asAdminList(r.data));
export const adminCreateMember = (data) => api.post("/admin/members", data).then((r) => r.data);
export const adminUpdateMember = (id, data) => api.put(`/admin/members/${id}`, data).then((r) => r.data);
export const adminDeleteMember = (id) => api.delete(`/admin/members/${id}`).then((r) => r.data);
export const adminMembersImportTemplate = () =>
  api.get("/admin/members/import-template", { responseType: "blob" }).then((r) => r.data);
export const adminImportMembersFile = (
  file,
  { dryRun = false, removeMissing = false } = {}
) => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("dry_run", dryRun ? "true" : "false");
  fd.append("remove_missing", removeMissing ? "true" : "false");
  return api.post("/admin/members/import-file", fd, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000,
  }).then((r) => r.data);
};

export const adminDesignations = () => api.get("/admin/designations").then((r) => asAdminList(r.data));
export const adminCreateDesignation = (data) => api.post("/admin/designations", data).then((r) => r.data);
export const adminUpdateDesignation = (id, data) => api.put(`/admin/designations/${id}`, data).then((r) => r.data);
export const adminDeleteDesignation = (id) => api.delete(`/admin/designations/${id}`).then((r) => r.data);
export const adminSyncDesignationsAia = (data = {}) =>
  api.post("/admin/designations/sync-aia", data, { timeout: 30000 }).then((r) => r.data);
export const adminDesignationsSyncStatus = () =>
  api.get("/admin/designations/sync-status").then((r) => r.data);
export const adminDesignationsImportTemplate = () =>
  api.get("/admin/designations/import-template", { responseType: "blob" }).then((r) => r.data);
export const adminImportDesignationsFile = (file, { dryRun = false } = {}) => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("dry_run", dryRun ? "true" : "false");
  return api.post("/admin/designations/import-file", fd, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000,
  }).then((r) => r.data);
};

export const adminLeads = () => api.get("/admin/leads").then((r) => asAdminList(r.data));
export const adminUpdateLead = (id, data) => api.put(`/admin/leads/${id}`, data).then((r) => r.data);
export const adminDeleteLead = (id) => api.delete(`/admin/leads/${id}`).then((r) => r.data);

export const adminMessages = () => api.get("/admin/messages").then((r) => asAdminList(r.data));
export const adminUpdateMessage = (id, data) => api.put(`/admin/messages/${id}`, data).then((r) => r.data);
export const adminDeleteMessage = (id) => api.delete(`/admin/messages/${id}`).then((r) => r.data);

export const adminSettings = () => api.get("/admin/settings").then((r) => r.data);
export const adminPutSettings = (data) => api.put("/admin/settings", data).then((r) => r.data);

export const adminPages = () => api.get("/admin/pages").then((r) => asAdminList(r.data));
export const adminReconcileSystemPages = () => api.post("/admin/pages/reconcile-system").then((r) => r.data);
export const adminResetPageBlocks = (id) => api.post(`/admin/pages/${id}/reset-blocks`).then((r) => r.data);
export const adminPage = (id) => api.get(`/admin/pages/${id}`).then((r) => r.data);
export const adminCreatePage = (data) => api.post("/admin/pages", data).then((r) => r.data);
export const adminUpdatePage = (id, data) => api.put(`/admin/pages/${id}`, data).then((r) => r.data);
export const adminDeletePage = (id) => api.delete(`/admin/pages/${id}`).then((r) => r.data);

export const adminDocumentSections = () => api.get("/admin/document-sections").then((r) => asAdminList(r.data));
export const adminAddDocumentSection = (name) =>
  api.post("/admin/document-sections", { name }).then((r) => r.data);
export const adminDocuments = () => api.get("/admin/documents").then((r) => asAdminList(r.data));
export const adminCreateDocument = (data) => api.post("/admin/documents", data).then((r) => r.data);
export const adminUpdateDocument = (id, data) => api.put(`/admin/documents/${id}`, data).then((r) => r.data);
export const adminDeleteDocument = (id) => api.delete(`/admin/documents/${id}`).then((r) => r.data);

export const adminUtility = () => api.get("/admin/utility").then((r) => r.data);
export const adminUpdateUtilityPolo = (data) => api.put("/admin/utility/polo", data).then((r) => r.data);
export const adminCreateUtilityItem = (data) => api.post("/admin/utility-items", data).then((r) => r.data);
export const adminUpdateUtilityItem = (id, data) => api.put(`/admin/utility-items/${id}`, data).then((r) => r.data);
export const adminDeleteUtilityItem = (id) => api.delete(`/admin/utility-items/${id}`).then((r) => r.data);
export const adminUtilityEvent = (eventId) =>
  api.get(`/admin/utility/event/${eventId}`).then((r) => r.data);
export const adminUpdateUtilityEventMaterial = (eventId, utilityMaterial) =>
  api.put(`/admin/utility/event/${eventId}/material`, { utilityMaterial }).then((r) => r.data);
/** @deprecated usa adminUtilityEvent */
export const adminUtilityRtoEvent = adminUtilityEvent;
/** @deprecated usa adminUpdateUtilityEventMaterial */
export const adminUpdateUtilityRtoMaterial = adminUpdateUtilityEventMaterial;
export const adminImportAiaDocuments = () => api.post("/admin/documents/import-aia-figc").then((r) => r.data);
export const adminImportLegnanoDocuments = () => api.post("/admin/documents/import-aia-legnano").then((r) => r.data);
export const adminImportAllDocuments = () => api.post("/admin/documents/import-all-sources").then((r) => r.data);

export const adminTestimonials = () => api.get("/admin/testimonials").then((r) => asAdminList(r.data));
export const adminCreateTestimonial = (data) => api.post("/admin/testimonials", data).then((r) => r.data);
export const adminUpdateTestimonial = (id, data) => api.put(`/admin/testimonials/${id}`, data).then((r) => r.data);
export const adminDeleteTestimonial = (id) => api.delete(`/admin/testimonials/${id}`).then((r) => r.data);

export const adminUpload = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/admin/upload", fd, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
};

export const adminUploadAttachment = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/admin/upload-attachment", fd, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
};

export const adminGallery = (filters = {}) => {
  const params = {};
  if (filters.status) params.status = filters.status;
  if (filters.category) params.category = filters.category;
  if (filters.dateFrom) params.dateFrom = filters.dateFrom;
  if (filters.dateTo) params.dateTo = filters.dateTo;
  return api.get("/admin/gallery", { params }).then((r) => asAdminList(r.data));
};
export const adminGalleryCreate = (data) => api.post("/admin/gallery", data).then((r) => r.data);
export const adminGalleryUpload = (file, opts = {}) => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("caption", opts.caption || "");
  fd.append("sortOrder", String(opts.sortOrder ?? 0));
  if (opts.category) fd.append("category", opts.category);
  if (opts.sourceUrl) fd.append("sourceUrl", opts.sourceUrl);
  if (opts.aspect) fd.append("aspect", opts.aspect);
  return api.post("/admin/gallery/upload", fd, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
};
export const adminGallerySourceBlob = (id) =>
  api.get(`/admin/gallery/${id}/source`, { responseType: "blob" }).then((r) => r.data);
export const adminGalleryUpdate = (id, data) => api.put(`/admin/gallery/${id}`, data).then((r) => r.data);
export const adminGalleryApprove = (id) => api.post(`/admin/gallery/${id}/approve`).then((r) => r.data);
export const adminGalleryReject = (id) => api.post(`/admin/gallery/${id}/reject`).then((r) => r.data);
export const adminGalleryDelete = (id) => api.delete(`/admin/gallery/${id}`).then((r) => r.data);

// ---- Portale (admin: presenze & notifiche) ----
export const adminPresenzeEvento = (eventId) => api.get(`/portal/admin/presenze/eventi/${eventId}`).then((r) => r.data);
export const adminPresenzeEventoSave = (eventId, updates) =>
  api.put(`/portal/admin/presenze/eventi/${eventId}`, updates).then((r) => r.data);
export const adminPresenzeAssociato = (memberId) =>
  api.get(`/portal/admin/presenze/associati/${memberId}`).then((r) => r.data);
export const adminComunicazioni = () => api.get("/portal/admin/comunicazioni").then((r) => asAdminList(r.data));
export const adminComunicazioneLetture = (id) =>
  api.get(`/admin/comunicazioni/${id}/letture`).then((r) => r.data);
export const adminCreaComunicazione = (data) => api.post("/portal/admin/comunicazioni", data).then((r) => r.data);
export const adminDeleteComunicazione = (id) => api.delete(`/portal/admin/comunicazioni/${id}`).then((r) => r.data);
export default api;
