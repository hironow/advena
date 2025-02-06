import type { Timestamp } from 'firebase/firestore';

export type User = {
  id: string; // firestoreのid (uuid)
  firebase_uid: string; // firebase authのuid
  created_at: Timestamp;
  updated_at: Timestamp;
  status: 'creating' | 'created';
};

export const USER_COLLECTION = 'users'; // firestoreのcollection名: 作成後に変更しない
