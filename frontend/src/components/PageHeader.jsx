import { Eyebrow, HeroTitle } from "@/design-system";
import PageBrandBar from "./PageBrandBar";

export default function PageHeader({ eyebrow, title, description, bg }) {
  return (
    <section className="relative bg-navy-700 text-white pt-6 pb-12 min-[1140px]:pt-16 lg:pb-14 overflow-hidden">
      <div className="absolute inset-0 bg-pattern-stadio opacity-30" />
      {bg && (
        <div className="absolute inset-0 z-0">
          <img src={bg} alt="" className="w-full h-full object-cover opacity-20" />
        </div>
      )}
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 z-10">
        <PageBrandBar className="mb-6" tone="onDark" />
        {eyebrow && (
          <Eyebrow as="div" className="text-gold-400 tracking-[0.25em] mb-4">
            {eyebrow}
          </Eyebrow>
        )}
        <HeroTitle className="text-white mb-5 max-w-4xl">
          {title}
        </HeroTitle>
        <span className="gold-divider mb-5 block" />
        {description && <p className="text-lg text-slate-200 max-w-3xl leading-relaxed">{description}</p>}
      </div>
    </section>
  );
}
