import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import SiteHeader from "../SiteHeader";
import MobileNavMenu from "../MobileNavMenu";
import PageBrandBar from "../PageBrandBar";

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

function wrap(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("SiteHeader", () => {
  it("mobile: no white header bar (menu lives in page brand row)", () => {
    mockMatchMedia(false);
    wrap(<SiteHeader />);
    expect(screen.queryByTestId("site-header")).not.toBeInTheDocument();
  });

  it("desktop: shows CTA buttons inline", () => {
    mockMatchMedia(true);
    wrap(<SiteHeader />);
    expect(screen.getByTestId("site-header")).toHaveAttribute("data-nav-mode", "inline");
    expect(screen.queryByTestId("header-mobile-toggle")).not.toBeInTheDocument();
    expect(screen.getByTestId("header-cta-diventa-arbitro")).toBeInTheDocument();
    expect(screen.getByTestId("nav-link-area-associati")).toBeInTheDocument();
  });
});

describe("MobileNavMenu / PageBrandBar", () => {
  it("mobile: hamburger opens menu with CTAs", () => {
    mockMatchMedia(false);
    wrap(<PageBrandBar />);
    expect(screen.getByTestId("page-brand-bar")).toBeInTheDocument();
    expect(screen.getByTestId("header-mobile-toggle")).toBeInTheDocument();
    expect(screen.queryByTestId("mobile-menu")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("header-mobile-toggle"));
    expect(screen.getByTestId("mobile-menu")).toBeInTheDocument();
    expect(screen.getByTestId("header-cta-diventa-arbitro")).toBeInTheDocument();
    expect(screen.getByTestId("nav-link-area-associati")).toBeInTheDocument();
    expect(screen.getByText("Chi Siamo")).toBeInTheDocument();
  });

  it("desktop: MobileNavMenu is hidden", () => {
    mockMatchMedia(true);
    wrap(<MobileNavMenu />);
    expect(screen.queryByTestId("mobile-nav-menu")).not.toBeInTheDocument();
  });
});
