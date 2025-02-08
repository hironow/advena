import importlib
import os

import pytest
from google.cloud import storage


def reload_storage_module():
    """
    環境変数の状態に応じてモジュールを再読み込みし、返却するヘルパー関数
    """
    import src.blob.storage as storage_module

    importlib.reload(storage_module)
    return storage_module


def test_emulator_mode(monkeypatch):
    """
    USE_FIREBASE_EMULATOR が "true" の場合、ストレージバケットは
    "<GOOGLE_CLOUD_PROJECT>.appspot.com" になることを検証する。
    """
    monkeypatch.setenv("USE_FIREBASE_EMULATOR", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    # GOOGLE_CLOUD_STORAGE_BUCKET は使用されないので削除しておく
    monkeypatch.delenv("GOOGLE_CLOUD_STORAGE_BUCKET", raising=False)

    storage_module = reload_storage_module()

    expected_bucket = "test-project.appspot.com"
    assert storage_module.storage_bucket == expected_bucket, (
        f"エミュレータモードでは storage_bucket は {expected_bucket} であるべき。"
    )
    # storage_client の project プロパティの確認
    assert isinstance(storage_module.storage_client, storage.Client)
    assert storage_module.storage_client.project == "test-project"


def test_non_emulator_mode_with_bucket(monkeypatch):
    """
    USE_FIREBASE_EMULATOR が "true" でない場合、環境変数 GOOGLE_CLOUD_STORAGE_BUCKET の値が
    storage_bucket として採用されることを検証する。
    """
    # エミュレータモードではないので、明示的に削除
    monkeypatch.delenv("USE_FIREBASE_EMULATOR", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "prod-project")
    monkeypatch.setenv("GOOGLE_CLOUD_STORAGE_BUCKET", "prod-bucket")

    storage_module = reload_storage_module()

    expected_bucket = "prod-bucket"
    assert storage_module.storage_bucket == expected_bucket, (
        f"通常モードでは storage_bucket は {expected_bucket} であるべき。"
    )
    assert isinstance(storage_module.storage_client, storage.Client)
    assert storage_module.storage_client.project == "prod-project"


def test_non_emulator_mode_without_bucket(monkeypatch):
    """
    USE_FIREBASE_EMULATOR が "true" でなく、かつ GOOGLE_CLOUD_STORAGE_BUCKET が設定されていない場合、
    storage_bucket は空文字列となることを検証する。
    """
    monkeypatch.delenv("USE_FIREBASE_EMULATOR", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "prod-project")
    monkeypatch.delenv("GOOGLE_CLOUD_STORAGE_BUCKET", raising=False)

    storage_module = reload_storage_module()

    expected_bucket = ""
    assert storage_module.storage_bucket == expected_bucket, (
        f"通常モードで GOOGLE_CLOUD_STORAGE_BUCKET 未設定の場合、storage_bucket は空文字列であるべき。"
    )
    assert isinstance(storage_module.storage_client, storage.Client)
    assert storage_module.storage_client.project == "prod-project"
