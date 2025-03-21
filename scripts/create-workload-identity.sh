#!/usr/bin/env bash
set -euo pipefail

# Workload Identity Federation for GitHub Actions
# see: https://github.com/google-github-actions/auth?tab=readme-ov-file#preferred-direct-workload-identity-federation
export REPO="hironow/advena"   # リポジトリ名 (owner/repo 形式)
export PROJECT_ID="advena-dev" # GCPプロジェクトID
export GITHUB_ACTIONS_SA="github-actions-on-advena"

echo "=== Settings ==="
echo "REPO:        $REPO"
echo "PROJECT_ID:  $PROJECT_ID"
echo "GITHUB_ACTIONS_SA: $GITHUB_ACTIONS_SA"
echo "================"

# Enable the IAM Credentials API
gcloud services enable iamcredentials.googleapis.com --project "${PROJECT_ID}"

# 紐付け用のservice accountを作成
gcloud iam service-accounts create "${GITHUB_ACTIONS_SA}" \
  --project="${PROJECT_ID}" \
  --display-name="GitHub Actions Service Account for advena"

# Create a (Workload Identity) Pool
gcloud iam workload-identity-pools create "github" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"
# PoolのフルIDを取得
WORKLOAD_IDENTITY_POOL_ID=$(
  gcloud iam workload-identity-pools describe "github" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --format="value(name)"
)
echo "WORKLOAD_IDENTITY_POOL_ID: ${WORKLOAD_IDENTITY_POOL_ID}"
# ex: projects/123456789/locations/global/workloadIdentityPools/github


# Create a (Workload Identity Pool) Provider
gcloud iam workload-identity-pools providers create-oidc "my-repo" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github" \
  --display-name="My GitHub repo Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '${REPO}'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
# ProviderのフルIDを取得
PROVIDER_ID=$(
  gcloud iam workload-identity-pools providers describe "my-repo" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --workload-identity-pool="github" \
    --format="value(name)"
)
echo "PROVIDER_ID: ${PROVIDER_ID}"
# ex: projects/123456789/locations/global/workloadIdentityPools/github/providers/my-repo

# Bind the service account to the Workload Identity Pool
gcloud iam service-accounts add-iam-policy-binding "${GITHUB_ACTIONS_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${REPO}"

echo "⭐️ All done!"