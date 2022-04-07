#!/usr/bin/env bash

set -euo pipefail

# enable debug
# set -x

echo "Configuring SQS..."
echo "HOSTNAME:${HOSTNAME}"
echo "AWS_REGION_NAME:${AWS_REGION_NAME}"
create_queue() {
    local QUEUE_NAME_TO_CREATE=$1
    awslocal --endpoint-url=http://${HOSTNAME}:4566 sqs create-queue --queue-name ${QUEUE_NAME_TO_CREATE} --region ${AWS_REGION_NAME} --attributes VisibilityTimeout=3600
}
echo "Creating Queues.."
create_queue "default"
echo "Creating Queues..Done"
echo "Configuring SQS...Done"
