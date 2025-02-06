#!/bin/bash
set -euo pipefail

# Schedule Invoke to Cloud Run for Cloud Scheduler
export PROJECT_ID="advena-dev"
export REGION="us-central1"
export GRANT_CLOUD_RUN_SERVICE="backend-advena"
export USER_SA_OF_SCHEDULER="schedule-invoke-cloud-run"
export USER_SA_OF_SCHEDULER_EMAIL="${USER_SA_OF_SCHEDULER}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== Settings ==="
echo "PROJECT_ID:  $PROJECT_ID"
echo "REGION:  $REGION"
echo "GRANT_CLOUD_RUN_SERVICE:  $GRANT_CLOUD_RUN_SERVICE"
echo "USER_SA_OF_SCHEDULER:  $USER_SA_OF_SCHEDULER"
echo "USER_SA_OF_SCHEDULER_EMAIL:  $USER_SA_OF_SCHEDULER_EMAIL"
echo "================"

# Enable the Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com --project "${PROJECT_ID}"

# サービスアカウントの存在チェックと作成
if ! gcloud iam service-accounts list \
    --filter="email:${USER_SA_OF_SCHEDULER_EMAIL}" \
    --format="value(email)" | grep -q "${USER_SA_OF_SCHEDULER_EMAIL}"; then
  echo "Creating service account: ${USER_SA_OF_SCHEDULER_EMAIL}"
  gcloud iam service-accounts create "${USER_SA_OF_SCHEDULER}" \
    --project="${PROJECT_ID}" \
    --description="Cloud Scheduler Service Account for Cloud Run Invoker"
else
  echo "Service account ${USER_SA_OF_SCHEDULER_EMAIL} already exists. Skipping creation."
fi

# Grant role
echo "Granting Cloud Run Invoker role to Service Account for Cloud Scheduler"
gcloud run services add-iam-policy-binding "${GRANT_CLOUD_RUN_SERVICE}" \
  --member="serviceAccount:${USER_SA_OF_SCHEDULER_EMAIL}" \
  --role="roles/run.invoker" \
  --region="${REGION}" \
  --project="${PROJECT_ID}"

# 付与されているrolesを確認
echo "Check the roles granted to the Cloud Scheduler service account"
gcloud run services get-iam-policy "${GRANT_CLOUD_RUN_SERVICE}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}"

echo "⭐️ All done!"
