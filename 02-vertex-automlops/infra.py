import datetime
from google_cloud_automlops import AutoMLOps
from google_cloud_automlops.AutoMLOps import component
from google.cloud import aiplatform
from functions import create_dataset, train_model, deploy_model

PROJECT_ID = 'mlops-devrel'
MODEL_ID = 'dry-beans-dt'
TRAINING_DATASET = f'{PROJECT_ID}.test_dataset.dry_beans'
TARGET_COLUMN = 'Class'
REGION = 'us-central1'
MODEL_DIRECTORY = f'gs://{PROJECT_ID}-{MODEL_ID}-bucket/trained_models/{datetime.datetime.now()}'
DATA_PATH = f'gs://{PROJECT_ID}-{MODEL_ID}-bucket/data.csv'



create_dataset = component(
    packages_to_install=[
        'google-cloud-bigquery',
        'pandas',
        'pyarrow',
        'db_dtypes',
        'fsspec',
        'gcsfs'
    ]
)(create_dataset)



train_model = component(
    packages_to_install=[
        'scikit-learn==1.2.2',
        'pandas',
        'joblib',
        'tensorflow'
    ]
)(train_model)

deploy_model = component(
    packages_to_install=[
        'google-cloud-aiplatform'
    ]
)(deploy_model)


@AutoMLOps.pipeline #(name='automlops-pipeline', description='This is an optional description')
def pipeline(
    bq_table: str,
    model_directory: str,
    data_path: str,
    project_id: str,
    region: str):

    create_dataset_task = create_dataset(
        bq_table=bq_table,
        data_path=data_path,
        project_id=project_id)

    train_model_task = train_model(
        model_directory=model_directory,
        data_path=data_path).after(create_dataset_task)

    deploy_model_task = deploy_model(
        model_directory=model_directory,
        project_id=project_id,
        region=region).after(train_model_task)



pipeline_params = {
    'bq_table': TRAINING_DATASET,
    'model_directory': MODEL_DIRECTORY,
    'data_path': DATA_PATH,
    'project_id': PROJECT_ID,
    'region': REGION
}


if __name__ == "__main__": 

    # %%
    AutoMLOps.generate(
           project_id=PROJECT_ID,
           pipeline_params=pipeline_params,
           use_ci=True,
           naming_prefix=MODEL_ID,
           schedule_pattern='59 11 * * 0', # retrain every Sunday at Midnight
           setup_model_monitoring=True     # use this if you would like to use Vertex Model Monitoring
    )


    # %%
    AutoMLOps.provision(hide_warnings=False)

    # %%
    AutoMLOps.deploy(precheck=True, hide_warnings=False)

    # Wait before this step #
    # 1. Wait for code to be pushed
    # 2. Wait for automatic build to be triggered
    # 3. Wait for pipeline to run.


    # %%
    aiplatform.init(project=PROJECT_ID, location=REGION)
    beans_endpoints = aiplatform.Endpoint.list(filter=f'display_name="beans-model_endpoint"')

    # Grab the most recent beans-model deployment
    endpoint_name = beans_endpoints[0].resource_name
    endpoint_name

    AutoMLOps.monitor(
        alert_emails=[], # update if you would like to receive email alerts
        target_field=TARGET_COLUMN,
        model_endpoint=endpoint_name,
        monitoring_interval=1,
        monitoring_location=REGION,
        auto_retraining_params=pipeline_params,
        drift_thresholds={'Area': 0.000001, 'Perimeter': 0.000001},
        skew_thresholds={'Area': 0.000001, 'Perimeter': 0.000001},
        training_dataset=f'bq://{TRAINING_DATASET}',
        hide_warnings=False
    )


