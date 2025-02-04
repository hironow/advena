'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { signIn as nextAuthSignIn, useSession } from 'next-auth/react';

import { useGoogleAuth } from '@/hooks/use-google-auth';
import { Button } from '@/components/ui/button';

export default function Page() {
  const router = useRouter();
  const { data: session, status } = useSession();
  console.info('client component session: ', session);
  console.info('client component status: ', status);

  const isLoggedIn = status === 'authenticated';

  const { signInWithPopup, signOut } = useGoogleAuth();

  const handleSignInWithPopup = () => {
    signInWithPopup()
      .then((credential) => credential.user.getIdToken(true))
      .then((idToken) => nextAuthSignIn('credentials', { idToken }))
      .catch((err) => {
        console.error('Google sign in error:', err);
        toast.error('Failed to sign in with Google');
      });
  };

  const handleSignOut = () => {
    signOut().catch(console.error);
  };

  return (
    <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
      <div className="w-full max-w-md overflow-hidden rounded-2xl flex flex-col gap-12">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
          <h3 className="text-xl font-semibold dark:text-zinc-50">Sign In</h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400">
            Use your Google Account to sign in
          </p>
        </div>
        <div className="flex flex-col gap-4 px-4 sm:px-16">
          <Button onClick={handleSignInWithPopup} disabled={isLoggedIn}>
            Sign In with Google
          </Button>
          <p className="text-center text-sm text-gray-600 mt-4 dark:text-zinc-400">
            {"Don't have an account? "}
            <Link
              href="/register"
              className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
            >
              Sign up
            </Link>
            {' for free.'}
          </p>
        </div>

        {isLoggedIn && (
          <div className="flex flex-col gap-4 px-4 sm:px-16">
            <Button onClick={handleSignOut}>Sign Out</Button>
          </div>
        )}
      </div>
    </div>
  );
}
