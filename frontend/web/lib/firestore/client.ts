'use client';

// clientから参照される firestore access library
// firebase packageのfirestoreを利用しているが、firebase-admin packageのfirestoreは利用しないこと

import { db } from '../firebase/client';
import {
  addDoc,
  collection,
  deleteDoc,
  doc,
  getDoc,
  getDocs,
  getFirestore,
  increment,
  onSnapshot,
  orderBy,
  query,
  runTransaction,
  serverTimestamp,
  setDoc,
  Timestamp,
  updateDoc,
  where,
} from 'firebase/firestore';
import { type User, USER_COLLECTION } from './types';

// Status: firestoreのdocumentの状態を表す
// -ingは「command」として、-edは「event」として使われ、eventarcを通して backend に通知される
// creating: documentの作成中
// created: documentの作成完了
// deleting: documentの削除中
// error: エラー発生時

type GetUserSnapshotCallback = (user: User) => void;

export const getUserSnapshot = (uid: string, cb: GetUserSnapshotCallback) => {
  const q = doc(db, USER_COLLECTION, uid);
  const unsubscribe = onSnapshot(q, (doc) => {
    const user = {
      ...doc.data(),
    } as User;
    cb(user);
  });
  return unsubscribe;
};

export const addUser = async (uid: string): Promise<void> => {
  try {
    await setDoc(doc(db, USER_COLLECTION, uid), {
      uid: uid,
      createdAt: serverTimestamp(),
      status: 'creating',
    });
    console.info(`[COMMAND] ${USER_COLLECTION} creating`);
    console.info(`[COMMAND] not yet assigned id`);
  } catch (error) {
    console.error('Error adding document: ', error);
  }
};

export const getUserByUid = async (uid: string): Promise<User> => {
  const docRef = await getDoc(doc(db, USER_COLLECTION, uid));
  return {
    ...docRef.data(),
  } as User;
};
