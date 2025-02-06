#!/bin/bash
set -euo pipefail

# TODO: WIP

##############################
# 変数定義 (必要に応じて変更)
##############################
# Artifact Registry が存在するプロジェクト（Docker イメージが push される側）
export DEV_PROJECT="advena-dev"
# イメージを pull するプロジェクト（pull 用のサービスアカウントを作成する側）
export PRD_PROJECT="advena-prd"

# Artifact Registry のリポジトリ名とロケーション
export REPO_NAME="my-repo"
export REPO_LOCATION="us-central1"

# advena-prd 側で作成するサービスアカウントの名前（メールアドレスは <名前>@<PRD_PROJECT>.iam.gserviceaccount.com となる）
export PULL_SA_NAME="my-prd-pull"
export PULL_SA_EMAIL="${PULL_SA_NAME}@${PRD_PROJECT}.iam.gserviceaccount.com"

##############################
# 設定内容の表示
##############################
echo "========== 設定内容 =========="
echo "Artifact Registry プロジェクト (DEV): ${DEV_PROJECT}"
echo "イメージ Pull 用プロジェクト (PRD): ${PRD_PROJECT}"
echo "Artifact Registry リポジトリ名: ${REPO_NAME}"
echo "Artifact Registry リージョン: ${REPO_LOCATION}"
echo "作成するサービスアカウント名: ${PULL_SA_NAME}"
echo "サービスアカウントのメール: ${PULL_SA_EMAIL}"
echo "=============================="
echo

##############################
# advena-prd 側でサービスアカウント作成
##############################
echo "【STEP 1】advena-prd プロジェクト内でサービスアカウントの存在確認..."
existing_sa=$(gcloud iam service-accounts list \
  --filter="email:${PULL_SA_EMAIL}" \
  --project="${PRD_PROJECT}" \
  --format="value(email)")

if [ -z "${existing_sa}" ]; then
  echo "サービスアカウント ${PULL_SA_EMAIL} は存在しないので作成します。"
  gcloud iam service-accounts create "${PULL_SA_NAME}" \
    --project="${PRD_PROJECT}" \
    --display-name="Pull 用 Artifact Registry アクセス用 SA"
  echo "サービスアカウント ${PULL_SA_EMAIL} を作成しました。"
else
  echo "サービスアカウント ${PULL_SA_EMAIL} は既に存在します。"
fi
echo

##############################
# advena-dev 側で IAM ポリシーに読み取り権限を付与
##############################
echo "【STEP 2】advena-dev プロジェクトの Artifact Registry リポジトリに IAM バインディングを追加します..."
gcloud artifacts repositories add-iam-policy-binding "${REPO_NAME}" \
  --location="${REPO_LOCATION}" \
  --project="${DEV_PROJECT}" --quiet \
  --member="serviceAccount:${PULL_SA_EMAIL}" \
  --role="roles/artifactregistry.reader"

echo "IAM バインディングの追加が完了しました。"
echo

##############################
# 終了メッセージ
##############################
echo "設定が完了しました。"
echo "advena-dev の Artifact Registry (${REPO_NAME}) に対して、"
echo "advena-prd のサービスアカウント (${PULL_SA_EMAIL}) に読み取り権限 (roles/artifactregistry.reader) を付与しました。"
