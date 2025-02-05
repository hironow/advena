import 'server-only';

import type { AppOptions } from 'firebase-admin/app';
import {
  getApps,
  initializeApp as initializeAdminApp,
  cert,
} from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import { getFirestore } from 'firebase-admin/firestore';
import type { ServiceAccount } from 'firebase-admin';

/**
 * Firebase Admin SDK のアプリ (singleton)
 */
let adminApp: ReturnType<typeof initializeAdminApp> | null = null;
const getAdminApp = () => {
  if (!adminApp) {
    const options: AppOptions =
      process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === 'true'
        ? {
            projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
          }
        : {
            credential: cert({
              projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
              clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
              // 改行文字を正しく復元
              privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(
                /\\n/g,
                '\n',
              ),
            } as ServiceAccount),
          };

    // 初回呼び出し時にのみ初期化
    adminApp = getApps()[0] ?? initializeAdminApp(options);
  }
  return adminApp;
};

export const getAdminDb = () => {
  return getFirestore(getAdminApp());
};

export const getAdminAuth = () => {
  return getAuth(getAdminApp());
};
