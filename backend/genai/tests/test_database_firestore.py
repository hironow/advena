import importlib
import os

import pytest
from google.cloud import firestore


def reload_firestore_module():
    """
    環境変数の状態に応じて、モジュールを再読み込みして返すヘルパー関数
    """
    import src.database.firestore as firestore_module

    importlib.reload(firestore_module)
    return firestore_module


def test_ci_true(monkeypatch):
    # CI環境の場合は MockFirestore を使うはず
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("USE_FIREBASE_EMULATOR", raising=False)

    firestore_module = reload_firestore_module()

    # CI環境の場合、MockFirestore がインポートされるはず
    from mockfirestore import MockFirestore

    assert isinstance(firestore_module.db, MockFirestore), (
        "CI環境ではMockFirestoreであるべき"
    )


def test_emulator(monkeypatch):
    # USE_FIREBASE_EMULATOR 環境の場合、firestore.Client(project=...) を使うはず
    monkeypatch.setenv("CI", "false")
    monkeypatch.setenv("USE_FIREBASE_EMULATOR", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")

    firestore_module = reload_firestore_module()

    assert isinstance(firestore_module.db, firestore.Client), (
        "エミュレータ使用時はfirestore.Clientであるべき"
    )
    # firestore.Client のインスタンスの project 属性が環境変数の値と一致することを確認
    assert firestore_module.db.project == "test-project", (
        "project名が環境変数の値と一致すること"
    )


def test_default(monkeypatch):
    # 上記以外の場合、通常の firestore.Client を使うはず
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("USE_FIREBASE_EMULATOR", raising=False)

    firestore_module = reload_firestore_module()

    assert isinstance(firestore_module.db, firestore.Client), (
        "デフォルトではfirestore.Clientであるべき"
    )
