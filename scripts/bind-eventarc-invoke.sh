#!/bin/bash
set -euo pipefail

# Eventarc Invoke to Cloud Run for Cloud Eventarc
export PROJECT_ID="advena-dev"
export REGION="us-central1"
export GRANT_CLOUD_RUN_SERVICE="backend-advena"
export USER_SA_OF_EVENTARC="eventarc-invoke-cloud-run"
export USER_SA_OF_EVENTARC_EMAIL="${USER_SA_OF_EVENTARC}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== Settings ==="
echo "PROJECT_ID:  $PROJECT_ID"
echo "REGION:  $REGION"
echo "GRANT_CLOUD_RUN_SERVICE:  $GRANT_CLOUD_RUN_SERVICE"
echo "USER_SA_OF_EVENTARC:  $USER_SA_OF_EVENTARC"
echo "USER_SA_OF_EVENTARC_EMAIL:  $USER_SA_OF_EVENTARC_EMAIL"
echo "================"

# Enable the Cloud EVENTARC API
gcloud services enable eventarc.googleapis.com --project "${PROJECT_ID}"

# サービスアカウントの存在チェックと作成
if ! gcloud iam service-accounts list \
    --filter="email:${USER_SA_OF_EVENTARC_EMAIL}" \
    --format="value(email)" | grep -q "${USER_SA_OF_EVENTARC_EMAIL}"; then
  echo "Creating service account: ${USER_SA_OF_EVENTARC_EMAIL}"
  gcloud iam service-accounts create "${USER_SA_OF_EVENTARC}" \
    --project="${PROJECT_ID}" \
    --description="Cloud Eventarc Service Account for Cloud Run Invoker"
else
  echo "Service account ${USER_SA_OF_EVENTARC_EMAIL} already exists. Skipping creation."
fi

# Grant role
echo "Granting Cloud Run Invoker role to Service Account for Cloud Eventarc"
gcloud run services add-iam-policy-binding "${GRANT_CLOUD_RUN_SERVICE}" \
  --member="serviceAccount:${USER_SA_OF_EVENTARC_EMAIL}" \
  --role="roles/run.invoker" \
  --region="${REGION}" \
  --project="${PROJECT_ID}"

# TODO: Eventarcの設定

echo "⭐️ All done!"
