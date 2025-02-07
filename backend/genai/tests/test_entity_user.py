import time
from datetime import datetime

import pytest
from google.api_core.exceptions import GoogleAPICallError
from pydantic import ValidationError

from src.database.firestore import (
    db,  # テスト時は Firestore エミュレータなどのテスト環境が利用される前提
)
from src.event_sourcing.entity.user import User, get, get_by_firebase_uid, update


# ---------------------------------------------------------------------------
# テスト前に対象コレクション内のドキュメントを全削除するフィクスチャ
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_users_collection():
    collection_ref = db.collection(User.__collection__)
    docs = list(collection_ref.list_documents())
    for doc in docs:
        # 削除は非同期反映の場合もあるため、失敗時はリトライ等の仕組みを検討してください
        doc.delete()
    # 確実に削除が反映されるように少し待機（必要に応じて調整）
    time.sleep(0.5)
    yield
    # テスト後にもクリーンアップ（必要に応じて）


# ---------------------------------------------------------------------------
# テストケース
# ---------------------------------------------------------------------------
def test_migrate_document():
    """
    ドキュメントに version や name が存在しない場合、get() 呼び出し時に
    マイグレーションが実施され、最終的に __current_version__ に合わせた状態になることを確認。
    """
    user_id = "test_user_migrate"
    # version, name 未設定の状態でドキュメントを作成
    user_data = {
        "id": user_id,
        "firebase_uid": "firebase_migrate",
        "status": "created",
        "created_at": datetime(2020, 1, 1),
        "updated_at": None,
        "last_signed_in": None,
        "continuous_login_count": 0,
        "login_count": 0,
        # "version" や "name" は未設定
    }
    db.collection(User.__collection__).document(user_id).set(user_data)
    # 書き込み反映待ち

    user = get(user_id)
    assert user is not None, "get() でユーザが取得できるはず"
    # マイグレーションにより最新バージョンになっているはず（例: 2）
    assert user.version == User.__current_version__, (
        f"version は {User.__current_version__} である必要がある"
    )
    # migrate_from_1_to_2 の処理で name が補完される例として "Default Name" を設定している
    assert user.name == "Default Name", "name フィールドにデフォルト値が設定されるはず"


def test_update():
    """
    update() による更新処理のテスト。
    既存ドキュメントの name フィールドを変更し、更新後の内容が反映されることを確認する。
    """
    user_id = "test_user_update"
    initial_data = {
        "version": User.__current_version__,
        "id": user_id,
        "firebase_uid": "firebase_update",
        "status": "created",
        "created_at": datetime(2020, 1, 1),
        "updated_at": None,
        "last_signed_in": None,
        "continuous_login_count": 0,
        "login_count": 0,
        "name": "Original Name",
    }
    doc_ref = db.collection(User.__collection__).document(user_id)
    doc_ref.set(initial_data)

    # 更新内容
    updated_data = initial_data.copy()
    updated_data["name"] = "Updated Name"
    # updated_at を更新（例として現在時刻を設定）
    updated_data["updated_at"] = datetime.utcnow()
    user_instance = User(**updated_data)
    update(user_id, user_instance)

    # 取得して更新が反映されているか確認
    updated_doc = doc_ref.get().to_dict()
    assert updated_doc["name"] == "Updated Name", (
        "name フィールドが更新されている必要がある"
    )
    # 他のフィールドについても必要に応じて検証可能


def test_get_by_firebase_uid_single():
    """
    firebase_uid による単一件の取得をテストする。
    """
    user_id = "test_user_get_by_uid"
    firebase_uid = "firebase_unique"
    user_data = {
        "version": User.__current_version__,
        "id": user_id,
        "firebase_uid": firebase_uid,
        "status": "created",
        "created_at": datetime(2020, 1, 1),
        "updated_at": None,
        "last_signed_in": None,
        "continuous_login_count": 0,
        "login_count": 0,
        "name": "Unique User",
    }
    db.collection(User.__collection__).document(user_id).set(user_data)

    user = get_by_firebase_uid(firebase_uid)
    assert user is not None, "firebase_uid による取得でユーザが返るはず"
    assert user.id == user_id, "取得されたユーザの id が一致する必要がある"


def test_get_by_firebase_uid_multiple(caplog):
    """
    同一 firebase_uid を持つ複数のドキュメントが存在する場合、get_by_firebase_uid() は None を返すことを確認する。
    また、ログにエラーメッセージが出力されることも検証する。
    """
    firebase_uid = "firebase_duplicate"
    # 2 件のドキュメントを作成
    user_data1 = {
        "version": User.__current_version__,
        "id": "dup_user_1",
        "firebase_uid": firebase_uid,
        "status": "created",
        "created_at": datetime(2020, 1, 1),
        "updated_at": None,
        "last_signed_in": None,
        "continuous_login_count": 0,
        "login_count": 0,
        "name": "Dup User 1",
    }
    user_data2 = {
        "version": User.__current_version__,
        "id": "dup_user_2",
        "firebase_uid": firebase_uid,
        "status": "created",
        "created_at": datetime(2020, 1, 1),
        "updated_at": None,
        "last_signed_in": None,
        "continuous_login_count": 0,
        "login_count": 0,
        "name": "Dup User 2",
    }
    db.collection(User.__collection__).document("dup_user_1").set(user_data1)
    db.collection(User.__collection__).document("dup_user_2").set(user_data2)

    user = get_by_firebase_uid(firebase_uid)
    # 複数件存在する場合、get_by_firebase_uid() は None を返す実装になっている
    assert user is None, "重複している場合、None を返すはず"
    # ログに「Multiple documents found」が出力されているか検証
    assert "Multiple documents found" in caplog.text


# --- テストケース 1: マイグレーション処理がバージョンを更新しないケース ---
def test_migrate_failure_no_version_change(monkeypatch, caplog):
    """
    MIGRATION 関数が正しくバージョンを更新しなかった場合、migrate() がエラーログを出力し、
    ドキュメントの version が更新されないことを確認する。
    """
    user_id = "test_migrate_failure"
    # 必須フィールドのみを持ち、version 0 で作成
    user_data = {
        "id": user_id,
        "firebase_uid": "firebase_failure",
        "status": "created",
        "created_at": datetime(2020, 1, 1),
        "updated_at": None,
        "last_signed_in": None,
        "continuous_login_count": 0,
        "login_count": 0,
        "version": 0,
    }
    # ドキュメント作成
    db.collection(User.__collection__).document(user_id).set(user_data)

    # version 0 のマイグレーション関数を、何も変更しない不正な関数に置き換える
    import src.event_sourcing.entity.user as user_entity  # モジュール内のグローバル変数 MIGRATIONS を参照するため

    def faulty_migration(doc: dict) -> dict:
        # version の更新を行わず、元の doc をそのまま返す
        return doc

    monkeypatch.setitem(user_entity.MIGRATIONS, 0, faulty_migration)

    doc_snapshot = db.collection(User.__collection__).document(user_id).get()
    migrated = user_entity.migrate(doc_snapshot, auto_migrate=False)
    # version は更新されず 0 のままであることを確認
    assert migrated["version"] == 0
    # エラーログに「did not update the version number」が出力されていることを確認
    assert "did not update the version number" in caplog.text


# --- テストケース 2: update() の更新中に例外が発生するケース ---
def test_update_failure(monkeypatch):
    """
    update() 呼び出し時に、update_in_transaction 内で例外が発生した場合、
    その例外が再スローされることを検証する。
    """
    user_id = "test_update_failure"
    initial_data = {
        "version": User.__current_version__,
        "id": user_id,
        "firebase_uid": "firebase_update_failure",
        "status": "created",
        "created_at": datetime(2020, 1, 1),
        "updated_at": None,
        "last_signed_in": None,
        "continuous_login_count": 0,
        "login_count": 0,
        "name": "Initial Name",
    }
    # 初期ドキュメント作成
    db.collection(User.__collection__).document(user_id).set(initial_data)

    # update_in_transaction を例外を発生させる関数に差し替え
    import src.event_sourcing.entity.user as user_entity

    def faulty_update_in_transaction(transaction, doc_ref, new_data):
        # errors 引数に空リストを指定してエラーを発生させる
        raise GoogleAPICallError("Simulated update failure", errors=[])

    monkeypatch.setattr(
        user_entity, "update_in_transaction", faulty_update_in_transaction
    )

    # 更新内容を作成
    updated_data = initial_data.copy()
    updated_data["name"] = "Updated Name"
    updated_data["updated_at"] = datetime.utcnow()
    user_instance = User(**updated_data)

    with pytest.raises(GoogleAPICallError) as excinfo:
        user_entity.update(user_id, user_instance)
    assert "Simulated update failure" in str(excinfo.value)


# --- テストケース 3: 不正なドキュメントによる User の生成失敗ケース ---
def test_get_failure_invalid_document():
    """
    必須フィールド（例: firebase_uid）が欠落したドキュメントの場合、get() 呼び出し時に
    Pydantic のバリデーションエラーが発生することを検証する。
    """
    user_id = "test_get_failure_invalid"
    # firebase_uid を欠落させる（必須フィールドのため）
    invalid_data = {
        "version": User.__current_version__,
        "id": user_id,
        # "firebase_uid": missing intentionally
        "status": "created",
        "created_at": datetime(2020, 1, 1),
        "updated_at": None,
        "last_signed_in": None,
        "continuous_login_count": 0,
        "login_count": 0,
        "name": "Invalid User",
    }
    db.collection(User.__collection__).document(user_id).set(invalid_data)

    with pytest.raises(ValidationError):
        # get() 内で migrate() の後、User(**doc_dict) の呼び出し時にバリデーションエラーが発生するはず
        get(user_id)


def test_get_migrate_minimal_document():
    """
    クライアントが最低限の情報のみ（id, firebase_uid, created_at, status="creating"）
    を Firestore に保存した場合、get() 呼び出し時に migrate() により以下が実現されることを検証する。
      - version が 2 (最新) になる
      - status が "creating" から "created" に更新される
      - オプショナルフィールド（updated_at, last_signed_in, continuous_login_count, login_count, name）
        が補完され、name は "Default Name" に設定される
    """
    user_id = "test_minimal"
    minimal_doc = {
        "id": user_id,
        "firebase_uid": "some_firebase_uid",
        "created_at": datetime(2020, 1, 1),
        "status": "creating",
    }

    # Firestore にドキュメントを登録（クライアント側の最低限の情報）
    doc_ref = db.collection(User.__collection__).document(user_id)
    doc_ref.set(minimal_doc)
    # 書き込み反映の待機（テスト環境に合わせて調整）

    # get() を呼ぶと、migrate() により不足フィールドの補完とステータス変換が実行される
    user = get(user_id)
    assert user is not None, "User エンティティが生成されるはず"

    # マイグレーション結果の確認
    assert user.version == User.__current_version__, (
        "最終的なバージョンは 2 である必要がある"
    )
    assert user.status == "created", "status は 'creating' から 'created' に更新される"
    # クライアントが送信した基本情報は保持される
    assert user.id == user_id
    assert user.firebase_uid == "some_firebase_uid"
    assert user.created_at == datetime(2020, 1, 1)
    # 補完されるべきオプショナルフィールドの確認
    assert user.updated_at is None, "updated_at は補完され、None であるはず"
    assert user.last_signed_in is None, "last_signed_in は補完され、None であるはず"
    assert user.continuous_login_count == 0, (
        "continuous_login_count は補完され、0 であるはず"
    )
    assert user.login_count == 0, "login_count は補完され、0 であるはず"
    assert user.name == "Default Name", (
        "name は migrate_from_1_to_2 により 'Default Name' に設定される"
    )

    # ※オプション: Firestore 側のドキュメントが自動更新されていることも確認
    migrated_doc = doc_ref.get().to_dict()
    assert migrated_doc.get("version") == User.__current_version__
    assert migrated_doc.get("status") == "created"
    assert migrated_doc.get("name") == "Default Name"
