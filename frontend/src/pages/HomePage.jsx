import SystemCmsPage from "./SystemCmsPage";
import SiteGallerySection from "../components/SiteGallerySection";

export default function HomePage() {
  return (
    <SystemCmsPage slug="home" testId="home-page">
      <SiteGallerySection />
    </SystemCmsPage>
  );
}
