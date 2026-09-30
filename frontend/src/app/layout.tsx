import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";

// The brand face from the Figma designs; these files cover Russian and Kazakh too.
const gilroy = localFont({
  variable: "--font-gilroy",
  display: "swap",
  src: [
    { path: "./fonts/Gilroy-Regular.woff2", weight: "400" },
    { path: "./fonts/Gilroy-Medium.woff2", weight: "500" },
    { path: "./fonts/Gilroy-Semibold.woff2", weight: "600" },
    { path: "./fonts/Gilroy-Bold.woff2", weight: "700" },
  ],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "InVision U — AI-Powered Admissions Platform",
  description:
    "AI-powered candidate scoring and ranking for InVision U admissions",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${gilroy.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-subtle text-ink">
        {children}
      </body>
    </html>
  );
}
