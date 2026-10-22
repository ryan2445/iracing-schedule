#!/bin/bash
set -e

# Build the frontend
npm run build

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="road-analysis-reports-${ACCOUNT_ID}"

# Sync built assets to S3 tracker/ prefix with --delete to remove stale assets
aws s3 sync dist/ "s3://${BUCKET}/tracker/" --delete

echo "Tracker deploy complete!"
