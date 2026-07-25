import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenUni",
  description: "Ask a question about your university and get a cited answer.",
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
