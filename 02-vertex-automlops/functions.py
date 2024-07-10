
def create_dataset(
    bq_table: str,
    data_path: str,
    project_id: str
):
    """Custom component that takes in a BQ table and writes it to GCS.

    Args:
        bq_table: The source biquery table.
        data_path: The gcs location to write the csv.
        project_id: The project ID.
    """
    from google.cloud import bigquery
    import pandas as pd
    from sklearn import preprocessing

    bq_client = bigquery.Client(project=project_id)

    def get_query(bq_input_table: str) -> str:
        """Generates BQ Query to read data.

        Args:
            bq_input_table: The full name of the bq input table to be read into
                the dataframe (e.g. <project>.<dataset>.<table>)
        Returns: A BQ query string.
        """
        return f'''
        SELECT *
        FROM `{bq_input_table}`
        '''

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

    dataframe = load_bq_data(get_query(bq_table), bq_client)
    dataframe.to_csv(data_path, index=False)


def train_model(
    data_path: str,
    model_directory: str
):
    """Custom component that trains a decision tree on the training data.

    Args:
        data_path: GS location of the training data.
        model_directory: GS location of saved model.
    """
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import train_test_split
    import pandas as pd
    import tensorflow as tf
    import pickle
    import os

    def save_model(model, uri):
        """Saves a model to uri."""
        with tf.io.gfile.GFile(uri, 'w') as f:
            pickle.dump(model, f)

    df = pd.read_csv(data_path)

    labels = df.pop('Class').tolist()
    data = df.values.tolist()

    x_train, x_test, y_train, y_test = train_test_split(data, labels)
    skmodel = DecisionTreeClassifier()
    skmodel.fit(x_train,y_train)
    score = skmodel.score(x_test,y_test)
    print('accuracy is:',score)

    output_uri = os.path.join(model_directory, 'model.pkl')
    save_model(skmodel, output_uri)


def deploy_model(
    model_directory: str,
    project_id: str,
    region: str
):
    """Custom component that uploads a saved model from GCS to Vertex Model Registry
       and deploys the model to an endpoint for online prediction.

    Args:
        model_directory: GS location of saved model.
        project_id: Project_id.
        region: Region.
    """
    import pprint as pp
    import random

    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=region)
    # Check if model exists
    models = aiplatform.Model.list()
    model_name = 'beans-model'
    if 'beans-model' in (m.name for m in models):
        parent_model = model_name
        model_id = None
        is_default_version=False
        version_aliases=['experimental', 'challenger', 'custom-training', 'decision-tree']
        version_description='challenger version'
    else:
        parent_model = None
        model_id = model_name
        is_default_version=True
        version_aliases=['champion', 'custom-training', 'decision-tree']
        version_description='first version'

    serving_container = 'us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-2:latest'
    uploaded_model = aiplatform.Model.upload(
        artifact_uri=model_directory,
        model_id=model_id,
        display_name=model_name,
        parent_model=parent_model,
        is_default_version=is_default_version,
        version_aliases=version_aliases,
        version_description=version_description,
        serving_container_image_uri=serving_container,
        serving_container_ports=[8080],
        labels={'created_by': 'automlops-team'},
    )

    endpoint = uploaded_model.deploy(
        machine_type='n1-standard-4',
        deployed_model_display_name='deployed-beans-model')

    sample_input = [[random.uniform(0, 300) for x in range(16)]]

    # Test endpoint predictions
    print('running prediction test...')
    try:
        resp = endpoint.predict(instances=sample_input)
        pp.pprint(resp)
    except Exception as ex:
        print('prediction request failed', ex)
