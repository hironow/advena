#!/bin/bash
set -euo pipefail

EVENTARC_NAME=$1

# settings
PROJECT_ID="advena-dev"
DEAD_LETTER_TOPIC="backend-advena-dead-letter"

echo "=== Settings ==="
echo "PROJECT_ID:  $PROJECT_ID"
echo "EVENTARC_NAME:  $EVENTARC_NAME"
echo "DEAD_LETTER_TOPIC:  $DEAD_LETTER_TOPIC"
echo "================"

# Pub/Sub needs the role to subscribe to the topic.
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
PUBSUB_DEFAULT_SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"

# timeoutを伸ばし、Dead Letter Topicを設定
SUBSCRIPTION=$(gcloud pubsub subscriptions list --format json | jq -r '.[].name' | grep "$EVENTARC_NAME")
echo "Update subscription ${SUBSCRIPTION} for long ack deadline"
gcloud pubsub subscriptions update "${SUBSCRIPTION}" \
  --ack-deadline 300 \
  --dead-letter-topic $DEAD_LETTER_TOPIC \
  --min-retry-delay 300 \
  --max-retry-delay 600

# Grant roles
gcloud pubsub subscriptions add-iam-policy-binding "${SUBSCRIPTION}" \
  --member="serviceAccount:${PUBSUB_DEFAULT_SERVICE_ACCOUNT}" \
  --role="roles/pubsub.subscriber"

echo "⭐️ ${SUBSCRIPTION} is updated!"
