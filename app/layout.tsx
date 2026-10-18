import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CRAG Intelligence Platform",
  description: "Corrective RAG — Cross-Encoder Reranking, 3-Tier Grading, Ambiguous Resolution",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          <Navbar />
          <div style={{ display: "flex" }}>
            <Sidebar />
            <main style={{ flex: 1, marginLeft: 64, marginTop: 64, minHeight: "calc(100vh - 64px)" }}>
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
