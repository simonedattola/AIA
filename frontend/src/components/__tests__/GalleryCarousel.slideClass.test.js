import { gallerySlideClass } from "../GalleryCarousel";

describe("gallerySlideClass", () => {
  it("sizes portrait by width so mobile tiles stay readable", () => {
    const cls = gallerySlideClass("9:16");
    expect(cls).toContain("aspect-[9/16]");
    expect(cls).toContain("w-[min(48vw,13.5rem)]");
    expect(cls).not.toMatch(/\bh-44\b/);
    expect(cls).not.toMatch(/\bh-52\b/);
  });

  it("sizes landscape by width", () => {
    const cls = gallerySlideClass("16:9");
    expect(cls).toContain("aspect-[16/9]");
    expect(cls).toContain("w-[min(78vw,22rem)]");
  });

  it("defaults unknown aspect to landscape frame", () => {
    expect(gallerySlideClass("4:3")).toContain("aspect-[16/9]");
    expect(gallerySlideClass(undefined)).toContain("aspect-[16/9]");
  });
});
