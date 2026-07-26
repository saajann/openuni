import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenUni | RAG Demo",
  description: "Ask questions about any university and get cited answers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
