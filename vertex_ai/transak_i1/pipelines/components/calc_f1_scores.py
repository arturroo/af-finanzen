from kfp.dsl import component, Input
from google_cloud_pipeline_components.types.artifact_types import ClassificationMetrics
from typing import NamedTuple
import json

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-pipeline-components"],
)
def calc_f1_scores_op(
    evaluation_candidate: Input[ClassificationMetrics],
    evaluation_production: Input[ClassificationMetrics],
) -> NamedTuple("Outputs", [
    ("max_f1_macro_candidate", float),
    ("max_f1_macro_production", float),
]):
    """
    Calculates the maximum F1-macro score from evaluation metrics.
    It reads the metrics from the local path of the input artifacts.
    """
    def _get_max_f1_macro(artifact_path: str) -> float:
        print(f"Reading artifact from local path: {artifact_path}")
        try:
            with open(artifact_path, 'r') as f:
                evaluation_data = json.load(f)
        except Exception as e:
            print(f"Error reading or parsing evaluation data from {artifact_path}: {e}")
            return 0.0

        print(f"Evaluation data keys: {list(evaluation_data.keys())}")

        max_f1 = 0.0
        if 'confidenceMetrics' in evaluation_data:
            for metric in evaluation_data['confidenceMetrics']:
                if 'f1ScoreMacro' in metric and metric['f1ScoreMacro'] is not None:
                    f1_score = metric['f1ScoreMacro']
                    if f1_score > max_f1:
                        max_f1 = f1_score
        else:
            print(f"Warning: 'confidenceMetrics' key not found in evaluation data from {artifact_path}")

        if max_f1 == 0.0:
            print("Warning: Could not find a valid f1ScoreMacro, returning 0.0")

        return max_f1

    # --- Main execution ---
    # Handle the case where production model might not exist on first run
    if evaluation_production.uri == "gcs://dummy/uri":
        print("Production model evaluation is a dummy, skipping calculation.")
        production_f1 = 0.0
    else:
        production_f1 = _get_max_f1_macro(evaluation_production.path)

    candidate_f1 = _get_max_f1_macro(evaluation_candidate.path)

    print(f"Candidate max_f1_macro: {candidate_f1}")
    print(f"Production max_f1_macro: {production_f1}")

    return (candidate_f1, production_f1)
