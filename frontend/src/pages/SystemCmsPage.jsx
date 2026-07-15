import { useCmsPage } from "../lib/useCmsPage";
import CmsPageShell from "../components/cms/CmsPageShell";

/** Pagina di sistema interamente gestita da blocchi CMS. */
export default function SystemCmsPage({ slug, testId, defaultHeader, blockContext, children }) {
  const { page, stats, loading } = useCmsPage(slug);
  return (
    <CmsPageShell
      slug={slug}
      testId={testId || `${slug}-page`}
      defaultHeader={defaultHeader}
      page={page}
      stats={stats}
      loading={loading}
      blockContext={blockContext}
    >
      {children}
    </CmsPageShell>
  );
}
