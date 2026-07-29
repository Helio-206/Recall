import type { Metadata } from "next";

import { AppSplash } from "@/components/layout/app-splash";

import "./globals.css";

export const metadata: Metadata = {
  title: "Recall",
  description: "A Learning OS for structured internet video learning.",
  icons: {
    icon: "/recall-mark.svg",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body>
        <div className="app-vignette" />
        <AppSplash />
        {children}
      </body>
    </html>
  );
}
