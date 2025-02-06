import 'server-only';
import { randomUUID } from 'node:crypto';

// Eventarc のエンドポイント（ローカルでのシミュレーション用）
const EVENTARC_ENDPOINT_BASE = 'http://localhost:8000';
export const EVENTARC_ENDPOINT_ADD_USER = `${EVENTARC_ENDPOINT_BASE}/add_user`;
export const EVENTARC_ENDPOINT_ADD_KEYWORD = `${EVENTARC_ENDPOINT_BASE}/add_keyword`;

// CloudEvent の型定義（必要な拡張属性含む）
interface CloudEventBody {
  specversion: string;
  id: string;
  source: string;
  type: string;
  time: string;
  datacontenttype: string;
  subject: string;
  document: string; // Python 側で参照するためのフィールドを追加
  data_base64: string;
}

// CloudEvent ボディを生成する関数
export const createCloudEventBody = (
  collection: string,
  doc_id: string,
  data_base64: string,
): CloudEventBody => {
  const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
  const time = new Date().toISOString();
  return {
    specversion: '1.0',
    id: randomUUID(),
    source: `//firestore.googleapis.com/projects/${projectId}/databases/(default)/documents`,
    type: 'google.cloud.firestore.document.v1.created',
    time,
    // JSON で送信するために変更
    datacontenttype: 'application/json',
    subject: `documents/${collection}/${doc_id}`,
    // Python 側が document フィールドを期待しているので追加
    document: `${collection}/${doc_id}`,
    data_base64,
  };
};

// 共通の CloudEvent 送信関数（エラーハンドリング付き）
export const sendCloudEvent = async (
  endpoint: string,
  eventBody: CloudEventBody,
): Promise<void> => {
  try {
    const url = new URL(endpoint);
    console.info(`[COMMAND] Sending CloudEvent to ${url}`);
    console.info(`[COMMAND] Event body: ${JSON.stringify(eventBody)}`);

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/cloudevents+json',
      },
      body: JSON.stringify(eventBody),
    });

    if (!response.ok) {
      console.error(
        `[ERROR] Failed to send CloudEvent: ${response.status} ${response.statusText}`,
      );
    } else {
      console.info('[INFO] CloudEvent sent successfully.');
    }
  } catch (error) {
    console.error(`[ERROR] Exception while sending CloudEvent: ${error}`);
  }
};
