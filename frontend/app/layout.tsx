import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Lenny Growth Assistant",
  description: "AI-powered growth assistant grounded in Lenny Rachitsky's podcast interviews.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
