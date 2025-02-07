#!/usr/bin/env bash
set -euo pipefail

# Workload Identity Federation for GitHub Actions
# see: https://github.com/google-github-actions/auth?tab=readme-ov-file#preferred-direct-workload-identity-federation
export REPO="hironow/advena"                    # リポジトリ名 (owner/repo 形式)
export PROJECT_ID="advena-dev"                  # GCPプロジェクトID
export IDENTITY_POOL="github"                   # Workload Identity Poolの名前
export IDENTITY_PROVIDER="my-repo"              # Workload Identity Pool Providerの名前
export ARTIFACT_REGISTRY_REPOSITORY="advena"    # Artifact Registryのリポジトリ名
export ARTIFACT_REGISTRY_LOCATION="us-central1" # Artifact Registryのリージョン
export GITHUB_ACTIONS_SA="github-actions-on-advena"

echo "=== Settings ==="
echo "REPO:        $REPO"
echo "PROJECT_ID:  $PROJECT_ID"
echo "IDENTITY_POOL: $IDENTITY_POOL"
echo "IDENTITY_PROVIDER: $IDENTITY_PROVIDER"
echo "ARTIFACT_REGISTRY_REPOSITORY: $ARTIFACT_REGISTRY_REPOSITORY"
echo "ARTIFACT_REGISTRY_LOCATION: $ARTIFACT_REGISTRY_LOCATION"
echo "GITHUB_ACTIONS_SA: $GITHUB_ACTIONS_SA"
echo "================"

# Enable the Artifact Registry API
gcloud services enable artifactregistry.googleapis.com --project "${PROJECT_ID}"

# PoolのフルIDを取得
WORKLOAD_IDENTITY_POOL_ID=$(
  gcloud iam workload-identity-pools describe "${IDENTITY_POOL}" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --format="value(name)"
)
echo "WORKLOAD_IDENTITY_POOL_ID: ${WORKLOAD_IDENTITY_POOL_ID}"
# ex: projects/123456789/locations/global/workloadIdentityPools/github

# ProviderのフルIDを取得
PROVIDER_ID=$(
  gcloud iam workload-identity-pools providers describe "${IDENTITY_PROVIDER}" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --workload-identity-pool="${IDENTITY_POOL}" \
    --format="value(name)"
)
echo "PROVIDER_ID: ${PROVIDER_ID}"
# ex: projects/123456789/locations/global/workloadIdentityPools/github/providers/my-repo

# service accountへ紐付けたのでコメントアウト。 principalSet の設定はしない FIXME: debug後、principalSetでも動くか確認
# WORKLOAD_IDENTITY_PRINCIPAL="//iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${REPO}"
GITHUB_ACTIONS_SA_EMAIL="${GITHUB_ACTIONS_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_DEFAULT_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Add a policy binding to the Artifact Registry repository as direct push from GitHub Actions
echo "Add a policy binding to the Artifact Registry as direct push"
gcloud artifacts repositories add-iam-policy-binding "${ARTIFACT_REGISTRY_REPOSITORY}" \
  --location="${ARTIFACT_REGISTRY_LOCATION}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/artifactregistry.writer" \
  --member="serviceAccount:${GITHUB_ACTIONS_SA_EMAIL}"

# Add a policy binding to the Cloud Build as trigger cloud build from GitHub Actions
# NOTE: needs serviceusage.services.use, storage.buckets.get, storage.buckets.list, storage.objects.create
echo "Add a policy binding to the Cloud Build as trigger"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --role="roles/cloudbuild.builds.editor" \
  --project="${PROJECT_ID}" --quiet \
  --member="serviceAccount:${GITHUB_ACTIONS_SA_EMAIL}"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/serviceusage.serviceUsageConsumer" \
  --member="serviceAccount:${GITHUB_ACTIONS_SA_EMAIL}"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/storage.objectViewer" \
  --member="serviceAccount:${GITHUB_ACTIONS_SA_EMAIL}"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/storage.objectCreator" \
  --member="serviceAccount:${GITHUB_ACTIONS_SA_EMAIL}"
# NOTE: storage admin が必要であったため、上記の2つとともに storage.admin を追加すること
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/storage.admin" \
  --member="serviceAccount:${GITHUB_ACTIONS_SA_EMAIL}"

# DEBUG ONLY: serviceusage.services.use がないとエラーになったら、一時的に roles/editor をつけてdebugすること
# see: https://cloud.google.com/logging/docs/audit/configure-data-access

# IMPORTANT: Compute EngineデフォルトSAをGitHub ActionsのSAが「ActAs」（代理実行）する必要があるため、必要なのは iam.serviceAccounts.actAs 権限、すなわち roles/iam.serviceAccountUser の付与
gcloud iam service-accounts add-iam-policy-binding "${COMPUTE_DEFAULT_SERVICE_ACCOUNT}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/iam.serviceAccountUser" \
  --member="serviceAccount:${GITHUB_ACTIONS_SA_EMAIL}"


# Add a policy binding to the Cloud Build as builder and pusher
echo "Add a policy binding to the Cloud Build as builder and pusher"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_DEFAULT_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
# secret manager access (for Cloud Build)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CLOUD_BUILD_DEFAULT_SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project="${PROJECT_ID}" --quiet
# artifact registry
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CLOUD_BUILD_DEFAULT_SERVICE_ACCOUNT}" \
  --role="roles/artifactregistry.writer" \
  --project="${PROJECT_ID}" --quiet


# Check result
# artifact registry
gcloud artifacts repositories get-iam-policy "${ARTIFACT_REGISTRY_REPOSITORY}" --location="${ARTIFACT_REGISTRY_LOCATION}" --format=json --project="${PROJECT_ID}" | jq -r '.bindings[] | select(.role == "roles/artifactregistry.writer")'
# service usage
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/serviceusage.serviceUsageConsumer")'
# cloud build
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/cloudbuild.builds.editor")'
# cloud storage
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/storage.objectViewer")'
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/storage.objectCreator")'
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/storage.admin")'
# gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/editor")'
gcloud iam service-accounts get-iam-policy "${COMPUTE_DEFAULT_SERVICE_ACCOUNT}" --format=json | jq -r '.bindings[] | select(.role == "roles/iam.serviceAccountUser")'
# secret manager
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/secretmanager.secretAccessor")'
# artifact registry
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/artifactregistry.writer")'

echo "⭐️ All done!"