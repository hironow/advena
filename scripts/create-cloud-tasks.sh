#!/bin/bash
set -euo pipefail

# Eventarc Invoke to Cloud Run for Cloud Eventarc
export PROJECT_ID="advena-dev"
export LOCATION="us-central1"
export TASKS_NAME="async-task-worker"

echo "=== Settings ==="
echo "PROJECT_ID:  $PROJECT_ID"
echo "LOCATION:  $LOCATION"
echo "TASKS_NAME:  $TASKS_NAME"
echo "================"

# Enable the Cloud Tasks API
gcloud services enable cloudtasks.googleapis.com --project "${PROJECT_ID}"

# Create a Cloud Tasks queue, if it does not exist
if gcloud tasks queues list --project "${PROJECT_ID}" --location $LOCATION --format json | jq -r '.[].name' | grep $TASKS_NAME; then
  # すでにあれば作成しない
  echo "Cloud Tasks queue ${TASKS_NAME} already exists. Skipping creation."
else
  gcloud tasks queues create "$TASKS_NAME" \
    --location "$LOCATION" \
    --project "$PROJECT_ID" \
    --log-sampling-ratio=1.0
  echo "Cloud Tasks queue ${TASKS_NAME} is created!"
fi

echo "⭐️ All done!"
