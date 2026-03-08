import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "SixPet Catalog Manager",
    description: "Gerenciador de catálogos de produtos pet",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://catalog-api.sxconnect.com.br";

    return (
        <html lang="pt-BR">
            <head>
                <script
                    dangerouslySetInnerHTML={{
                        __html: `window.__API_URL__ = "${apiUrl}";`,
                    }}
                />
            </head>
            <body className={inter.className}>
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
