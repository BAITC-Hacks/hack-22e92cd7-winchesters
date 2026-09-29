import type { NextConfig } from "next";

// Set only in the Docker build (frontend/Dockerfile). The browser then calls
// /api/... on its own origin and Next proxies it to the backend container.
// Local `next dev` leaves it unset and talks to NEXT_PUBLIC_API_URL directly.
const backend = process.env.BACKEND_INTERNAL_URL;

const nextConfig: NextConfig = {
  output: "standalone",
  ...(backend && {
    // FastAPI routes such as /api/candidates/ need their trailing slash; Next's
    // default redirect would strip it and FastAPI would redirect straight back
    // to the internal backend host.
    skipTrailingSlashRedirect: true,
    async rewrites() {
      return [
        { source: "/api/:path*/", destination: `${backend}/api/:path*/` },
        { source: "/api/:path*", destination: `${backend}/api/:path*` },
      ];
    },
  }),
};

export default nextConfig;
