/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Firestore の radio_shows コレクションのドキュメントを表現するエンティティ。
 * ※ __current_version__ は最新のスキーマバージョンを表す。
 */
export interface RadioShow {
  id: string;
  version: number;
  created_at: string;
  updated_at?: string | null;
  status: "creating" | "created";
  masterdata_blob_path: string;
  broadcasted_at?: string | null;
  audio_url?: string | null;
  script_url?: string | null;
  book_count?: number;
  books?: RadioShowBook[];
}
export interface RadioShowBook {
  title: string;
  url: string;
  thumbnail_url: string;
  isbn: string;
  jp_e_code: string;
}
export interface RadioShowId {
  id: string;
}
