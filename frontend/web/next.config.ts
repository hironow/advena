import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'standalone',
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      {
        hostname: 'avatar.vercel.sh',
      },
    ],
  },
};

// Next.jsのビルド時に環境変数を確認する
console.info(
  Object.keys(process.env)
    .filter((key) => key.includes('NEXT_PUBLIC'))
    .map((key) => `${key} = ${process.env[key]}`),
);

export default nextConfig;
