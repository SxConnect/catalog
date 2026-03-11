/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    images: {
        domains: ['mins3.sxconnect.com.br', 'localhost'],
    },
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    },
    experimental: {
        serverComponentsExternalPackages: [],
    },
    // Configurações para melhorar estabilidade
    swcMinify: true,
    reactStrictMode: true,
    // Configurações para evitar problemas de hidratação
    compiler: {
        removeConsole: process.env.NODE_ENV === 'production',
    },
}

module.exports = nextConfig
