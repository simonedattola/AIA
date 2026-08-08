import { clsx } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

/**
 * Custom fontSize tokens use the `text-ds-*` prefix. Without registering them,
 * tailwind-merge treats them as text-color and drops them when `text-navy-*` /
 * `text-white` is also present — leaving section titles at 16px.
 */
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [
        {
          text: [
            "ds-page",
            "ds-page-lg",
            "ds-hero",
            "ds-hero-sm",
            "ds-hero-lg",
            "ds-cta",
            "ds-cta-md",
            "ds-cta-lg",
            "ds-section",
            "ds-section-lg",
            "ds-subsection",
            "ds-subsection-lg",
            "ds-card",
            "ds-body",
            "ds-small",
            "ds-caption",
          ],
        },
      ],
    },
  },
});

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
