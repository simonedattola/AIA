import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchArticle } from "../lib/api";
import { formatDateIt } from "../lib/format";
import { scrollPageToTop } from "../lib/scroll";
import { useDocumentTitle } from "../components/RouteDocumentTitle";
import { ArrowLeft, Calendar, User as UserIcon } from "lucide-react";
import ArticleProse from "../components/ArticleProse";
import PageBrandBar from "../components/PageBrandBar";
import { Button, Card, CardTitle, CtaTitle, Eyebrow, PageTitle, SectionTitle } from "@/design-system";

function ArticleTopNav({ category, variant = "light" }) {
  const isHero = variant === "hero";
  return (
    <div
      className="flex flex-wrap items-center gap-3 sm:gap-4 mb-5 sm:mb-6"
      data-testid="news-article-top-nav"
    >
      <Link
        to="/news"
        className={`inline-flex items-center gap-2 text-sm font-medium shrink-0 ${
          isHero ? "text-gold-400 hover:text-white" : "text-navy-600 hover:text-gold-400"
        }`}
        data-testid="news-back-link"
      >
        <ArrowLeft className="h-4 w-4 shrink-0" aria-hidden />
        Tutte le news
      </Link>
      {category && (
        <>
          <span
            className={`hidden sm:block h-4 w-px shrink-0 ${isHero ? "bg-white/30" : "bg-slate-300"}`}
            aria-hidden
          />
          <span
            className={`inline-flex items-center px-3 py-1 text-xs font-semibold tracking-wider uppercase leading-none ${
              isHero
                ? "rounded-full bg-gold-400/20 border border-gold-400/30 text-gold-300"
                : "rounded bg-navy-50 text-navy-700"
            }`}
          >
            {category}
          </span>
        </>
      )}
    </div>
  );
}

export default function NewsDetailPage() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    scrollPageToTop();
    fetchArticle(slug)
      .then(setData)
      .catch(() => setError("Articolo non trovato"));
  }, [slug]);

  useEffect(() => {
    if (!data?.article?.bodyHtml) return;
    const root = document.querySelector('[data-testid="news-body-html"]');
    root?.querySelectorAll("iframe").forEach((el) => {
      el.setAttribute("tabindex", "-1");
    });
  }, [data?.article?.bodyHtml]);

  useDocumentTitle(data?.article?.title || (error ? "Articolo non trovato" : "News"));

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-32 text-center" data-testid="news-detail-error">
        <PageTitle className="mb-4">Articolo non trovato</PageTitle>
        <Button to="/news" variant="primary">
          Torna alle news
        </Button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-32 text-center text-slate-500">
        Caricamento…
      </div>
    );
  }

  const { article, related } = data;
  return (
    <div data-testid="news-detail-page" style={{ overflowAnchor: "none" }}>
      <article>
        {article.coverUrl ? (
          <div className="relative h-[55vh] min-h-[400px] max-h-[640px] overflow-hidden bg-navy-900 flex flex-col">
            <img
              src={article.coverUrl}
              alt={article.title}
              className="absolute inset-0 w-full h-full object-cover opacity-80"
            />
            <div className="absolute inset-0 hero-overlay" />
            <div className="relative z-10 flex flex-col flex-1 justify-between pt-6 min-[1140px]:pt-8">
              <div className="max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8">
                <PageBrandBar className="mb-4" tone="onDark" />
              </div>
              <div className="max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 pb-12 lg:pb-16 text-white">
                <ArticleTopNav category={article.category} variant="hero" />
                <CtaTitle className="text-white leading-tight mb-5 max-w-4xl">
                  {article.title}
                </CtaTitle>
                <div className="flex items-center gap-5 text-sm text-slate-200">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4" /> {formatDateIt(article.publishedAt)}
                  </span>
                  {article.authorName && (
                    <span className="flex items-center gap-1.5">
                      <UserIcon className="h-4 w-4" /> {article.authorName}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <section className="relative bg-navy-700 text-white pt-6 pb-10 min-[1140px]:pt-16">
            <div className="absolute inset-0 overflow-hidden bg-pattern-stadio opacity-30" aria-hidden />
            <div className="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 z-10">
              <PageBrandBar className="mb-6" tone="onDark" />
              <ArticleTopNav category={article.category} variant="hero" />
              <CtaTitle className="text-white leading-tight mb-4">{article.title}</CtaTitle>
              <div className="flex items-center gap-4 text-sm text-slate-200">
                <span className="flex items-center gap-1.5">
                  <Calendar className="h-4 w-4" /> {formatDateIt(article.publishedAt)}
                </span>
              </div>
            </div>
          </section>
        )}

        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-12">
          {article.excerpt && (
            <p
              className="text-xl text-slate-600 leading-relaxed mb-10 font-light italic border-l-4 border-gold-400 pl-6"
              data-testid="news-excerpt"
            >
              {article.excerpt}
            </p>
          )}

          <ArticleProse html={article.bodyHtml} />

          {Array.isArray(article.relatedMembers) && article.relatedMembers.length > 0 && (
            <aside
              className="mt-12 pt-8 border-t border-slate-200"
              data-testid="news-related-members"
            >
              <Eyebrow as="div" className="mb-3 tracking-[0.2em]">
                Associati citati
              </Eyebrow>
              <div className="flex flex-wrap gap-2">
                {article.relatedMembers.map((m) => (
                  <Link
                    key={m.id || m.slug}
                    to={`/arbitri/${m.slug}`}
                    className="inline-flex items-center gap-1.5 rounded-full border border-navy-200 bg-navy-50 px-3 py-1.5 text-sm font-medium text-navy-800 hover:bg-navy-100 hover:border-navy-300 transition-colors"
                    data-testid={`news-member-tag-${m.slug}`}
                  >
                    <UserIcon className="h-3.5 w-3.5 text-navy-500" aria-hidden />
                    {m.name || `${m.firstName || ""} ${m.lastName || ""}`.trim()}
                  </Link>
                ))}
              </div>
            </aside>
          )}
        </div>
      </article>

      {related.length > 0 && (
        <section className="bg-background site-section border-t border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <Eyebrow as="div" className="mb-2 tracking-[0.25em]">
              Continua a leggere
            </Eyebrow>
            <SectionTitle className="mb-2">Articoli correlati</SectionTitle>
            <span className="gold-divider mb-10 block" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {related.map((a) => (
                <Card
                  key={a.slug}
                  as="article"
                  interactive
                  padding="none"
                  className="overflow-hidden hover:border-navy-600"
                  data-testid={`related-news-${a.slug}`}
                >
                  <Link to={`/news/${a.slug}`} className="block" onClick={() => scrollPageToTop()}>
                    {a.coverUrl && (
                      <div className="aspect-[16/10] bg-slate-100 overflow-hidden">
                        <img
                          src={a.coverUrl}
                          alt={a.title}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      </div>
                    )}
                    <div className="p-ds-card">
                      <div className="flex items-center gap-2 text-xs mb-2">
                        <span className="inline-block px-2 py-0.5 bg-navy-50 text-navy-700 rounded font-medium">
                          {a.category}
                        </span>
                        <time className="text-slate-500">{formatDateIt(a.publishedAt)}</time>
                      </div>
                      <CardTitle as="h3" className="leading-tight line-clamp-2">
                        {a.title}
                      </CardTitle>
                    </div>
                  </Link>
                </Card>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
