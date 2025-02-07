import os

from google.cloud import storage  # type: ignore

# Google Cloud プロジェクト名。未設定の場合は空文字列でエラーが発火するようにする
gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")

if os.getenv("USE_FIREBASE_EMULATOR") == "true":
    # Firebase のデフォルトバケット名規則に従う
    storage_bucket = f"{gcp_project}.appspot.com"
else:
    # use env
    storage_bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET", "")

# プロジェクトが設定されている場合は project 引数を渡してクライアントを生成
storage_client = storage.Client(project=gcp_project)
