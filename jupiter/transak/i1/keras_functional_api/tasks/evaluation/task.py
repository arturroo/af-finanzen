import argparse
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import json
import base64
import os
from google.cloud import aiplatform


# We must import our custom layers so Keras knows about them when loading the model
from trainer.model import CyclicalFeature, AmountFeatures
from common.utils import df2dataset

def _parse_args():
    """Parses command-line arguments for the evaluation task."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-path', required=True, type=str, help='GCS path to the exported model directory.')
    parser.add_argument('--test-data-uri', required=True, type=str, help='GCS path to the test CSV file.')
    parser.add_argument('--metrics-path', required=True, type=str, help='Local path to write the metrics JSON file.')
    parser.add_argument('--confusion-matrix-path', required=True, type=str, help='Local path to write the confusion matrix plot.')
    parser.add_argument('--project-id', required=True, type=str)
    parser.add_argument('--region', required=True, type=str)
    return parser.parse_args()

def main():
    """Main entrypoint for the model evaluation task."""
    args = _parse_args()

    # 1. Load the exported model
    custom_objects = {
        "CyclicalFeature": CyclicalFeature,
        "AmountFeatures": AmountFeatures
    }
    
    # Dirty hack for Keras to check evaluation before model registeration
    import re
    keras_model_file_name = "model.keras"
    gs_keras_model_path = re.sub(r"(gs://.*?)/pipelines", r"\1/keras/pipelines", args.model_path.replace('/gcs/', 'gs://', 1))
    loaded_model = tf.keras.models.load_model(f"{gs_keras_model_path}/{keras_model_file_name}", custom_objects=custom_objects)
    print(f"Model loaded successfully: {loaded_model.summary()}")

    # 2. Load and prepare the test data using our consistent, imported function
    test_df = pd.read_csv(args.test_data_uri)
    test_ds = df2dataset(test_df, shuffle=False, batch_size=16)

    # 3. Generate Predictions
    y_pred_logits = loaded_model.predict(test_ds)
    y_pred = np.argmax(y_pred_logits, axis=1)
    y_true = np.concatenate([labels.numpy() for features, labels in test_ds]) # type: ignore

    # 4. Calculate and Save Metrics
    accuracy = accuracy_score(y_true, y_pred)
    f1_macro = classification_report(y_true, y_pred, output_dict=True)['macro avg']['f1-score']
    metrics_data = {
        'metrics': [
            {'name': 'accuracy-score', 'numberValue': accuracy, 'format': "PERCENTAGE"},
            {'name': 'f1-score-macro', 'numberValue': f1_macro, 'format': "PERCENTAGE"}
        ]
    }
    os.makedirs(os.path.dirname(args.metrics_path), exist_ok=True)
    with open(args.metrics_path, 'w') as f:
        json.dump(metrics_data, f)
    
    # 5. Generate Confusion Matrix Plot (as an in-memory image)
    cm = confusion_matrix(y_true, y_pred)
    class_names = sorted(test_df['i1_true_label'].unique()) 
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    
    # Save the plot to a temporary in-memory buffer
    from io import BytesIO
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    # 6. Create and Save an HTML file to display the plot
    # TOBE checked if I should use aiplatform.log_metrics() and aiplatform.log_classification_metrics() instead
    html_content = f'<html><body><img src="data:image/png;base64,{image_base64}"></body></html>'
    os.makedirs(os.path.dirname(args.confusion_matrix_path), exist_ok=True)
    with open(args.confusion_matrix_path, 'w') as f:
        f.write(html_content)



if __name__ == '__main__':
    main()
