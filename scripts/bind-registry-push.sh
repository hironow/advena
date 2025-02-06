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

echo "=== Settings ==="
echo "REPO:        $REPO"
echo "PROJECT_ID:  $PROJECT_ID"
echo "IDENTITY_POOL: $IDENTITY_POOL"
echo "IDENTITY_PROVIDER: $IDENTITY_PROVIDER"
echo "ARTIFACT_REGISTRY_REPOSITORY: $ARTIFACT_REGISTRY_REPOSITORY"
echo "ARTIFACT_REGISTRY_LOCATION: $ARTIFACT_REGISTRY_LOCATION"
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

WORKLOAD_IDENTITY_PRINCIPAL="//iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${REPO}"

# Add a policy binding to the Artifact Registry repository as direct push from GitHub Actions
echo "Add a policy binding to the Artifact Registry as direct push"
gcloud artifacts repositories add-iam-policy-binding "${ARTIFACT_REGISTRY_REPOSITORY}" \
  --location="${ARTIFACT_REGISTRY_LOCATION}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/artifactregistry.writer" \
  --member="principalSet:${WORKLOAD_IDENTITY_PRINCIPAL}"

# Add a policy binding to the Cloud Build as trigger cloud build from GitHub Actions
# NOTE: needs serviceusage.services.use, storage.buckets.get, storage.buckets.list, storage.objects.create
echo "Add a policy binding to the Cloud Build as trigger"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --role="roles/cloudbuild.builds.editor" \
  --project="${PROJECT_ID}" --quiet \
  --member="principalSet:${WORKLOAD_IDENTITY_PRINCIPAL}"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/serviceusage.serviceUsageConsumer" \
  --member="principalSet:${WORKLOAD_IDENTITY_PRINCIPAL}"  
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/storage.objectViewer" \
  --member="principalSet:${WORKLOAD_IDENTITY_PRINCIPAL}"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --project="${PROJECT_ID}" --quiet \
  --role="roles/storage.objectCreator" \
  --member="principalSet:${WORKLOAD_IDENTITY_PRINCIPAL}"

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
# secret manager
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/secretmanager.secretAccessor")'
# artifact registry
gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | jq -r '.bindings[] | select(.role == "roles/artifactregistry.writer")'

echo "⭐️ All done!"