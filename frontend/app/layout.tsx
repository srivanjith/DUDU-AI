import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "DODO — Your AI. Your Machine. Your Rules.",
  description: "Autonomous AI Agent and AI Software Development Environment",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased select-none">{children}</body>
    </html>
  );
}

