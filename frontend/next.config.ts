import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  /* config options here */
   images: {
    // Add the domain(s) where your profile images are hosted
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'lh3.googleusercontent.com', // 👈 This is the common domain for Google profile images
      },
      // You may need to add other domains if you support different providers
      // {
      //   protocol: 'https',
      //   hostname: 'platform-lookaside.fbsbx.com', // Example for Facebook
      // },
    ],
  },
};

export default nextConfig;
