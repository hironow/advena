import NextAuth from 'next-auth';
import { authConfig } from './auth.config';
import { getAdminAuth } from '@/lib/firebase/admin';
import { signInSchema } from '@/lib/zod';
import type { DefaultSession, Session } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';

interface ExtendedSession extends Session {
  user: {
    id: string; // firestore user uuid
    uid?: string; // firebase auth uid (not uuid)
  } & DefaultSession['user'];
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  debug: true,
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
          const adminAuth = getAdminAuth();

          const { idToken } = await signInSchema.parseAsync(credentials);
          console.info('got idToken: ', idToken);
          const decoded = await adminAuth.verifyIdToken(idToken);
          console.info('decoded: ', decoded);

          // NOTE: ここでfirebaseのauthを使ってユーザーを取得/作成する

          return {
            ...decoded,
            id: '42',
            uid: decoded.uid,
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
      return { ...token, ...user };
    },
    async session({
      session,
      token,
    }: { session: ExtendedSession; token: any }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.uid = token.uid as string;
      }
      return session;
    },
  },
});
