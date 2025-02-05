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
          privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
        } as ServiceAccount),
      };

export const adminApp = getApps()[0] ?? initializeAdminApp(options);

/**
 * Firestore
 */
export const adminDb: Firestore = getFirestore(adminApp);

/**
 * Auth
 */
export const adminAuth: Auth = getAuth(adminApp);
