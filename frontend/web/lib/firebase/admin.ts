import 'server-only';

import type { AppOptions } from 'firebase-admin/app';
import {
  getApps,
  initializeApp as initializeAdminApp,
  cert,
} from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import type { Auth } from 'firebase-admin/auth';
import { getFirestore } from 'firebase-admin/firestore';
import type { Firestore } from 'firebase-admin/firestore';
import type { ServiceAccount } from 'firebase-admin';

/**
 * Firebase Admin SDK のアプリ (singleton)
 */
function createFirebaseAdminApp(): ReturnType<typeof initializeAdminApp> {
  const adminApps = getApps();
  if (adminApps.length > 0) {
    console.info('[Firebase Admin] Use existing admin app');
    return adminApps[0];
  }

  // Emulator を使うかどうかのフラグ
  const useEmulator = process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === 'true';

  const adminOptions: AppOptions = useEmulator
    ? {
        projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
      }
    : {
        credential: cert({
          projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
          clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
          // 改行文字を正しく復元
          privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
        } as ServiceAccount),
      };
  return initializeAdminApp(adminOptions);
}

export const adminApp = createFirebaseAdminApp();

/**
 * Firestore
 */
export const adminDb: Firestore = getFirestore(adminApp);

/**
 * Auth
 */
export const adminAuth: Auth = getAuth(adminApp);
