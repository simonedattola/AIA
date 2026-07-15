import { useMemo } from "react";
import { parseArticleBody } from "../lib/articleBody";
import ArticleImageCarousel from "./ArticleImageCarousel";

export default function ArticleProse({ html, className = "prose-aia", testId = "news-body-html" }) {
  const segments = useMemo(() => parseArticleBody(html || ""), [html]);

  return (
    <div data-testid={testId}>
      {segments.map((seg, idx) =>
        seg.type === "carousel" ? (
          <ArticleImageCarousel key={`carousel-${idx}`} images={seg.images} />
        ) : (
          <div
            key={`html-${idx}`}
            className={className}
            dangerouslySetInnerHTML={{ __html: seg.content }}
          />
        )
      )}
    </div>
  );
}
