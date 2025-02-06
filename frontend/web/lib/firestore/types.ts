import type { Timestamp } from 'firebase/firestore';

export type User = {
  id: string; // firestoreのid (uuid)
  firebase_uid: string; // firebase authのuid
  createdAt: Timestamp;
  status: 'creating' | 'created';
  corpusName: string;
};

export const USER_COLLECTION = 'users'; // firestoreのcollection名: 作成後に変更しない
