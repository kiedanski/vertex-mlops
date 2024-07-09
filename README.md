# vertex-mlops

## Setup Guide

Following this guide 
https://github.com/google-github-actions/auth#direct-wif
on the (Preferred) Direct Workload Identity Federation section>>Click here to show detailed instructions for configuring GitHub authentication to Google Cloud via a direct Workload Identity Federation.
( below the diagram )
For the last line , in order to get the right sintaxis for member i used this documentation 
https://cloud.google.com/iam/docs/workload-identity-federation
 
```
gcloud iam workload-identity-pools create "github" \
  --project="vertex-llm-finetune" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```


```
gcloud iam workload-identity-pools describe "github" \
  --project="vertex-llm-finetune"\
  --location="global" \
  --format="value(name)"
```

output:
##projects/7029402384/locations/global/workloadIdentityPools/github


_____

3.
```
gcloud iam workload-identity-pools providers create-oidc "my-repo" \
  --project="vertex-llm-finetune" \
  --location="global" \
  --workload-identity-pool="github" \
  --display-name="My GitHub repo Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == 'kiedanski'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

—--
```
gcloud iam workload-identity-pools providers describe "my-repo" \                                                                                    --project="vertex-llm-finetune" \
  --location="global" \
  --workload-identity-pool="github" \
  --format="value(name)"
```

output:
## projects/7029402384/locations/global/workloadIdentityPools/github/providers/my-repo

—---------
```
gcloud storage buckets add-iam-policy-binding gs://bucket-for-storing-embeddings \                                                                   --project="vertex-llm-finetune" \                          
  --role="roles/storage.objectCreator" \                                                                                                                                     

member="principalSet://iam.googleapis.com/projects/7029402384/locations/global/workloadIdentityPools/github/attribute.repository/kiedanski/vertex-mlops"
```
