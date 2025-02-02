#!/bin/bash
set -euo pipefail

# Secret Manager Access for Cloud Run dotenvx
export PROJECT_ID="advena-dev"
export USER_SA_OF_SECRET_MANAGER="cloud-run-secret-access"
export USER_SA_OF_SECRET_MANAGER_EMAIL="${USER_SA_OF_SECRET_MANAGER}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== Settings ==="
echo "PROJECT_ID:  $PROJECT_ID"
echo "USER_SA_OF_SECRET_MANAGER:  $USER_SA_OF_SECRET_MANAGER"
echo "USER_SA_OF_SECRET_MANAGER_EMAIL:  $USER_SA_OF_SECRET_MANAGER_EMAIL"
echo "================"

# Enable the Secret Manager API
gcloud services enable secretmanager.googleapis.com --project "${PROJECT_ID}"

# サービスアカウントの存在チェックと作成
if ! gcloud iam service-accounts list \
    --filter="email:${USER_SA_OF_SECRET_MANAGER_EMAIL}" \
    --format="value(email)" | grep -q "${USER_SA_OF_SECRET_MANAGER_EMAIL}"; then
  echo "Creating service account: ${USER_SA_OF_SECRET_MANAGER_EMAIL}"
  gcloud iam service-accounts create "${USER_SA_OF_SECRET_MANAGER}" \
    --project="${PROJECT_ID}" \
    --description="Cloud Run Service Account for Secret Manager"
else
  echo "Service account ${USER_SA_OF_SECRET_MANAGER_EMAIL} already exists. Skipping creation."
fi

# 対象の Secret 名の配列
secrets=(
  "advena-dev-backend-DOTENV_PRIVATE_KEY"
  "advena-dev-frontend-DOTENV_PRIVATE_KEY"
)

# 各 Secret に対して、サービスアカウントに Secret Accessor ロールを付与
for secret in "${secrets[@]}"; do
  echo "Granting Secret Manager access to ${USER_SA_OF_SECRET_MANAGER_EMAIL} for secret ${secret}"
  gcloud secrets add-iam-policy-binding "${secret}" \
    --project="${PROJECT_ID}" \
    --member="serviceAccount:${USER_SA_OF_SECRET_MANAGER_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"
done

echo "⭐️ All done!"
