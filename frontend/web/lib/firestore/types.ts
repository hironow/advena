import type { Timestamp } from 'firebase/firestore';

type TimestampAsStr = string;

export type User = {
  id: string; // firestoreのid (uuid)
  firebase_uid: string; // firebase authのuid
  created_at: TimestampAsStr;
  updated_at?: TimestampAsStr;
  status: 'creating' | 'created';
};

export const USER_COLLECTION = 'users'; // firestoreのcollection名: 作成後に変更しない

export type RadioShow = {
  id: string;
  name: string;
  created_at: TimestampAsStr;
  updated_at: TimestampAsStr;
  status: 'published'; // 公開後しか参照しない
  published_at: TimestampAsStr;
  audio_url: string;
};

export const RADIO_SHOW_COLLECTION = 'radio_shows'; // firestoreのcollection名: 作成後に変更しない
