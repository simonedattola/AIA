import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useParams, useLocation } from "react-router-dom";
import ScrollToTop from "./components/ScrollToTop";
import { SiteProvider } from "./lib/site-context";
import { ToastContainer } from "./lib/toast";
import SiteLayout from "./components/SiteLayout";

import HomePage from "./pages/HomePage";
import NewsListPage from "./pages/NewsListPage";
import NewsDetailPage from "./pages/NewsDetailPage";
import DiventaArbitroPage from "./pages/DiventaArbitroPage";
import ChiSiamoPage from "./pages/ChiSiamoPage";
import DesignazioniPage from "./pages/DesignazioniPage";
import ArbitriPage from "./pages/ArbitriPage";
import OsservatoriPage from "./pages/OsservatoriPage";
import AssociatoProfilePage from "./pages/AssociatoProfilePage";
import EventiPage from "./pages/EventiPage";
import ContattiPage from "./pages/ContattiPage";
import PortalLoginPage from "./pages/portal/PortalLoginPage";
import AssociatoLayout from "./components/portal/AssociatoLayout";
import PortalDashboardPage from "./pages/portal/PortalDashboardPage";
import PortalProfiloPage from "./pages/portal/PortalProfiloPage";
import PortalCalendarioPage from "./pages/portal/PortalCalendarioPage";
import PortalStoricoPage from "./pages/portal/PortalStoricoPage";
import PortalAreaTecnicaPage from "./pages/portal/PortalAreaTecnicaPage";
import PortalUtilityPage from "./pages/portal/PortalUtilityPage";
import PortalComunicazioniPage from "./pages/portal/PortalComunicazioniPage";
import PortalPremiPage from "./pages/portal/PortalPremiPage";
import PortalMediaPage from "./pages/portal/PortalMediaPage";
import PortalMessaggiPage from "./pages/portal/PortalMessaggiPage";
import AdminComunicazioniPage from "./pages/admin/AdminComunicazioniPage";

import AdminLoginPage from "./pages/admin/AdminLoginPage";
import AdminLayout from "./pages/admin/AdminLayout";
import AdminErrorBoundary from "./components/admin/AdminErrorBoundary";
import AdminDashboardPage from "./pages/admin/AdminDashboardPage";
import AdminPagesPage from "./pages/admin/AdminPagesPage";
import AdminPageEditPage from "./pages/admin/AdminPageEditPage";
import AdminArticlesPage from "./pages/admin/AdminArticlesPage";
import AdminArticleEditPage from "./pages/admin/AdminArticleEditPage";
import AdminEventsPage from "./pages/admin/AdminEventsPage";
import AdminMembersPage from "./pages/admin/AdminMembersPage";
import AdminDesignationsPage from "./pages/admin/AdminDesignationsPage";
import AdminLeadsPage from "./pages/admin/AdminLeadsPage";
import AdminDocumentsPage from "./pages/admin/AdminDocumentsPage";
import AdminUtilityPage from "./pages/admin/AdminUtilityPage";
import AdminUtilityRtoMaterialPage from "./pages/admin/AdminUtilityRtoMaterialPage";
import AdminTestimonialsPage from "./pages/admin/AdminTestimonialsPage";
import AdminSettingsPage from "./pages/admin/AdminSettingsPage";
import AdminMessagesPage from "./pages/admin/AdminMessagesPage";
import AdminGalleryPage from "./pages/admin/AdminGalleryPage";
import CustomPage from "./pages/CustomPage";
import { ADMIN_ROUTES, PORTAL_ROUTES } from "./lib/appRoutes";

function PublicWrapper({ children }) {
  return <SiteLayout>{children}</SiteLayout>;
}

function NewsDetailRoute() {
  const { slug } = useParams();
  return <NewsDetailPage key={slug} />;
}

function LegacyPrefixRedirect({ from, to }) {
  const { pathname, search, hash } = useLocation();
  const next = `${pathname.replace(from, to)}${search}${hash}`;
  return <Navigate to={next} replace />;
}

function RedirectAssociatoSlug() {
  const { slug } = useParams();
  return <Navigate to={`/arbitri/${slug}`} replace />;
}

function RedirectAdminSubpath({ toPrefix }) {
  const params = useParams();
  const rest = Object.values(params).filter(Boolean).join("/");
  return <Navigate to={`${toPrefix}${rest ? `/${rest}` : ""}`} replace />;
}

function App() {
  return (
    <div className="App">
      <SiteProvider>
        <BrowserRouter>
          <ScrollToTop />
          <ToastContainer />
          <Routes>
            <Route path="/" element={<PublicWrapper><HomePage /></PublicWrapper>} />
            <Route path="/chi-siamo" element={<PublicWrapper><ChiSiamoPage /></PublicWrapper>} />
            <Route path="/designazioni" element={<PublicWrapper><DesignazioniPage /></PublicWrapper>} />
            <Route path="/arbitri" element={<PublicWrapper><ArbitriPage /></PublicWrapper>} />
            <Route path="/arbitri/:slug" element={<PublicWrapper><AssociatoProfilePage /></PublicWrapper>} />
            <Route path="/osservatori" element={<PublicWrapper><OsservatoriPage /></PublicWrapper>} />
            <Route path="/associati" element={<Navigate to="/arbitri" replace />} />
            <Route path="/associati/:slug" element={<RedirectAssociatoSlug />} />
            <Route path="/news" element={<PublicWrapper><NewsListPage /></PublicWrapper>} />
            <Route path="/news/:slug" element={<PublicWrapper><NewsDetailRoute /></PublicWrapper>} />
            <Route path="/eventi" element={<PublicWrapper><EventiPage /></PublicWrapper>} />
            <Route path="/diventa-arbitro" element={<PublicWrapper><DiventaArbitroPage /></PublicWrapper>} />
            <Route path="/contatti" element={<PublicWrapper><ContattiPage /></PublicWrapper>} />
            <Route path="/risorse" element={<Navigate to="/" replace />} />
            <Route path="/area/riservata" element={<Navigate to={PORTAL_ROUTES.login} replace />} />
            <Route path="/area-riservata/*" element={<LegacyPrefixRedirect from="/area-riservata" to="/area-associati" />} />
            <Route path="/area-associati">
              <Route path="login" element={<PortalLoginPage />} />
              <Route element={<AssociatoLayout />}>
                <Route index element={<PortalDashboardPage />} />
                <Route path="profilo" element={<PortalProfiloPage />} />
                <Route path="calendario" element={<PortalCalendarioPage />} />
                <Route path="storico-arbitrale" element={<PortalStoricoPage />} />
                <Route path="documenti" element={<PortalAreaTecnicaPage />} />
                <Route path="utility" element={<PortalUtilityPage />} />
                <Route path="comunicazioni-interne" element={<PortalComunicazioniPage />} />
                <Route path="premi-e-menzioni" element={<PortalPremiPage />} />
                <Route path="galleria" element={<PortalMediaPage />} />
                <Route path="messaggi" element={<PortalMessaggiPage />} />
                <Route path="storico" element={<Navigate to={PORTAL_ROUTES.storicoArbitrale} replace />} />
                <Route path="area-tecnica" element={<Navigate to={PORTAL_ROUTES.documenti} replace />} />
                <Route path="comunicazioni" element={<Navigate to={PORTAL_ROUTES.comunicazioniInterne} replace />} />
                <Route path="media" element={<Navigate to={PORTAL_ROUTES.galleria} replace />} />
                <Route path="premi" element={<Navigate to={PORTAL_ROUTES.premiEMenzioni} replace />} />
                <Route path="materiale-rto" element={<Navigate to={PORTAL_ROUTES.utility} replace />} />
                <Route path="news" element={<Navigate to={PORTAL_ROUTES.comunicazioniInterne} replace />} />
              </Route>
            </Route>
            <Route path="/p/:slug" element={<PublicWrapper><CustomPage /></PublicWrapper>} />

            {/* Admin */}
            <Route path="/admin/login" element={<Navigate to={ADMIN_ROUTES.login} replace />} />
            <Route path="/admin/*" element={<LegacyPrefixRedirect from="/admin" to="/amministrazione" />} />
            <Route path="/amministrazione/login" element={<AdminErrorBoundary><AdminLoginPage /></AdminErrorBoundary>} />
            <Route path="/amministrazione" element={<AdminErrorBoundary><AdminLayout /></AdminErrorBoundary>}>
              <Route index element={<AdminDashboardPage />} />
              <Route path="pagine" element={<AdminPagesPage />} />
              <Route path="pagine/:id" element={<AdminPageEditPage />} />
              <Route path="articoli" element={<AdminArticlesPage />} />
              <Route path="articoli/:id" element={<AdminArticleEditPage />} />
              <Route path="galleria" element={<AdminGalleryPage />} />
              <Route path="eventi" element={<AdminEventsPage />} />
              <Route path="comunicazioni-interne" element={<AdminComunicazioniPage />} />
              <Route path="anagrafica" element={<AdminMembersPage />} />
              <Route path="designazioni" element={<AdminDesignationsPage />} />
              <Route path="candidature" element={<AdminLeadsPage />} />
              <Route path="messaggi-sito" element={<AdminMessagesPage />} />
              <Route path="documenti" element={<AdminDocumentsPage />} />
              <Route path="utility" element={<AdminUtilityPage />} />
              <Route path="utility/evento/:eventId" element={<AdminUtilityRtoMaterialPage />} />
              <Route path="testimonianze" element={<AdminTestimonialsPage />} />
              <Route path="impostazioni" element={<AdminSettingsPage />} />
              {/* Redirect URL legacy */}
              <Route path="pages" element={<Navigate to={ADMIN_ROUTES.pagine} replace />} />
              <Route path="pages/:id" element={<RedirectAdminSubpath toPrefix={ADMIN_ROUTES.pagine} />} />
              <Route path="articles" element={<Navigate to={ADMIN_ROUTES.articoli} replace />} />
              <Route path="articles/:id" element={<RedirectAdminSubpath toPrefix={ADMIN_ROUTES.articoli} />} />
              <Route path="immagini" element={<Navigate to={ADMIN_ROUTES.galleria} replace />} />
              <Route path="events" element={<Navigate to={ADMIN_ROUTES.eventi} replace />} />
              <Route path="comunicazioni" element={<Navigate to={ADMIN_ROUTES.comunicazioniInterne} replace />} />
              <Route path="members" element={<Navigate to={ADMIN_ROUTES.anagrafica} replace />} />
              <Route path="designations" element={<Navigate to={ADMIN_ROUTES.designazioni} replace />} />
              <Route path="leads" element={<Navigate to={ADMIN_ROUTES.candidature} replace />} />
              <Route path="messages" element={<Navigate to={ADMIN_ROUTES.messaggiSito} replace />} />
              <Route path="documents" element={<Navigate to={ADMIN_ROUTES.documenti} replace />} />
              <Route path="testimonials" element={<Navigate to={ADMIN_ROUTES.testimonianze} replace />} />
              <Route path="settings" element={<Navigate to={ADMIN_ROUTES.impostazioni} replace />} />
              <Route path="utility/event/:eventId" element={<RedirectAdminSubpath toPrefix={`${ADMIN_ROUTES.utility}/evento`} />} />
              <Route path="utility/rto/:eventId" element={<RedirectAdminSubpath toPrefix={`${ADMIN_ROUTES.utility}/evento`} />} />
              <Route path="menu" element={<Navigate to={ADMIN_ROUTES.pagine} replace />} />
              <Route path="album" element={<Navigate to={ADMIN_ROUTES.galleria} replace />} />
              <Route path="notifiche" element={<Navigate to={ADMIN_ROUTES.comunicazioniInterne} replace />} />
              <Route path="officials" element={<Navigate to={ADMIN_ROUTES.anagrafica} replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </SiteProvider>
    </div>
  );
}

export default App;
