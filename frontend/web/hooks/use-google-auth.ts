'use client';

import { auth } from '@/lib/firebase/client';
import {
  GoogleAuthProvider,
  signInWithPopup as firebaseSignInWithPopup,
} from 'firebase/auth';
import { signOut as nextAuthSignOut } from 'next-auth/react';
// firebase auth側のsignOutを使いたい場合: 現状想定なし
// import { signOut as firebaseSignOut } from 'firebase/auth';
import { useCallback, useMemo, useState } from 'react';

export function useGoogleAuth() {
  const provider = useMemo(() => {
    const prov = new GoogleAuthProvider();
    // 例: ユーザーに毎回アカウント選択を促す
    // prov.setCustomParameters({ prompt: 'select_account' });
    return prov;
  }, []);

  const handleSignInWithPopup = useCallback(() => {
    return firebaseSignInWithPopup(auth, provider);
  }, [provider]);

  const handleSignOut = useCallback(async () => {
    return nextAuthSignOut();
  }, []);

  return {
    signInWithPopup: handleSignInWithPopup,
    signOut: handleSignOut,
  };
}
