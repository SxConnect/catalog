/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        return [
            {
                source: '/api-proxy/:path*',
                destination: 'http://sixpet-catalog-api:8000/api/:path*',
            },
        ];
    },
};

module.exports = nextConfig;