#!/bin/bash
set -e

# Build the frontend
npm run build

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="iracing-schedule-${ACCOUNT_ID}"

# Sync built assets to S3 root with --delete to remove stale assets
aws s3 sync dist/ "s3://${BUCKET}/" --delete

# Invalidate CloudFront cache for this bucket's distribution
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[?starts_with(DomainName, '${BUCKET}.s3.')]].Id | [0]" \
  --output text)

if [ -n "${DISTRIBUTION_ID}" ] && [ "${DISTRIBUTION_ID}" != "None" ]; then
  aws cloudfront create-invalidation --distribution-id "${DISTRIBUTION_ID}" --paths "/*"
else
  echo "Error: Could not find CloudFront distribution for bucket ${BUCKET}" >&2
  exit 1
fi

echo "iracing-schedule frontend deploy complete!"
