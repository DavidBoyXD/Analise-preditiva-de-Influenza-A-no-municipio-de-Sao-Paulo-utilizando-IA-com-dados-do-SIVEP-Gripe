import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dashboard de Influenza A - Municipio de Sao Paulo",
  description:
    "Protótipo academico (TCC) de analise preditiva de Influenza A no municipio de Sao Paulo, com dados do SIVEP-Gripe/DATASUS.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
