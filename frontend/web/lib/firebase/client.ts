'use client';

import type { FirebaseOptions } from 'firebase/app';
import { getApps, initializeApp as initializeClientApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import type { Auth } from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';
import type { Firestore } from 'firebase/firestore';
import { getStorage, connectStorageEmulator } from 'firebase/storage';

// see: https://firebase.google.com/docs/web/setup#available-libraries

/**
 * Firebase のクライアントアプリ (singleton)
 */
function createFirebaseClientApp(): ReturnType<typeof initializeClientApp> {
  const clientApps = getApps();
  if (clientApps.length > 0) {
    console.info('[Firebase] Use existing client app');
    return clientApps[0];
  }

  console.info('[Firebase] Initialize client app');
  const options: FirebaseOptions = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
    measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
  };
  return initializeClientApp(options);
}

export const app = createFirebaseClientApp();

export const db: Firestore = getFirestore(app);
if (process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === 'true') {
  connectFirestoreEmulator(db, '127.0.0.1', 8080);
  console.info('[Firebase] Using Firestore emulator');
}

export const auth: Auth = getAuth(app);
if (process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === 'true') {
  connectAuthEmulator(auth, 'http://127.0.0.1:9099');
  console.info('[Firebase] Using Auth emulator');
}

export const storage = getStorage(app);
if (process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === 'true') {
  connectStorageEmulator(storage, '127.0.0.1', 9199);
  console.info('[Firebase] Using Storage emulator');
}

// TODO: RemoteConfig
