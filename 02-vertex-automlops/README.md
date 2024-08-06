# Using AutoMLOPs


## Instructions

1. Setup google cloud credentials: `gcloud auth application-default login` and `gcloud config set account <account@example.com>`
2. Manually go to Bigquery and upload `preproc.csv` as a new table
3. Run `python3 infra.py`
4. Test that everything works `python3 test.py`
