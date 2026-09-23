/**
 * @jest-environment jsdom
 */
import { parseArticleBody } from "./articleBody";

describe("parseArticleBody carousels", () => {
  test("consecutive images become a carousel (≥2)", () => {
    const html = `
      <p>Intro</p>
      <img src="/uploads/a.jpg" alt="A">
      <img src="/uploads/b.jpg" alt="B">
      <img src="/uploads/c.jpg" alt="C">
      <p>Fine</p>
    `;
    const segs = parseArticleBody(html);
    const carousel = segs.find((s) => s.type === "carousel");
    expect(carousel).toBeTruthy();
    expect(carousel.images).toHaveLength(3);
    expect(carousel.images.map((i) => i.alt)).toEqual(["A", "B", "C"]);
  });

  test("single image stays html, not carousel", () => {
    const html = `<p>Solo</p><img src="/uploads/one.jpg" alt="One"><p>Dopo</p>`;
    const segs = parseArticleBody(html);
    expect(segs.some((s) => s.type === "carousel")).toBe(false);
  });

  test("image-only paragraphs count as carousel run", () => {
    const html = `
      <p><img src="/uploads/1.jpg"></p>
      <p><img src="/uploads/2.jpg"></p>
    `;
    const segs = parseArticleBody(html);
    const carousel = segs.find((s) => s.type === "carousel");
    expect(carousel?.images).toHaveLength(2);
  });
});
