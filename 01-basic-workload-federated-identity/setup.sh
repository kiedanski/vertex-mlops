# Get Project Variables

[[ -z $GITHUB_ORG ]] && echo "GITHUB_ORG is unset. Run export \$GITHUB_ORG=... and re run this script" && exit 0
[[ -z $REPO_NAME ]] && echo "REPO_NAME is unset. Run export \$REPO_NAME=... and re run this script" && exit 0


export PROJECT_ID=$(gcloud config get-value project)
echo $PROJECT_ID



export BUCKET_NAME="wfi-testing"
export POOL_NAME="github-new"
export PROVIDER_NAME="my-repository"

echo $BUCKET_NAME $POOL_NAME $PROVIDER_NAME

# Setup the necessary services and resources

gcloud iam service-accounts create "my-service-account-2" \
  --project "${PROJECT_ID}" || true

gcloud iam workload-identity-pools create "$POOL_NAME" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool" || true


export WORKLOAD_ID=$(gcloud iam workload-identity-pools describe "$POOL_NAME" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --format="value(name)") || true
echo $WORKLOAD_ID


gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --display-name="My GitHub repo Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == '${GITHUB_ORG}'" \
  --issuer-uri="https://token.actions.githubusercontent.com" || true

# Create a bucket if it does not exist and give the pool access to it 

gcloud storage buckets create "gs://${BUCKET_NAME}"



gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
	--project=$PROJECT_ID \
	--role="roles/storage.objectCreator" \
	--member="principalSet://iam.googleapis.com/$WORKLOAD_ID/attribute.repository/$GITHUB_ORG/$REPO_NAME"

