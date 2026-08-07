import { render, screen, fireEvent } from "@testing-library/react";
import SiteHeader from "../SiteHeader";

jest.mock("../../lib/site-context", () => ({
  useSite: () => ({
    settings: { siteName: "AIA Legnano" },
    loading: false,
    nav: [
      { id: "home", href: "/", label: "Home", order: 1 },
      { id: "chi", href: "/chi-siamo", label: "Chi Siamo", order: 2 },
      { id: "des", href: "/designazioni", label: "Designazioni", order: 3 },
    ],
  }),
}));

function mockMatchMedia(matchesInline) {
  window.matchMedia = jest.fn().mockImplementation((query) => ({
    matches: matchesInline,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
}

describe("SiteHeader", () => {
  it("mobile: hamburger only (no inline CTA buttons until menu opens)", () => {
    mockMatchMedia(false);
    render(<SiteHeader />);
    expect(screen.getByTestId("site-header")).toHaveAttribute("data-nav-mode", "compact");
    expect(screen.getByTestId("header-mobile-toggle")).toBeInTheDocument();
    expect(screen.queryByTestId("mobile-menu")).not.toBeInTheDocument();
    // CTAs not visible until menu opens
    expect(screen.queryByTestId("header-cta-diventa-arbitro")).not.toBeInTheDocument();
    expect(screen.queryByTestId("nav-link-area-associati")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("header-mobile-toggle"));
    expect(screen.getByTestId("mobile-menu")).toBeInTheDocument();
    expect(screen.getByTestId("header-cta-diventa-arbitro")).toBeInTheDocument();
    expect(screen.getByTestId("nav-link-area-associati")).toBeInTheDocument();
    expect(screen.getByText("Chi Siamo")).toBeInTheDocument();
  });

  it("desktop: shows CTA buttons inline", () => {
    mockMatchMedia(true);
    render(<SiteHeader />);
    expect(screen.getByTestId("site-header")).toHaveAttribute("data-nav-mode", "inline");
    expect(screen.queryByTestId("header-mobile-toggle")).not.toBeInTheDocument();
    expect(screen.getByTestId("header-cta-diventa-arbitro")).toBeInTheDocument();
    expect(screen.getByTestId("nav-link-area-associati")).toBeInTheDocument();
  });
});
