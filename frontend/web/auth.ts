import NextAuth from 'next-auth';
import { authConfig } from './auth.config';
import { getAdminAuth } from '@/lib/firebase/admin';
import { signInSchema } from '@/lib/zod';
import type { DefaultSession, Session } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import {
  addUserAdmin,
  getUserByFirebaseUidAdmin,
} from '@/lib/firestore/admin-db';
import type { User } from '@/lib/firestore/types';

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

          // NOTE: firebase auth uidを使ってユーザーを一意に識別する
          let userInFirestore: User | null = null;
          userInFirestore = await getUserByFirebaseUidAdmin(decoded.uid);
          if (userInFirestore === null) {
            console.info('User not found, creating user');
            await addUserAdmin(decoded.uid);
            userInFirestore = await getUserByFirebaseUidAdmin(decoded.uid);
          }
          // NOTE: 以降、userIdはサービス内で付与したuuidを使い、基本的にfirebase auth uidは使わない
          return {
            ...decoded,
            id: userInFirestore?.id, // firestore user uuid
            uid: decoded.uid, // firebase auth uid (not uuid)
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
