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
import { RADIO_SHOW_COLLECTION, USER_COLLECTION } from './types';
import type { User } from './generated/entity_user';
import type { RadioShow } from './generated/entity_radio_show';

// Status: firestoreのdocumentの状態を表す
// -ingは「command」として、-edは「event」として使われ、eventarcを通して backend に通知される
// creating: documentの作成中
// created: documentの作成完了
// deleting: documentの削除中
// error: エラー発生時

type GetUserSnapshotCallback = (user: User) => void;

export const getUserSnapshot = (
  userId: string,
  cb: GetUserSnapshotCallback,
) => {
  const q = doc(db, USER_COLLECTION, userId);
  const unsubscribe = onSnapshot(q, (doc) => {
    const user = {
      ...doc.data(),
    } as User;
    cb(user);
  });
  return unsubscribe;
};

export const getUserByUid = async (userId: string): Promise<User> => {
  const docRef = await getDoc(doc(db, USER_COLLECTION, userId));
  return {
    ...docRef.data(),
  } as User;
};

// ラジオ status (仮 & 最も複雑版):
// concepting
//    ↓
// concepted
//    ↓
// scripting
//    ↓
// scripted
//    ↓
// ┌──────────────┐
// │ (オプション)
// │ rehearsing
// │   ↓
// │ rehearsed
// └──────────────┘
//    ↓（リハーサルがあった場合は rehearsed、なければ scripted）
// recording
//    ↓
// recorded
//    ↓
// editing
//    ↓
// edited
//    ↓
// approving
//    ↓
// approved
//    ↓
// scheduling
//    ↓
// scheduled
//    ↓
// publishing
//    ↓
// published
//    ↓
// ┌─────────────────────────────┐
// │         分岐
// │  [アーカイブの場合]
// │      archiving → archived
// │  [ライブ放送の場合]
// │      broadcasting → broadcasted
// └─────────────────────────────┘

type getRadioShowsSnapshotCallback = (radioShows: RadioShow[]) => void;

export const getRadioShowsSnapshot = (cb: getRadioShowsSnapshotCallback) => {
  const q = query(
    // status が published のものだけ取得、published_at でソート、最新の公開が0番目
    collection(db, RADIO_SHOW_COLLECTION),
    where('status', '==', 'published'),
    orderBy('published_at', 'desc'),
  );
  const unsubscribe = onSnapshot(q, (querySnapshot) => {
    const radioShows = querySnapshot.docs.map(
      (doc) =>
        ({
          id: doc.id,
          ...doc.data(),
        }) as RadioShow,
    );
    cb(radioShows);
  });
  return unsubscribe;
};
