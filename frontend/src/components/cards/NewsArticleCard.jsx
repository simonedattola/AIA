import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Card, CardTitle } from "@/design-system";
import { formatDateIt } from "../../lib/format";

function NewsArticleCard({ article, showReadMore = true }) {
  return (
    <Card as="article" interactive padding="none" className="overflow-hidden hover:border-navy-600">
      <Link to={`/news/${article.slug}`} className="block">
        <div className="aspect-[16/10] bg-slate-100 overflow-hidden">
          {article.coverUrl && (
            <img src={article.coverUrl} alt={article.title} className="w-full h-full object-cover" loading="lazy" />
          )}
        </div>
        <div className="p-4 sm:p-ds-card-lg">
          <div className="flex items-center gap-2 text-xs mb-3">
            <span className="inline-block px-2.5 py-1 bg-navy-50 text-navy-700 rounded font-medium">
              {article.category}
            </span>
            <time className="text-slate-500">{formatDateIt(article.publishedAt)}</time>
          </div>
          <CardTitle as="h3" className="leading-tight mb-2 line-clamp-2">
            {article.title}
          </CardTitle>
          <p className="text-slate-600 text-sm line-clamp-3 mb-4">{article.excerpt}</p>
          {showReadMore && (
            <span className="inline-flex items-center gap-1.5 text-navy-600 font-medium text-sm">
              Leggi tutto <ArrowRight className="h-4 w-4" aria-hidden />
            </span>
          )}
        </div>
      </Link>
    </Card>
  );
}

export default memo(NewsArticleCard);
