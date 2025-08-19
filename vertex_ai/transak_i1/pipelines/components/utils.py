from kfp.dsl import component, Input, Output, Dataset, Artifact, container_component, ContainerSpec

# @container_component
# def get_artifact_uri_op(
#     input_artifact: Input[Dataset],
#     output_uri: Output[str],
# ):
#     """
#     A lightweight component to extract the GCS URI of an input artifact.
#     """
#     return ContainerSpec(
#         image='python:3.9',
#         command=[
#             'python',
#             '-c',
#             'import sys; with open(sys.argv[2], "w") as f: f.write(sys.argv[1])'
#         ],
#         args=[
#             input_artifact.path,
#             output_uri.path,
#         ]
#     )

@component(
    base_image='python:3.9',
)
def get_artifact_uri(
    artifact: Input[Artifact],
) -> str:
    return artifact.uri

@component(
    base_image='python:3.9',
)
def read_json_labels_op(
    labels_file: Input[Artifact]
) -> list:
    import json
    with open(labels_file.path) as f:
        return json.load(f)

@component(
    base_image='python:3.9',
)
def get_artifact_uri_list(
    artifact: Input[Artifact],
) -> list:
    return [artifact.uri]
