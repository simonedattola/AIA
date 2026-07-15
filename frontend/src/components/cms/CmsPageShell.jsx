import PageHeader from "../PageHeader";
import PageMeta from "../PageMeta";
import { BlocksRenderer } from "../../blocks/BlockRenderer";
import { cmsHeaderProps } from "../../lib/useCmsPage";
import { COMPACT_HEADER_SLUGS } from "../../lib/systemPages";

function BodyHtmlSection({ page, testId }) {
  if (!page?.bodyHtml) return null;
  return (
    <section className="site-section bg-background" data-testid={testId || "cms-body-html"}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="prose-aia" dangerouslySetInnerHTML={{ __html: page.bodyHtml }} />
      </div>
    </section>
  );
}

/** Hero a tutta pagina (solo home e simili): alto + statistiche o esplicitamente tall con sfondo. */
function isFullBleedHero(block) {
  if (!block || block.type !== "hero" || block.enabled === false) return false;
  const c = block.config || {};
  if (c.showStats) return true;
  if (c.height === "tall") return true;
  if (c.backgroundImage && c.primaryCta?.label) return true;
  return false;
}

function headerFromHero(block) {
  const c = block.config || {};
  return {
    eyebrow: c.eyebrow || "",
    title: c.title || "",
    description: c.subtitle || "",
    bg: c.backgroundImage || "",
  };
}

/** Wrapper CMS: intestazione compatta + blocchi. */
export default function CmsPageShell({ slug, testId, bodyTestId, defaultHeader = {}, page: pageProp, stats: statsProp, loading: loadingProp, blockContext = {}, children }) {
  const blocks = (pageProp?.blocks || []).filter((b) => b.enabled !== false);
  const usesCompactHeader = COMPACT_HEADER_SLUGS.has(slug);
  const fullBleed = !usesCompactHeader && blocks.length > 0 && isFullBleedHero(blocks[0]);
  const leadingHero = !usesCompactHeader && !fullBleed && blocks[0]?.type === "hero" ? blocks[0] : null;

  let contentBlocks = blocks;
  if (fullBleed) {
    contentBlocks = blocks;
  } else if (usesCompactHeader) {
    // Banner navy dai campi pagina: ignora eventuale blocco Hero in cima.
    contentBlocks = blocks.filter((b, i) => !(i === 0 && b.type === "hero"));
  } else if (leadingHero) {
    contentBlocks = blocks.slice(1);
  }

  const header = cmsHeaderProps(
    pageProp,
    usesCompactHeader ? defaultHeader : leadingHero ? { ...defaultHeader, ...headerFromHero(leadingHero) } : defaultHeader
  );
  // Banner compatto: solo navy + pattern, senza foto di sfondo (come Designazioni/Arbitri).
  const headerForRender = usesCompactHeader ? { ...header, bg: "" } : header;
  const showClassicHeader = !fullBleed && (
    usesCompactHeader
      ? Boolean(header.title || header.eyebrow || header.description)
      : Boolean(header.eyebrow || header.title || header.description)
  );
  const showBodyFallback = !fullBleed && contentBlocks.length === 0 && pageProp?.bodyHtml;

  if (loadingProp) {
    return <div className="min-h-[60vh]" data-testid={testId} />;
  }

  return (
    <div data-testid={testId}>
      <PageMeta page={pageProp} />
      {fullBleed ? (
        <BlocksRenderer blocks={blocks} context={{ stats: statsProp, ...blockContext }} />
      ) : (
        <>
          {showClassicHeader && <PageHeader {...headerForRender} />}
          {contentBlocks.length > 0 && (
            <BlocksRenderer blocks={contentBlocks} context={{ stats: statsProp, ...blockContext }} />
          )}
          {showBodyFallback && <BodyHtmlSection page={pageProp} testId={bodyTestId} />}
        </>
      )}
      {children}
    </div>
  );
}
