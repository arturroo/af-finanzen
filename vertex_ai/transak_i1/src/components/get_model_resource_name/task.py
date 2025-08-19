import argparse
import os

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vertex-model-path', required=True, type=str)
    parser.add_argument('--model-resource-name-path', required=True, type=str)
    return parser.parse_args()

def main():
    args = _parse_args()

    # Read the model resource name from the input path
    with open(args.vertex_model_path, 'r') as f:
        model_resource_name = f.read().strip()

    print(f"Extracted model resource name: {model_resource_name}")

    # Write the model resource name to the output path
    os.makedirs(os.path.dirname(args.model_resource_name_path), exist_ok=True)
    with open(args.model_resource_name_path, 'w') as f:
        f.write(model_resource_name)

if __name__ == '__main__':
    main()
