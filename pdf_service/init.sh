#!/bin/bash
set -e

echo "Initializing LocalStack resources..."

# Create SQS queue
awslocal sqs create-queue \
    --queue-name pdf-jobs \
    --region us-east-1

echo "SQS queue 'pdf-jobs' created"

# Create S3 bucket
awslocal s3 mb s3://pdf-profiles --region us-east-1

echo "S3 bucket 'pdf-profiles' created"
echo "LocalStack initialization complete!"
