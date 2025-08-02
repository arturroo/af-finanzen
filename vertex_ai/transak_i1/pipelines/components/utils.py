from kfp.dsl import container_component, Input, Output, Dataset, ContainerSpec

@container_component
def get_artifact_uri_op(
    input_artifact: Input[Dataset],
    output_uri: Output[str],
):
    """
    A lightweight component to extract the GCS URI of an input artifact.
    """
    return ContainerSpec(
        image='python:3.9',
        command=[
            'python',
            '-c',
            'import sys; with open(sys.argv[2], "w") as f: f.write(sys.argv[1])'
        ],
        args=[
            input_artifact.path,
            output_uri.path,
        ]
    )
