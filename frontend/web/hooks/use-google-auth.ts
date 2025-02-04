'use client';

import { auth } from '@/lib/firebase/client';
import {
  GoogleAuthProvider,
  signInWithPopup as firebaseSignInWithPopup,
} from 'firebase/auth';
import { signOut as nextAuthSignOut } from 'next-auth/react';
// import { signOut as firebaseSignOut } from 'firebase/auth';
import { useCallback, useMemo, useState } from 'react';

export function useGoogleAuth() {
  const provider = useMemo(() => {
    const prov = new GoogleAuthProvider();
    // 例: ユーザーに毎回アカウント選択を促す
    // prov.setCustomParameters({ prompt: 'select_account' });
    return prov;
  }, []);

  // ローディング状態とエラー状態を追加
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const signInWithPopup = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await firebaseSignInWithPopup(auth, provider);
      // 必要に応じて result からユーザー情報やトークンを抽出
      return result;
    } catch (err) {
      setError(err as Error);
      console.error('Error during sign in:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [provider]);

  const signOut = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Firebase Authもサインアウトさせたい場合は、以下を有効にする
      // await firebaseSignOut(auth);
      await nextAuthSignOut({ redirectTo: '/' });
    } catch (err) {
      setError(err as Error);
      console.error('Error during sign out:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    auth,
    provider,
    signInWithPopup,
    signOut,
    loading,
    error,
  };
}
