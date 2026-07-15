import SiteHeader from "./SiteHeader";
import SiteFooter from "./SiteFooter";

export default function SiteLayout({ children }) {
  return (
    <div className="app-canvas min-h-screen flex flex-col">
      <SiteHeader />
      <main className="flex-1 pt-16 max-[1139px]:pt-[4.5rem] xl:pt-[4.25rem]">{children}</main>
      <SiteFooter />
    </div>
  );
}
