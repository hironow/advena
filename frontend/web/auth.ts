import Credentials from 'next-auth/providers/credentials';

import { adminAuth } from '@/lib/firebase/admin';
import { signInSchema } from './lib/zod';
import NextAuth from 'next-auth';

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    // Google,
    // callback url: [origin]/api/auth/callback/google
    // NOTE: Googleを使うと、firebase auth emulatorで動作しないため、カスタム認証を使う
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
            // uid: decoded.uid,
          };
        } catch (error) {
          console.error('Error during authorization:', error);
          throw new Error('Authorization failed');
        }
      },
    }),
  ],
  // callbacks: {
  //   async jwt({ token, user }) {
  //     if (user) {
  //       token.id = user.id;
  //     }

  //     return token;
  //   },
  //   async session({
  //     session,
  //     token,
  //   }: {
  //     session: ExtendedSession;
  //     token: any;
  //   }) {
  //     if (session.user) {
  //       session.user.id = token.id as string;
  //     }

  //     return session;
  //   },
  // },
});
