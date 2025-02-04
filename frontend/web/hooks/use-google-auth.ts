'use client';

import { auth } from '@/lib/firebase/client';
import {
  GoogleAuthProvider,
  signInWithPopup as firebaseSignInWithPopup,
} from 'firebase/auth';
// next-auth の signOut を利用
import { signOut as nextAuthSignOut } from 'next-auth/react';
// Firebase Auth の signOut を利用する場合はこちらを使用
// import { signOut as firebaseSignOut } from 'firebase/auth';
import { useCallback, useMemo, useState } from 'react';

export function useGoogleAuth() {
  // プロバイダは一度だけ生成する
  const provider = useMemo(() => {
    const prov = new GoogleAuthProvider();
    // 例: ユーザーに毎回アカウント選択を促す
    prov.setCustomParameters({ prompt: 'select_account' });
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
      // Firebase 側もサインアウトさせたい場合は、以下を有効にする
      // await firebaseSignOut(auth);
      // next-auth の signOut を利用（オプションでリダイレクトの有無なども指定可能）
      await nextAuthSignOut({ redirect: false });
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
