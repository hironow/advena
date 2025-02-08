'use client';

import { toast } from 'sonner';
import {
  signIn as nextAuthSignIn,
  signOut as nextAuthSignOut,
  useSession,
} from 'next-auth/react';
import { useGoogleAuth } from '@/hooks/use-google-auth';
import { Button } from '@/components/ui/button';

export default function AuthButton() {
  const { data: session, status } = useSession();
  const isLoggedIn = status === 'authenticated';
  const { signInWithPopup, signOut } = useGoogleAuth();

  const handleSignIn = () => {
    signInWithPopup()
      .then((credential) => credential.user.getIdToken(true))
      .then((idToken) =>
        nextAuthSignIn('credentials', { idToken, redirect: false }),
      )
      .catch((err) => {
        console.error('Google sign in error:', err);
        toast.error('Failed to sign in with Google');
      });
  };

  const handleSignOut = () => {
    signOut()
      .then(() => nextAuthSignOut())
      .catch((err) => {
        console.error('Google sign out error:', err);
        toast.error('Failed to sign out');
      });
  };

  const handleClick = () => {
    if (isLoggedIn) {
      handleSignOut();
    } else {
      handleSignIn();
    }
  };

  return (
    <Button onClick={handleClick}>
      {isLoggedIn ? 'Sign Out' : 'Sign In with Google'}
    </Button>
  );
}
