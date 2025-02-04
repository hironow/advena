import NextAuth from 'next-auth';
import { authConfig } from '@/auth.config';

const authMiddleware = NextAuth(authConfig).auth;

const customMiddleware = (req: any) => {
  console.log("customMiddleware", req.auth); //  { session: { user: { ... } } }
};

const publicPaths = ['/login', '/terms', '/privacy'];
const publicPathsRegex = RegExp(`^(${publicPaths.join('|')})?/?$`, 'i');

export async function middleware(req: any) {
  const isPublicPath = publicPathsRegex.test(req.nextUrl.pathname);
  if (isPublicPath) {
    return customMiddleware(req);
  }
  return (authMiddleware as any)(req);
}

// Optionally, don't invoke Middleware on some paths
export const config = {
  /*
   * Match all routes except for the following:
   * - api/* (API routes)
   * - _next/static/* (static files)
   * - _next/image* (image optimization files)
   * - assets/* (static files)
   * - images/* (static files)
   * - fonts/* (static files)
   * - favicon.ico
   * - robots.txt
   * - home page (root route)
   */
  matcher: [
    '/((?!api|_next/static|_next/image|assets|images|fonts|favicon.ico|robots.txt|$).*)',
  ],
};
