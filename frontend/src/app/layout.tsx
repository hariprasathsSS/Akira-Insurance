import type { Metadata } from "next";
import { Inter, Newsreader } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const newsreader = Newsreader({
  subsets: ["latin"],
  style: ["normal", "italic"],
  variable: "--font-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AKIRA INSURANCE — Claims AI & Policy Operations",
  description: "Modern enterprise insurance intelligence with Japanese watercolor editorial minimalism.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${newsreader.variable}`}>
      <body className="antialiased min-h-screen bg-paper text-ink font-sans selection:bg-aoi-wash selection:text-ink">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
