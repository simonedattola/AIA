import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers/Providers";

export const metadata: Metadata = {
  title: "Area Riservata | AIA Legnano",
  description: "Portale associati sezione arbitrale AIA Legnano",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
