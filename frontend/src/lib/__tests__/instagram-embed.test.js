import {
  parseInstagramPostEmbed,
  parseInstagramUsername,
  instagramPermalink,
  instagramPostEmbedSrc,
  instagramProfileEmbedSrc,
  resolveInstagramEmbedInput,
} from "../instagram-embed";

describe("parseInstagramPostEmbed", () => {
  it("parses post url", () => {
    expect(parseInstagramPostEmbed("https://www.instagram.com/p/DW1XFlpjGQV/")).toEqual({
      shortcode: "DW1XFlpjGQV",
      kind: "post",
    });
  });

  it("parses reel url", () => {
    expect(parseInstagramPostEmbed("https://www.instagram.com/reel/AbC123/")).toEqual({
      shortcode: "AbC123",
      kind: "reel",
    });
  });

  it("parses blockquote permalink", () => {
    const html =
      '<blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/p/DW1XFlpjGQV/?utm_source=ig_embed"></blockquote>';
    expect(parseInstagramPostEmbed(html)).toEqual({
      shortcode: "DW1XFlpjGQV",
      kind: "post",
    });
  });

  it("rejects profile url for post parse", () => {
    expect(parseInstagramPostEmbed("https://www.instagram.com/aia_legnano/")).toBeNull();
  });
});

describe("parseInstagramUsername", () => {
  it("from profile url", () => {
    expect(parseInstagramUsername("https://www.instagram.com/aia_legnano")).toBe("aia_legnano");
    expect(parseInstagramUsername("https://www.instagram.com/aia_legnano/")).toBe("aia_legnano");
  });

  it("from handle", () => {
    expect(parseInstagramUsername("@aia_legnano")).toBe("aia_legnano");
  });

  it("rejects reserved paths", () => {
    expect(parseInstagramUsername("https://www.instagram.com/p/ABC/")).toBe("");
    expect(parseInstagramUsername("https://www.instagram.com/reel/ABC/")).toBe("");
  });
});

describe("instagramProfileEmbedSrc", () => {
  it("builds official profile embed url", () => {
    expect(instagramProfileEmbedSrc("https://www.instagram.com/aia_legnano/")).toBe(
      "https://www.instagram.com/aia_legnano/embed"
    );
  });
});

describe("resolveInstagramEmbedInput", () => {
  it("reads object href and flat fields", () => {
    expect(
      resolveInstagramEmbedInput({ instagramEmbed: { href: "https://www.instagram.com/p/AAA/" } })
    ).toContain("/p/AAA/");
    expect(resolveInstagramEmbedInput({ instagramEmbed: "https://www.instagram.com/p/BBB/" })).toContain(
      "/p/BBB/"
    );
    expect(resolveInstagramEmbedInput({ instagramPostUrl: "https://www.instagram.com/p/CCC/" })).toContain(
      "/p/CCC/"
    );
  });
});

describe("instagram permalink/src", () => {
  it("builds urls", () => {
    const parsed = { shortcode: "DW1XFlpjGQV", kind: "post" };
    expect(instagramPermalink(parsed)).toBe("https://www.instagram.com/p/DW1XFlpjGQV/");
    expect(instagramPostEmbedSrc(parsed)).toContain("/embed/captioned");
  });
});
