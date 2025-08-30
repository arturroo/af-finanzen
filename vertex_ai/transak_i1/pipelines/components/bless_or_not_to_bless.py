from kfp.v2.dsl import component, Input
from google_cloud_pipeline_components.types.artifact_types import ClassificationMetrics
from typing import NamedTuple

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform", "google-cloud-pipeline-components"],
)
def bless_or_not_to_bless_op(
    candidate_metrics: Input[ClassificationMetrics],
    production_metrics: Input[ClassificationMetrics],
) -> NamedTuple("Outputs", [("decision", str)]):
    """
    Compares the F1 score of the candidate and production models
    and returns a decision string: 'bless' or 'not_to_bless'.
    """
    candidate_f1 = candidate_metrics.metadata.get('max_f1_macro', 0.0)
    production_f1 = production_metrics.metadata.get('max_f1_macro', 0.0)

    print(f"Candidate F1 Score: {candidate_f1}")
    print(f"Production F1 Score: {production_f1}")

    if candidate_f1 > production_f1:
        decision = "bless"
    else:
        decision = "not_to_bless"

    print(f"Decision: {decision}")

    from collections import namedtuple
    outputs = namedtuple("Outputs", ["decision"])
    return outputs(decision)
