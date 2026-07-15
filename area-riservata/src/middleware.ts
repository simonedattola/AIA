export { default } from "next-auth/middleware";

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/profilo",
    "/calendario",
    "/area-tecnica",
    "/storico",
    "/news",
    "/premi",
    "/media",
    "/messaggi",
    "/admin/:path*",
  ],
};
