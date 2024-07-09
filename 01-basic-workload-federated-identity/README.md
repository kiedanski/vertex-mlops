# Setup the necessary services and resources


```sh
source variables.sh
```

```sh
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
  --project "${PROJECT_ID}" || true
```


```sh
gcloud iam workload-identity-pools create "$POOL_NAME" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool" || true
```


```sh
export WORKLOAD_ID=$(gcloud iam workload-identity-pools describe "$POOL_NAME" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --format="value(name)") || true
echo $WORKLOAD_ID
```


```sh
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --display-name="My GitHub repo Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == '${GITHUB_ORG}'" \
  --issuer-uri="https://token.actions.githubusercontent.com" || true
  ```

```sh
export PROVIDER_FULL_PATH=$(gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
	--project="$PROJECT_ID" \
	--location="global" \
	--workload-identity-pool="POOL_NAME" \
	--format="value(name)")
echo $PROVIDER_FULL_PATH
```

# Create Bucket and give it the appropiate permissions [Workflow Specific]

We create the bucket used to upload the files

```sh
gcloud storage buckets create "gs://${BUCKET_NAME}"
```

Token requires uniform bucket level access, so we enable it.
```sh
gcloud storage buckets update gs://testing-bucket-09072024 --uniform-bucket-level-access
```

We give the pool permissions to write to the bucket 

```
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
	--project=$PROJECT_ID \
	--role="roles/storage.objectCreator" \
	--member="principalSet://iam.googleapis.com/$WORKLOAD_ID/attribute.repository/$GITHUB_ORG/$REPO_NAME"
```


# Generate the Github Action 

We generate the github action replacing existing environmental variables

```sh
envsubst '$PROVIDER_FULL_PATH,$PROJECT_ID,$BUCKET_NAME' < action.yaml > ../.github/workflows/01-basic-workload-federated-identity.yaml
```
