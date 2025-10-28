/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export', // Static export for Firebase Hosting
  images: {
    unoptimized: true, // Firebase Hosting doesn't support Image Optimization
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  trailingSlash: true, // Firebase Hosting recommendation
};

module.exports = nextConfig;
