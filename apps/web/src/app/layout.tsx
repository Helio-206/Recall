import type { Metadata } from "next";

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
        {children}
      </body>
    </html>
  );
}
