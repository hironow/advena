import time
from datetime import datetime

import pytest

from src.database.firestore import db
from src.event_sourcing.entity.user import UserId

# インポートは実際のプロジェクト構成に合わせて調整してください
from src.event_sourcing.entity.user_keyword import (
    Keyword,
)
from src.event_sourcing.entity.user_keyword import (
    get as get_keyword,
)
from src.event_sourcing.entity.user_keyword import (
    get_by_field as get_keyword_by_field,
)
from src.event_sourcing.entity.user_keyword import (
    update as update_keyword,
)


# ---------------------------------------------------------------------------
# テスト前に対象ユーザーの keywords サブコレクションを全削除するフィクスチャ
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_keywords_subcollection():
    test_user_id = "test_user_keywords"
    keywords_ref = (
        db.collection("users").document(test_user_id).collection(Keyword.__collection__)
    )
    docs = list(keywords_ref.list_documents())
    for doc in docs:
        doc.delete()
    yield


# ---------------------------------------------------------------------------
# テスト用の UserId オブジェクトを返すフィクスチャ
# ---------------------------------------------------------------------------
@pytest.fixture
def test_user() -> UserId:
    return UserId(id="test_user_keywords")


# ---------------------------------------------------------------------------
# テストケース 1: 最低限の情報のみからのマイグレーション検証
# ---------------------------------------------------------------------------
def test_get_migrate_minimal_keyword(test_user: UserId):
    """
    クライアントが最低限の情報のみを保存した場合、get() 呼び出し時にマイグレーションが実施され、
    version が補完されることなどを検証する。
    """
    keyword_id = "kw1"
    # クライアントが送信する最小限の情報（version, updated_at は未設定）
    minimal_doc = {
        "id": keyword_id,
        "user_id": test_user.id,
        "created_at": datetime(2020, 1, 1),
        "text": "example keyword",
    }
    doc_ref = (
        db.collection("users")
        .document(test_user.id)
        .collection(Keyword.__collection__)
        .document(keyword_id)
    )
    doc_ref.set(minimal_doc)

    keyword = get_keyword(test_user, keyword_id)
    assert keyword is not None, "Keyword エンティティが取得できるはず"
    # マイグレーションにより version が補完され、Keyword.__current_version__ (1) になる
    assert keyword.version == Keyword.__current_version__
    assert keyword.updated_at is None
    assert keyword.text == "example keyword"
    assert keyword.id == keyword_id
    assert keyword.user_id == test_user.id

    # Firestore 側にもマイグレーション結果が反映されているか検証
    updated_doc = doc_ref.get().to_dict()
    assert updated_doc.get("version") == Keyword.__current_version__
    assert updated_doc.get("updated_at") is None


# ---------------------------------------------------------------------------
# テストケース 2: キーワードの更新処理の検証
# ---------------------------------------------------------------------------
def test_update_keyword(test_user: UserId):
    """
    キーワードドキュメントを取得後、text フィールドを更新して再保存し、更新が正しく反映されることを検証する。
    """
    keyword_id = "kw2"
    minimal_doc = {
        "id": keyword_id,
        "user_id": test_user.id,
        "created_at": datetime(2020, 1, 1),
        "text": "initial keyword",
    }
    doc_ref = (
        db.collection("users")
        .document(test_user.id)
        .collection(Keyword.__collection__)
        .document(keyword_id)
    )
    doc_ref.set(minimal_doc)

    # get() によりマイグレーションが適用される
    keyword = get_keyword(test_user, keyword_id)
    assert keyword is not None

    # 更新用データを作成：text フィールドを変更
    updated_keyword_data = keyword.model_dump()
    updated_keyword_data["text"] = "updated keyword"
    # Keyword は KeywordId を継承しているので、updated_keyword_data に id と user_id が含まれる
    updated_keyword = Keyword(**updated_keyword_data)

    update_keyword(test_user, updated_keyword)

    updated_doc = doc_ref.get().to_dict()
    assert updated_doc.get("text") == "updated keyword"


# ---------------------------------------------------------------------------
# テストケース 3: 指定フィールドによる単一件取得の検証
# ---------------------------------------------------------------------------
def test_get_by_field_single(test_user: UserId):
    """
    指定フィールド（例: text）で検索し、単一の Keyword エンティティが取得できることを検証する。
    """
    keyword_id = "kw3"
    minimal_doc = {
        "id": keyword_id,
        "user_id": test_user.id,
        "created_at": datetime(2020, 1, 1),
        "text": "unique keyword",
    }
    db.collection("users").document(test_user.id).collection(
        Keyword.__collection__
    ).document(keyword_id).set(minimal_doc)

    keyword = get_keyword_by_field(test_user, "text", "unique keyword")
    assert keyword is not None
    assert keyword.text == "unique keyword"


# ---------------------------------------------------------------------------
# テストケース 4: 指定フィールドによる複数件存在時の検証
# ---------------------------------------------------------------------------
def test_get_by_field_multiple(test_user: UserId, caplog):
    """
    同じ text の値を持つキーワードが複数存在する場合、get_by_field() は None を返すこと、
    および重複に関するエラーログが出力されることを検証する。
    """
    # 同一の text を持つ2件のキーワードドキュメントを作成
    for idx in range(2):
        kw_id = f"kw_mult_{idx}"
        minimal_doc = {
            "id": kw_id,
            "user_id": test_user.id,
            "created_at": datetime(2020, 1, 1),
            "text": "duplicate keyword",
        }
        db.collection("users").document(test_user.id).collection(
            Keyword.__collection__
        ).document(kw_id).set(minimal_doc)

    keyword = get_keyword_by_field(test_user, "text", "duplicate keyword")
    assert keyword is None
    assert "Multiple Keyword documents found" in caplog.text


# ---------------------------------------------------------------------------
# テストケース 5: 存在しないキーワードドキュメントの取得検証
# ---------------------------------------------------------------------------
def test_get_nonexistent_keyword(test_user: UserId):
    """
    存在しないキーワードIDを指定した場合、get() が None を返すことを検証する。
    """
    keyword = get_keyword(test_user, "nonexistent_kw")
    assert keyword is None
