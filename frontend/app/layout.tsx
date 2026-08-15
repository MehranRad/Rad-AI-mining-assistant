import type { Metadata } from "next";
import { Vazirmatn, Manrope } from "next/font/google";
import "./globals.css";

const vazirmatn = Vazirmatn({
  subsets: ["arabic", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-vazirmatn",
});

const manrope = Manrope({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-manrope",
});

export const metadata: Metadata = {
  title: "Rad AI — Mining Intelligence",
  description: "AI-powered intelligence for smarter mining operations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa">
      <body
        className={`${vazirmatn.variable} ${manrope.variable} antialiased`}
        style={{
          fontFamily: "var(--font-vazirmatn), sans-serif",
          background:
            "linear-gradient(120deg, #2b2115 0%, #352818 35%, #3d2e1a 55%, #34281a 75%, #2a2015 100%)",
          minHeight: "100vh",
        }}
      >
        {children}
      </body>
    </html>
  );
}