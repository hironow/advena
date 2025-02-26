import 'server-only';

// serverから参照される firestore access library

import { Timestamp, FieldValue } from 'firebase-admin/firestore';

import { getAdminDb, useEmulator } from '../firebase/admin';
import { USER_COLLECTION } from './types';
import type { User } from './generated/entity_user';
import { randomUUID } from 'node:crypto';
import {
  createCloudEventBody,
  EVENTARC_ENDPOINT_ADD_USER,
  sendCloudEvent,
} from './cloudevents/cloudevents';

// Status: firestoreのdocumentの状態を表す
// -ingは「command」として、-edは「event」として使われ、eventarcを通して backend に通知される
// creating: documentの作成中
// created: documentの作成完了
// deleting: documentの削除中
// error: エラー発生時

// ユーザー追加処理（Firestore ドキュメント作成と CloudEvent の送信）
export const addUserAdmin = async (firebase_uid: string): Promise<void> => {
  const adminDb = getAdminDb();
  const newUserId = randomUUID(); // uuid v4

  // tx付きでfirebase_uid に該当するユーザを探し、なければ作成
  await adminDb.runTransaction(async (tx) => {
    const utcNow = Timestamp.fromDate(
      new Date(new Date().toUTCString()),
    ) as unknown as string;

    const userRef = await tx.get(
      adminDb
        .collection(USER_COLLECTION)
        .where('firebase_uid', '==', firebase_uid)
        .limit(1),
    );
    if (userRef.empty) {
      const newUserRef = adminDb.collection(USER_COLLECTION).doc(newUserId);
      const newUser: User = {
        version: 0,
        id: newUserId,
        firebase_uid: firebase_uid,
        created_at: utcNow,
        status: 'creating',
      };
      tx.set(newUserRef, newUser);
      console.info(
        `[COMMAND] ${USER_COLLECTION} document for id ${newUserId} created with status 'creating'`,
      );
      return;
    }
  });

  if (useEmulator) {
    // 送信データ（ここでは id のみを JSON 化）
    const data = { id: newUserId };
    const dataBase64 = Buffer.from(JSON.stringify(data)).toString('base64');
    const eventBody = createCloudEventBody(
      USER_COLLECTION,
      newUserId,
      dataBase64,
    );
    await sendCloudEvent(EVENTARC_ENDPOINT_ADD_USER, eventBody);
  }
};

export const getUserByFirebaseUidAdmin = async (
  firebase_uid: string,
): Promise<User | null> => {
  const adminDb = getAdminDb();

  const userRef = await adminDb
    .collection(USER_COLLECTION)
    .where('firebase_uid', '==', firebase_uid)
    .limit(1)
    .get();
  if (userRef.empty) {
    return null;
  }
  const userDoc = userRef.docs[0];
  return {
    ...userDoc.data(),
  } as User;
};
