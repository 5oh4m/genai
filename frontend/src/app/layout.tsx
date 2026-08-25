import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "AEGIS-AI — Adversarial Cyber Defense Simulation",
  description: "Real-time adversarial AI fraud detection simulation platform — Red vs Blue Team command center.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable}`}>
        <div className="app-shell">
          <header className="top-nav">
            <div className="brand">
              <div className="brand-hex"></div>
              <span className="brand-name">AEGIS-AI</span>
              <span className="brand-sub">SIMULATION ENGINE</span>
            </div>

            <nav className="nav-tabs">
              <Link href="/" className="nav-tab"><span>⚡</span> Stream</Link>
              <Link href="/attack" className="nav-tab"><span>🎯</span> Red Team</Link>
              <Link href="/defense" className="nav-tab"><span>🛡</span> Blue Team</Link>
              <Link href="/threats" className="nav-tab"><span>🔬</span> Threats</Link>
              <Link href="/sandbox" className="nav-tab"><span>🧪</span> Sandbox</Link>
            </nav>

            <div className="nav-right">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', fontWeight: 600, color: 'var(--danger-color)' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--danger-color)' }}></div>
                LIVE
              </div>
            </div>
          </header>

          <main className="main-viewport">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
