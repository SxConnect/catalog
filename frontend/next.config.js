/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    images: {
        domains: ['mins3.sxconnect.com.br', 'localhost'],
    },
    experimental: {
        serverActions: false,
    },
}

module.exports = nextConfig
