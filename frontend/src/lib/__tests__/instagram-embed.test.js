import {
  parseInstagramPostEmbed,
  instagramPermalink,
  instagramPostEmbedSrc,
  resolveInstagramEmbedInput,
} from "../instagram-embed";

describe("parseInstagramPostEmbed", () => {
  it("parses post URL", () => {
    expect(parseInstagramPostEmbed("https://www.instagram.com/p/DW1XFlpjGQV/")).toEqual({
      shortcode: "DW1XFlpjGQV",
      kind: "post",
    });
  });

  it("parses reel and blockquote embed html", () => {
    expect(parseInstagramPostEmbed("https://www.instagram.com/reel/AbC123/")).toEqual({
      shortcode: "AbC123",
      kind: "reel",
    });
    const html =
      '<blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/p/DW1XFlpjGQV/?utm_source=ig_embed"></blockquote>';
    expect(parseInstagramPostEmbed(html)).toEqual({
      shortcode: "DW1XFlpjGQV",
      kind: "post",
    });
  });

  it("rejects profile-only URLs", () => {
    expect(parseInstagramPostEmbed("https://www.instagram.com/aia_legnano/")).toBeNull();
  });
});

describe("resolveInstagramEmbedInput", () => {
  it("reads href, html object, string and flat fields", () => {
    expect(resolveInstagramEmbedInput({ instagramEmbed: { href: "https://www.instagram.com/p/AAA/" } })).toContain(
      "/p/AAA/"
    );
    expect(resolveInstagramEmbedInput({ instagramEmbed: "https://www.instagram.com/p/BBB/" })).toContain("/p/BBB/");
    expect(resolveInstagramEmbedInput({ instagramPostUrl: "https://www.instagram.com/p/CCC/" })).toContain("/p/CCC/");
  });
});

describe("instagram permalink/src", () => {
  it("builds embed URLs", () => {
    const parsed = { shortcode: "DW1XFlpjGQV", kind: "post" };
    expect(instagramPermalink(parsed)).toBe("https://www.instagram.com/p/DW1XFlpjGQV/");
    expect(instagramPostEmbedSrc(parsed)).toContain("/embed/captioned");
  });
});
