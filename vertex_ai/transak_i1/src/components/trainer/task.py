import argparse
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import os
from google.cloud import aiplatform

# Import model-building logic from the same package
from .model import build_model, create_stateful_preprocessing_layers
from src.common.utils import df2dataset

def _parse_args():
    """Parses command-line arguments for the training task."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--train-data-uri', required=True, type=str, help='GCS path to the training CSV file.')
    parser.add_argument('--val-data-uri', required=True, type=str, help='GCS path to the validation CSV file.')
    parser.add_argument('--output-model-path', required=True, type=str, help='GCS path to save the exported model.')
    parser.add_argument('--vertex-model-path', required=True, type=str, help='Local path to write the Vertex AI Model resource name.')
    parser.add_argument('--num-epochs', required=True, type=int, help='Number of training epochs.')
    parser.add_argument('--learning-rate', required=True, type=float, help='Learning rate for the optimizer.')
    parser.add_argument('--batch-size', required=True, type=int, help='Training and validation batch size.')
    parser.add_argument('--num-classes', required=True, type=int, help='Number of output classes.')
    parser.add_argument('--tensorboard-resource-name', required=True, type=str)
    parser.add_argument('--project-id', required=True, type=str, help='GCP Project ID.')
    parser.add_argument('--region', required=True, type=str, help='GCP Region for Vertex AI resources.')
    parser.add_argument('--experiment-name', required=True, type=str, help='Name of the experiment for tracking.')
    # parser.add_argument('--run-name', required=True, type=str, help='Name of the run for tracking.')
    parser.add_argument('--model-display-name', required=True, type=str, help='Display name for the model in Vertex AI Model Registry.')
    parser.add_argument('--serving-container-image-uri', required=True, type=str, help='URI of the serving container image.')
    return parser.parse_args()


def main():
    """Main entrypoint for the training task."""
    args = _parse_args()
    
    print("Initializing AI Platform with autologging...")
    aiplatform.init(project=args.project_id, 
                    location=args.region, 
                    experiment=args.experiment_name, 
                    experiment_tensorboard=args.tensorboard_resource_name
                    )
    aiplatform.autolog()
    
    #with aiplatform.start_run(
    #    #run=args.run_name, 
    #    resume=True
    #    ) as experiment_run:
    
    # 1. Load Data
    train_df = pd.read_csv(args.train_data_uri)
    val_df = pd.read_csv(args.val_data_uri)

    # Drop the 'tid' column as it's not a feature for the model
    if 'tid' in train_df.columns:
        train_df = train_df.drop(columns=['tid'])
    if 'tid' in val_df.columns:
        val_df = val_df.drop(columns=['tid'])

    train_ds = df2dataset(train_df, batch_size=args.batch_size)
    val_ds = df2dataset(val_df, shuffle=False, batch_size=args.batch_size)

    # 2. Create and Adapt Preprocessing Layers
    layer_hyperparams = {'desc_vocab_size': 5000}
    preprocessing_layers = create_stateful_preprocessing_layers(layer_hyperparams)

    preprocessing_layers['description_text_vectorizer'].adapt(train_ds.map(lambda x, y: x['description']))
    preprocessing_layers['type_lookup'].adapt(train_ds.map(lambda x, y: x['type']))
    preprocessing_layers['currency_lookup'].adapt(train_ds.map(lambda x, y: x['currency']))

    df_for_adapt = train_df.copy()
    df_for_adapt['amount_log'] = np.log1p(np.abs(df_for_adapt['amount']))
    df_for_adapt['amount_sign'] = (df_for_adapt['amount'] >= 0).astype(np.float32)
    numeric_features_for_adapt = df_for_adapt[['started_year', 'first_started_year', 'amount_log', 'amount_sign']].values
    preprocessing_layers['normalizer'].adapt(numeric_features_for_adapt)

    # 3. Build and Compile Model
    model_hyperparams = {
        'desc_hash_bins': 1000,
        'cross_bins': 5000,
        'num_classes': args.num_classes,
        'desc_embedding_dim': 32,
        'type_embedding_dim': 4,
        'currency_embedding_dim': 3,
        'learning_rate': args.learning_rate
    }
    model = build_model(
        preprocessing_layers=preprocessing_layers, 
        hyperparams=model_hyperparams
    )
    model.summary()

    # 4. Train Model    
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=3, verbose=1, restore_best_weights=True
    )
    tfboard = tf.keras.callbacks.TensorBoard(
        log_dir=os.getenv('AIP_TENSORBOARD_LOG_DIR'), # Do not work. I could not get tensorboard working with this
        # update_freq='epoch',
        histogram_freq=1,
        write_graph=True,
        write_images=True
    )
    # print(f"Tensorboard resource name: {tfboard.resource_name}")
    print(f"Tensorboard log directory: {tfboard.log_dir}")

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.num_epochs,
        callbacks=[early_stopping, tfboard]
    )

    # 5. Export Model for Deployment
    print(f"TF2 Model export: args.output_model_path: {args.output_model_path}")
    os.makedirs(os.path.dirname(args.output_model_path), exist_ok=True)
    print(f"TF2 Model export to: {args.output_model_path}")
    model.export(args.output_model_path)
    if os.path.exists(os.path.join(args.output_model_path, "saved_model.pb")):
        print("TF2 Model export - Verification successful: saved_model.pb file was created.")
    else:
        print("TF2 Model export - Verification FAILED: saved_model.pb file was NOT created.")

    keras_model_file_name = "model.keras"
    print(f"Keras Model local export: args.output_model_path: {args.output_model_path}")
    print(f"Keras Model local export to: {keras_model_file_name}")
    model.save(keras_model_file_name)
    if os.path.exists(keras_model_file_name):
        print(f"Keras Model local export - Verification successful: {keras_model_file_name} file was created.")
    else:
        print(f"Keras Model local export - Verification FAILED: {keras_model_file_name} file was NOT created.")

    # Dirty hack to allow filtering models that do not meet minimum evaluation metric ceriteria
    import re
    gs_keras_model_path = re.sub(r"(gs://.*?)/pipelines", r"\1/keras/pipelines", args.output_model_path.replace('/gcs/', 'gs://', 1))
    print(f"gsutil cp model.keras {gs_keras_model_path}/{keras_model_file_name}")
    os.system(f"gsutil cp model.keras {gs_keras_model_path}/{keras_model_file_name}")

    # Look for an existing model with the same display name to set as parent
    print(f"Searching for parent model with display name: {args.model_display_name}")
    parent_model_resource_name = None
    models = aiplatform.Model.list(
        filter=f'display_name="{args.model_display_name}"',
        project=args.project_id,
        location=args.region,
    )
    if models:
        parent_model_resource_name = models[0].resource_name
        print(f"Found parent model: {parent_model_resource_name}")
    else:
        print("No parent model found. A new model entry will be created.")

    # Upload the model to Vertex AI Model Registry
    print(f"Uploading model to Vertex AI Model Registry: {args.model_display_name}")
    vertex_model = aiplatform.Model.upload(
        display_name=args.model_display_name,
        parent_model=parent_model_resource_name,
        artifact_uri=args.output_model_path,
        serving_container_image_uri=args.serving_container_image_uri,
        description="Wide & Deep transaction classifier trained via a Vertex AI Pipeline.",
        sync=True # Waits for the upload to complete
    )
    print(f"Model uploaded to registry: {vertex_model.resource_name}")

    # Write the Vertex Model resource name to the specified path
    with open(args.vertex_model_path, 'w') as f:
        f.write(vertex_model.resource_name)

if __name__ == '__main__':
    main()
