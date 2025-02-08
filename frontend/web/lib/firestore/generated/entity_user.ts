/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Firestore の users コレクションのドキュメントを表現するエンティティ。
 * ※ __current_version__ は最新のスキーマバージョンを表す。
 */
export interface User {
  id: string;
  version: number;
  created_at: string;
  updated_at?: string | null;
  firebase_uid: string;
  status: "creating" | "created";
  last_signed_in?: string | null;
  continuous_login_count?: number;
  login_count?: number;
  name?: string | null;
}
export interface UserId {
  id: string;
}
