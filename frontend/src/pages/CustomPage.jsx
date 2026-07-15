import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchPage, fetchStats } from "../lib/api";
import { BlocksRenderer } from "../blocks/BlockRenderer";
import PageMeta from "../components/PageMeta";
import PageHeader from "../components/PageHeader";
import { cmsHeaderProps } from "../lib/useCmsPage";
import { Button } from "@/design-system";

export default function CustomPage() {
  const { slug } = useParams();
  const [page, setPage] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null); setPage(null);
    fetchPage(slug).then(setPage).catch(() => setError("Pagina non trovata"));
    fetchStats().then(setStats);
  }, [slug]);

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-32 text-center" data-testid="custom-page-error">
        <h1 className="font-display text-3xl font-bold text-navy-700 mb-4">Pagina non trovata</h1>
        <Button to="/" variant="primary">Torna alla home</Button>
      </div>
    );
  }
  if (!page) return <div className="min-h-[60vh]"/>;

  const blocks = (page.blocks || []).filter((b) => b.enabled !== false);
  const hasHero = blocks.length > 0 && blocks[0].type === "hero";
  const header = cmsHeaderProps(page);

  return (
    <div data-testid={`custom-page-${slug}`}>
      <PageMeta page={page} />
      {hasHero ? (
        <BlocksRenderer blocks={blocks} context={{ stats }} />
      ) : (
        <>
          {(header.eyebrow || header.title || header.description) && <PageHeader {...header} />}
          {blocks.length > 0 && <BlocksRenderer blocks={blocks} context={{ stats }} />}
          {blocks.length === 0 && page.bodyHtml && (
            <section className="site-section bg-background">
              <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="prose-aia" dangerouslySetInnerHTML={{ __html: page.bodyHtml }} />
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
