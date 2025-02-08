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
  radio_show_id: string;
  title: string;
  host: string;
  status: "draft" | "published";
  description?: string | null;
}
export interface RadioShowId {
  id: string;
}
