import 'server-only';

// serverから参照される firestore access library

import { Timestamp, FieldValue } from 'firebase-admin/firestore';

import { getAdminDb } from '../firebase/admin';
import { type User, USER_COLLECTION } from './types';

export const addUserAdmin = async (uid: string): Promise<void> => {
  try {
    const adminDb = getAdminDb();
    await adminDb.collection(USER_COLLECTION).doc(uid).set({
      uid: uid,
      createdAt: FieldValue.serverTimestamp(),
      status: 'creating',
    });
    console.info(`[COMMAND] ${USER_COLLECTION} creating`);
    console.info(`[COMMAND] not yet assigned id`);
  } catch (error) {
    console.error('Error adding document: ', error);
  }
};

export const getUserByUidAdmin = async (uid: string): Promise<User | null> => {
  const adminDb = getAdminDb();
  const docRef = adminDb.collection(USER_COLLECTION).doc(uid);
  const doc = await docRef.get();
  if (!doc.exists) {
    return null;
  }
  return doc.data() as User;
};
