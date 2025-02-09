#!/bin/bash
set -euo pipefail

# Eventarc Invoke to Cloud Run for Cloud Eventarc
export PROJECT_ID="advena-dev"
export REGION="us-central1"
export FIRESTORE_LOCATION="nam5"
export GRANT_CLOUD_RUN_SERVICE="backend-advena"
export USER_SA_OF_EVENTARC="eventarc-invoke-cloud-run"
export USER_SA_OF_EVENTARC_EMAIL="${USER_SA_OF_EVENTARC}@${PROJECT_ID}.iam.gserviceaccount.com"
export DEAD_LETTER_TOPIC="backend-advena-dead-letter"

echo "=== Settings ==="
echo "PROJECT_ID:  $PROJECT_ID"
echo "REGION:  $REGION"
echo "FIRESTORE_LOCATION:  $FIRESTORE_LOCATION"
echo "GRANT_CLOUD_RUN_SERVICE:  $GRANT_CLOUD_RUN_SERVICE"
echo "USER_SA_OF_EVENTARC:  $USER_SA_OF_EVENTARC"
echo "USER_SA_OF_EVENTARC_EMAIL:  $USER_SA_OF_EVENTARC_EMAIL"
echo "DEAD_LETTER_TOPIC:  $DEAD_LETTER_TOPIC"
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

# Grant roles
# Cloud Pub/Sub needs the role to create identity tokens.
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
PUBSUB_DEFAULT_SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"
echo "Granting Pub/Sub Token Creator role to Service Account for Cloud Eventarc"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PUBSUB_DEFAULT_SERVICE_ACCOUNT}" \
  --role='roles/iam.serviceAccountTokenCreator' \
  --project="${PROJECT_ID}" --quiet
# Eventarc needs the role invoke Cloud Run services.
echo "Granting Cloud Run Invoker role to Service Account for Cloud Eventarc"
gcloud run services add-iam-policy-binding "${GRANT_CLOUD_RUN_SERVICE}" \
  --member="serviceAccount:${USER_SA_OF_EVENTARC_EMAIL}" \
  --role="roles/run.invoker" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" --quiet
# NOTE: eventarc.events.receiveEvent が必要
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${USER_SA_OF_EVENTARC_EMAIL}" \
  --role="roles/eventarc.eventReceiver" \
  --project="${PROJECT_ID}" --quiet

# Eventarcの設定
# NOTE: Eventarc用の dead leader を作成。topicのみを作成して、subscriptionは手動で作成する
if gcloud pubsub topics list --format json | jq -r '.[].name' | grep $DEAD_LETTER_TOPIC; then
  # すでにあれば作成しない
  echo "Dead letter topic ${DEAD_LETTER_TOPIC} already exists. Skipping creation."
else
  echo "Creating dead letter topic: ${DEAD_LETTER_TOPIC}"
  gcloud pubsub topics create $DEAD_LETTER_TOPIC \
    --project="${PROJECT_ID}"
fi
echo "Dead letter topic ${DEAD_LETTER_TOPIC} grant roles"
gcloud pubsub topics add-iam-policy-binding "${DEAD_LETTER_TOPIC}" \
  --member="serviceAccount:${PUBSUB_DEFAULT_SERVICE_ACCOUNT}" \
  --role="roles/pubsub.publisher" \
  --project="${PROJECT_ID}" --quiet


# NOTE: labelをつけても、Pub/Sub topic, subscriptionには反映されないので注意
ADD_USER_PATH="add_user"
ADD_USER_DOCUMENT="users/{userId}"
TRIGGER_ADD_USER_NAME="${GRANT_CLOUD_RUN_SERVICE}-add-user"
if gcloud eventarc triggers list --location="${FIRESTORE_LOCATION}" --format="value(name)" | grep -q "${TRIGGER_ADD_USER_NAME}"; then
  # すでに同名のトリガーが存在する場合は作成しない
  echo "Trigger ${TRIGGER_ADD_USER_NAME} already exists. Skipping creation."
else
  # トリガーはFirestoreと同じlocationに作成する
  echo "Creating trigger: ${TRIGGER_ADD_USER_NAME}"
  gcloud eventarc triggers create "${TRIGGER_ADD_USER_NAME}" \
    --location="${FIRESTORE_LOCATION}" \
    --destination-run-service="${GRANT_CLOUD_RUN_SERVICE}" \
    --destination-run-region="${REGION}" \
    --event-filters="type=google.cloud.firestore.document.v1.created" \
    --event-filters="database=(default)" \
    --event-filters-path-pattern="document=${ADD_USER_DOCUMENT}" \
    --service-account="${USER_SA_OF_EVENTARC_EMAIL}" \
    --event-data-content-type="application/protobuf" \
    --destination-run-path="/${ADD_USER_PATH}"
fi
ADD_RADIO_SHOW_PATH="add_radio_show"
ADD_RADIO_SHOW_DOCUMENT="radio_shows/{radioShowId}"
TRIGGER_ADD_RADIO_SHOW_NAME="${GRANT_CLOUD_RUN_SERVICE}-add-radio-show"
if gcloud eventarc triggers list --location="${FIRESTORE_LOCATION}" --format="value(name)" | grep -q "${TRIGGER_ADD_RADIO_SHOW_NAME}"; then
  # すでに同名のトリガーが存在する場合は作成しない
  echo "Trigger ${TRIGGER_ADD_RADIO_SHOW_NAME} already exists. Skipping creation."
else
  # トリガーはFirestoreと同じlocationに作成する
  echo "Creating trigger: ${TRIGGER_ADD_RADIO_SHOW_NAME}"
  gcloud eventarc triggers create "${TRIGGER_ADD_RADIO_SHOW_NAME}" \
    --location="${FIRESTORE_LOCATION}" \
    --destination-run-service="${GRANT_CLOUD_RUN_SERVICE}" \
    --destination-run-region="${REGION}" \
    --event-filters="type=google.cloud.firestore.document.v1.created" \
    --event-filters="database=(default)" \
    --event-filters-path-pattern="document=${ADD_RADIO_SHOW_DOCUMENT}" \
    --service-account="${USER_SA_OF_EVENTARC_EMAIL}" \
    --event-data-content-type="application/protobuf" \
    --destination-run-path="/${ADD_RADIO_SHOW_PATH}"
fi
# TODO: 以降追加のtriggerがあれば、同様に作成する

echo "waiting... for create eventarc's Pub/Sub topic and subscription"
# 2分
sleep 120 

# triggerごとの処理を別scriptに分けているので実行
# NOTE: 失敗している可能性があるので、確認後、手動で実行する場合もある
bash ./scripts/update-eventarc-trigger.sh "${TRIGGER_ADD_USER_NAME}"
bash ./scripts/update-eventarc-trigger.sh "${TRIGGER_ADD_RADIO_SHOW_NAME}"
# TODO: 以降追加のtriggerがあれば、同様に作成する

echo "⭐️ All done!"
