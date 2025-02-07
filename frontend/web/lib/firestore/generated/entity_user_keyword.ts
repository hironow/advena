/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Firestore の users/{userId}/keywords コレクションのドキュメントを表現するエンティティ。
 * ※ __current_version__ は最新のスキーマバージョンを表す。
 */
export interface Keyword {
  id: string;
  user_id: string;
  version: number;
  created_at: string;
  updated_at?: string | null;
  text: string;
}
export interface KeywordId {
  id: string;
  user_id: string;
}
