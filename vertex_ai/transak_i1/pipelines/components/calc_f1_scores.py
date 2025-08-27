from kfp.dsl import component, Input, Output
from google_cloud_pipeline_components.types.artifact_types import ClassificationMetrics

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-storage"],
)
def calc_f1_scores_op(
    candidate_evaluation_artifact: Input[ClassificationMetrics],
    production_evaluation_artifact: Input[ClassificationMetrics],
    max_f1_micro_candidate: Output[float],
    max_f1_micro_production: Output[float],
):
    """
    A component that calculates the maximum F1-micro score for both
    candidate and production model evaluations.
    """
    import json
    from google.cloud import storage

    def _get_max_f1_micro(artifact_uri: str) -> float:
        if not artifact_uri or artifact_uri == "gcs://dummy/uri":
            print(f"Warning: Artifact URI is empty or dummy: {artifact_uri}. Returning 0.0.")
            return 0.0

        print(f"Reading artifact from: {artifact_uri}")
        client = storage.Client()
        # Assuming the URI is gs://bucket/path/to/evaluation.json
        path_parts = artifact_uri.replace("gs://", "").split("/", 1)
        bucket_name = path_parts[0]
        blob_name = path_parts[1]

        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        try:
            content = blob.download_as_text()
            evaluation_data = json.loads(content)
        except Exception as e:
            print(f"Error downloading or parsing evaluation data from {artifact_uri}: {e}")
            return 0.0

        max_f1 = 0.0
        if 'metrics' in evaluation_data and 'confidenceMetrics' in evaluation_data['metrics']:
            for metric in evaluation_data['metrics']['confidenceMetrics']:
                if 'f1ScoreMicro' in metric:
                    f1_score = metric['f1ScoreMicro']
                    if f1_score > max_f1:
                        max_f1 = f1_score
        else:
            print(f"'metrics' or 'confidenceMetrics' not found in evaluation data from {artifact_uri}")

        return max_f1

    # Calculate for candidate model
    candidate_f1 = _get_max_f1_micro(candidate_evaluation_artifact.uri)
    max_f1_micro_candidate.write(candidate_f1)
    print(f"Candidate max_f1_micro: {candidate_f1}")

    # Calculate for production model
    production_f1 = _get_max_f1_micro(production_evaluation_artifact.uri)
    max_f1_micro_production.write(production_f1)
    print(f"Production max_f1_micro: {production_f1}")
