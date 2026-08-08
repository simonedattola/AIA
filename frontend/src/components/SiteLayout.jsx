import SiteHeader from "./SiteHeader";
import SiteFooter from "./SiteFooter";

export default function SiteLayout({ children }) {
  return (
    <div className="app-canvas min-h-screen flex flex-col">
      <SiteHeader />
      {/* Padding top solo con SiteHeader desktop (≥1140px). Su mobile niente barra bianca. */}
      <main className="flex-1 min-[1140px]:pt-16 xl:pt-[4.25rem]">{children}</main>
      <SiteFooter />
    </div>
  );
}
