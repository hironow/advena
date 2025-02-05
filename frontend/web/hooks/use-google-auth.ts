'use client';

import { auth } from '@/lib/firebase/client';
import {
  GoogleAuthProvider,
  signInWithPopup as firebaseSignInWithPopup,
  signInWithRedirect as firebaseSignInWithRedirect,
} from 'firebase/auth';
import { signOut as nextAuthSignOut } from 'next-auth/react';
// firebase auth側のsignOutを使いたい場合: 現状想定なし
// import { signOut as firebaseSignOut } from 'firebase/auth';
import { useCallback, useMemo } from 'react';

export function useGoogleAuth() {
  const provider = useMemo(() => {
    const prov = new GoogleAuthProvider();
    // 例: ユーザーに毎回アカウント選択を促す 他には 'login_hint auto_select' もある
    prov.setCustomParameters({ prompt: 'select_account' });
    return prov;
  }, []);

  const handleSignInWithPopup = useCallback(() => {
    // WithRedirectは後続のnext-authと競合するので注意
    return firebaseSignInWithRedirect(auth, provider);
  }, [provider]);

  const handleSignOut = useCallback(async () => {
    return nextAuthSignOut();
  }, []);

  return {
    signInWithPopup: handleSignInWithPopup,
    signOut: handleSignOut,
  };
}
