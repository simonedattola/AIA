import { render, screen } from "@testing-library/react";
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

describe("SiteHeader", () => {
  beforeEach(() => {
    window.matchMedia = jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));
  });

  it("renders brand and Area Associati CTA", () => {
    render(<SiteHeader />);
    expect(screen.getByTestId("site-header")).toBeInTheDocument();
    expect(screen.getByAltText(/AIA Legnano/i)).toBeInTheDocument();
    expect(screen.getByTestId("nav-link-area-associati")).toBeInTheDocument();
    expect(screen.getByText(/Area Associati/i)).toBeInTheDocument();
  });

  it("renders Diventa Arbitro CTA", () => {
    render(<SiteHeader />);
    expect(screen.getByTestId("header-cta-diventa-arbitro")).toBeInTheDocument();
  });
});
