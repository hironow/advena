import NextAuth from 'next-auth';
import { authConfig } from './auth.config';
import { getAdminAuth } from '@/lib/firebase/admin';
import { signInSchema } from '@/lib/zod';
import type { DefaultSession, Session } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { addUser, getUserByUid } from './lib/firestore/client';
import { User } from './lib/firestore/types';

interface ExtendedSession extends Session {
  user: {
    id: string; // firestore user uuid
    uid?: string; // firebase auth uid (not uuid)
  } & DefaultSession['user'];
}

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
          const adminAuth = getAdminAuth();

          const { idToken } = await signInSchema.parseAsync(credentials);
          console.info('got idToken: ', idToken);
          const decoded = await adminAuth.verifyIdToken(idToken);
          console.info('decoded: ', decoded);

          // NOTE: ここでfirebaseのauth uidを使ってユーザーを取得/作成する
          let userInFirestore: User;
          userInFirestore = await getUserByUid(decoded.uid);
          console.info('userInFirestore: ', userInFirestore);
          if (!userInFirestore) {
            console.info('User not found, creating user');
            await addUser(decoded.uid); // adminのfirestoreの方がいい？
            userInFirestore = await getUserByUid(decoded.uid);
          }

          return {
            ...decoded,
            id: userInFirestore.id,
            uid: decoded.uid,
          };
        } catch (error) {
          console.error('Error during authorization:', error);
          throw new Error('Authorization failed throw error');
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
