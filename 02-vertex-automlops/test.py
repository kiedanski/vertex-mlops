import pandas as pd
from google.cloud import bigquery
from google.cloud import aiplatform
from infra import PROJECT_ID, TRAINING_DATASET, REGION
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

def get_query(bq_input_table: str) -> str:
    """Generates BQ Query to read data.

    Args:
        bq_input_table: The full name of the bq input table to be read into
        the dataframe (e.g. <project>.<dataset>.<table>)

    Returns: A BQ query string.
    """
    return f'''SELECT * FROM `{bq_input_table}`'''

def load_bq_data(query: str, client: bigquery.Client) -> pd.DataFrame:
    """Loads data from bq into a Pandas Dataframe for EDA.

    Args:
        query: BQ Query to generate data.
        client: BQ Client used to execute query.

    Returns:
        pd.DataFrame: A dataframe with the requested data.
    """
    df = client.query(query).to_dataframe()
    return df

bq_client = bigquery.Client(project=PROJECT_ID)
aiplatform.init(project=PROJECT_ID, location=REGION)
beans_endpoints = aiplatform.Endpoint.list(filter=f'display_name="beans-model_endpoint"')

# Grab the most recent beans-model deployment
endpoint_name = beans_endpoints[0].resource_name
endpoint_name

# Get samples
df = load_bq_data(get_query(TRAINING_DATASET), bq_client)
X_sample = df.iloc[:,:-1][:5000].values.tolist()

endpoint = aiplatform.Endpoint(endpoint_name)
response = endpoint.predict(instances=X_sample)
prediction = response[0]
# print the first prediction
print(prediction[0])

print(classification_report(df.iloc[:,-1][:5000].values, prediction))
