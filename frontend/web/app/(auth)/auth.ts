import { compare } from 'bcrypt-ts';
import NextAuth, { type User, type Session } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';

import { getUser } from '@/lib/db/queries';

import { authConfig } from './auth.config';

interface ExtendedSession extends Session {
  user: User;
}

export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut,
} = NextAuth({
  ...authConfig,
  providers: [
    // Google,
    // NOTE: Googleを使うと、firebase auth emulatorで動作しないため、カスタム認証を使う
    // see: https://authjs.dev/getting-started/authentication/credentials?framework=next-js
    Credentials({
      credentials: {
        idToken: { label: 'ID Token', type: 'text' },
      },
      async authorize({ idToken }: any) {
        console.info('idToken', idToken);
        // const users = await getUser(email);
        // if (users.length === 0) return null;
        // // biome-ignore lint: Forbidden non-null assertion.
        // const passwordsMatch = await compare(password, users[0].password!);
        // if (!passwordsMatch) return null;
        // return users[0] as any;

        return null;
      },
    }),
  ],
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
