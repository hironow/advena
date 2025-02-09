from datetime import datetime

import pytest

from src.database.firestore import db
from src.event_sourcing.entity.radio_show import (
    RadioShow,
    get,
    get_by_field,
    update,
)


# ---------------------------------------------------------------------------
# テスト前に radio_shows コレクション内のドキュメントを全削除するフィクスチャ
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_radio_shows_collection():
    collection_ref = db.collection(RadioShow.__collection__)
    docs = list(collection_ref.list_documents())
    for doc in docs:
        doc.delete()
    yield


# ---------------------------------------------------------------------------
# テストケース 1: 最低限の情報のみからのマイグレーション検証
# ---------------------------------------------------------------------------
def test_radio_get_migrate_minimal_document():
    """
    サーバーが最低限の情報のみ（id, created_at, status="creating"） で登録した場合、radio_get() 呼び出し時に以下のマイグレーションが実施されることを検証する。
      - version が _RADIO_SHOW_CURRENT_VERSION_ (1) に更新される
    """
    radio_show_id = "test_radio_show_1"
    minimal_doc = {
        "id": radio_show_id,
        "created_at": datetime(2020, 1, 1),
        "status": "creating",
        "masterdata_blob_path": "https://example.com/masterdata",
        # version, updated_at, は未設定
    }
    doc_ref = db.collection(RadioShow.__collection__).document(radio_show_id)
    doc_ref.set(minimal_doc)

    # radio_get() 呼び出しでマイグレーション処理が実施される
    radio_show = get(radio_show_id)
    assert radio_show is not None, "RadioShow エンティティが取得できるはず"
    # マイグレーション結果の確認
    assert radio_show.version == RadioShow.__current_version__, (
        "最終的な version は最新 (1) である"
    )
    assert radio_show.updated_at is None, "updated_at は補完され、None のままである"

    # Firestore 側も自動更新されていることを確認
    updated_doc = doc_ref.get().to_dict()
    assert updated_doc.get("version") == RadioShow.__current_version__


# ---------------------------------------------------------------------------
# テストケース 2: 更新処理の検証
# ---------------------------------------------------------------------------
def test_radio_update():
    """
    radio_update() による更新処理を検証する。
    既存ドキュメントの title や host を更新し、Firestore に正しく反映されることを確認する。
    """
    radio_show_id = "test_radio_show_2"
    minimal_doc = {
        "id": radio_show_id,
        "created_at": datetime(2020, 1, 1),
        "status": "creating",
        "masterdata_blob_path": "https://example.com/masterdata",
    }
    doc_ref = db.collection(RadioShow.__collection__).document(radio_show_id)
    doc_ref.set(minimal_doc)

    # 一度 radio_get() でマイグレーションを実施
    radio_show = get(radio_show_id)
    assert radio_show is not None

    # 更新用データ作成（title, host を変更）
    updated_data = radio_show.model_dump()
    updated_radio_show = RadioShow(**updated_data)

    update(radio_show_id, updated_radio_show)

    updated_doc = doc_ref.get().to_dict()


# ---------------------------------------------------------------------------
# テストケース 3: 単一件によるフィールド検索の検証
# ---------------------------------------------------------------------------
def test_radio_get_by_field_single():
    """
    radio_get_by_field() により、指定フィールド (例: host) で
    単一の RadioShow エンティティが取得できることを検証する。
    """
    radio_show_id = "test_radio_show_3"
    minimal_doc = {
        "version": 0,
        "id": radio_show_id,
        "created_at": datetime(2020, 1, 1),
        "status": "creating",
        "masterdata_blob_path": "https://example.com/masterdata",
    }
    db.collection(RadioShow.__collection__).document(radio_show_id).set(minimal_doc)

    radio_show = get_by_field("id", radio_show_id)
    assert radio_show is not None
    assert radio_show.id == radio_show_id
    assert radio_show.status == "creating"


# ---------------------------------------------------------------------------
# テストケース 4: 複数件存在する場合のフィールド検索検証
# ---------------------------------------------------------------------------
def test_radio_get_by_field_multiple(caplog):
    """
    radio_get_by_field() において、指定フィールドの値が複数存在する場合、
    None を返す（重複している旨のログが出力される）ことを検証する。
    """
    # 同一の host 値で 2 件のドキュメントを作成
    for idx in range(2):
        radio_show_id = f"test_radio_show_mult_{idx}"
        minimal_doc = {
            "version": 0,
            "id": radio_show_id,
            "created_at": datetime(2020, 1, 1),
            "status": "creating",
            "masterdata_blob_path": "https://example.com/masterdata",
        }
        db.collection(RadioShow.__collection__).document(radio_show_id).set(minimal_doc)

    radio_show = get_by_field("status", "creating")
    assert radio_show is None
    assert "Multiple documents found" in caplog.text


# ---------------------------------------------------------------------------
# テストケース 5: 存在しないドキュメントの場合の検証
# ---------------------------------------------------------------------------
def test_radio_get_not_found():
    """
    存在しない radio_show_id を指定した場合、radio_get() が None を返すことを検証する。
    """
    radio_show = get("nonexistent_radio_show")
    assert radio_show is None
