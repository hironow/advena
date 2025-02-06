import 'server-only';

// serverから参照される firestore access library

import { Timestamp, FieldValue } from 'firebase-admin/firestore';

import { getAdminDb } from '../firebase/admin';
import { type User, USER_COLLECTION } from './types';
import { randomUUID } from 'node:crypto';

// Status: firestoreのdocumentの状態を表す
// -ingは「command」として、-edは「event」として使われ、eventarcを通して backend に通知される
// creating: documentの作成中
// created: documentの作成完了
// deleting: documentの削除中
// error: エラー発生時

const useEmulator = process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === 'true';

// Eventarc のエンドポイント（ローカルでのシミュレーション用）
const EVENTARC_ENDPOINT_BASE = 'http://localhost:8000';
const EVENTARC_ENDPOINT_ADD_USER = `${EVENTARC_ENDPOINT_BASE}/add_user`;
const EVENTARC_ENDPOINT_ADD_KEYWORD = `${EVENTARC_ENDPOINT_BASE}/add_keyword`;

const createCloudEventBody = (
  collection: string,
  doc_id: string,
  data_base64: string,
) => {
  const PROJECT_ID = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
  const time = new Date().toISOString();
  return {
    specversion: '1.0',
    id: randomUUID(),
    source: `//firestore.googleapis.com/projects/${PROJECT_ID}/databases/(default)/documents`,
    type: 'google.cloud.firestore.document.v1.created',
    time: time,
    datacontenttype: 'application/protobuf',
    subject: `documents/${collection}/${doc_id}`,
    data_base64: data_base64,
  };
};

export const addUserAdmin = async (uid: string): Promise<void> => {
  try {
    const adminDb = getAdminDb();
    await adminDb.collection(USER_COLLECTION).doc(uid).set({
      uid: uid,
      createdAt: FieldValue.serverTimestamp(),
      status: 'creating',
    });
    console.info(`[COMMAND] ${USER_COLLECTION} creating`);
    console.info('[COMMAND] not yet assigned id');
  } catch (error) {
    console.error('Error adding document: ', error);
  }

  // genai server が eventarc を通して受信する
  // emulator を使っている場合はローカルのエンドポイントに送信する (eventarcへのrequestを模擬する)
  // 以下は行うべきリクエストの例:
  // curl -X POST http://localhost:8080/add_user \
  // -H "Content-Type: application/cloudevents+json" \
  // -d '{
  //   "specversion": "1.0",
  //   "id": "unique-event-id-1234",
  //   "source": "//firestore.googleapis.com/projects/advena-dev/databases/(default)/documents",
  //   "type": "google.cloud.firestore.document.v1.created",
  //   "time": "2025-02-06T12:00:00Z",
  //   "datacontenttype": "application/protobuf",
  //   "subject": "documents/users/abc123",
  //   "data_base64": "BASE64_ENCODED_PROTOBUF_PAYLOAD"
  // }'
  if (useEmulator) {
    const url = new URL(EVENTARC_ENDPOINT_ADD_USER);
    const data_base64 = Buffer.from(JSON.stringify({ uid: uid })).toString(
      'base64',
    );
    const body = createCloudEventBody(USER_COLLECTION, uid, data_base64);
    console.info(`[COMMAND] sending event to ${url}`);
    console.info(`[COMMAND] body: ${JSON.stringify(body)}`);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/cloudevents+json',
      },
      body: JSON.stringify(body),
    });
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
