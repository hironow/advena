import NextAuth from 'next-auth';
import { authConfig } from './auth.config';
import { adminAuth } from '@/lib/firebase/admin';
import { signInSchema } from '@/lib/zod';
import type { Session } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
interface ExtendedSession extends Session {}

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  providers: [
    // Google,
    // NOTE: Google Providerを使うとfirebase auth emulatorで動作しない。カスタム認証を使う
    // see: https://authjs.dev/getting-started/authentication/credentials?framework=next-js
    Credentials({
      credentials: {
        idToken: { label: 'ID Token', type: 'text' },
      },
      authorize: async (credentials) => {
        try {
          const { idToken } = await signInSchema.parseAsync(credentials);
          console.info('got idToken: ', idToken);
          const decoded = adminAuth.verifyIdToken(idToken);
          console.info('decoded: ', decoded);
          return {
            ...decoded,
            id: '1',
            // uid: decoded.uid,
          };
        } catch (error) {
          console.error('Error during authorization:', error);
          throw new Error('Authorization failed');
        }
      },
    }),
  ],
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({
      session,
      token,
    }: {
      session: ExtendedSession;
      token: any;
    }) {
      if (session.user) {
        session.user.id = token.id as string;
      }
      return session;
    },
  },
});

declare module 'next-auth' {
  interface Session {
    idToken?: string;
  }
}
