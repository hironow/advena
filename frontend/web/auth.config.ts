import type { NextAuthConfig } from 'next-auth';

export const authConfig = {
  debug: true,
  pages: {
    signIn: '/login',
    signOut: '/',
    error: '/status', // TODO: 状態ページを作成する (メンテナンス中含む)
    newUser: '/',
  },
  providers: [
    // added later in auth.ts since it requires bcrypt which is only compatible with Node.js
    // while this file is also used in non-Node.js environments (e.g. Edge Runtime)
  ],
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isOnRoot = nextUrl.pathname.startsWith('/');
      const isOnLogin = nextUrl.pathname.startsWith('/login');

      if (isLoggedIn && isOnLogin) {
        return Response.redirect(new URL('/', nextUrl as unknown as URL));
      }

      if (isOnLogin) {
        return true; // Always allow access to login pages
      }

      if (isOnRoot) {
        if (isLoggedIn) return true;
        return false; // Redirect unauthenticated users to login page
      }

      if (isLoggedIn) {
        return Response.redirect(new URL('/', nextUrl as unknown as URL));
      }

      return true;
    },
  },
} satisfies NextAuthConfig;
