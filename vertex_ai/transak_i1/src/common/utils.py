import pandas as pd
import numpy as np
import tensorflow as tf

def df2dataset(df: pd.DataFrame, shuffle=True, batch_size=32, mode: str = 'train'):
    """
    Converts a pandas DataFrame to a tf.data.Dataset, handling different modes.

    Args:
        df (pd.DataFrame): The input DataFrame.
        shuffle (bool): Whether to shuffle the dataset.
        batch_size (int): The batch size for the dataset.
        mode (str): 'train' to return (features, labels), 'inference' for features only.
    """
    df = df.copy()
    label_column = 'i1_true_label_id'

    # Always drop the transaction ID and the human-readable label name if they exist
    if "tid" in df.columns:
        df = df.drop(columns=["tid"])
    if "i1_true_label" in df.columns:
        df = df.drop(columns=["i1_true_label"])

    if mode == 'inference':
        # For inference, we don't need the label. Drop it if it exists.
        if label_column in df.columns:
            df = df.drop(columns=[label_column])
        for col in df.select_dtypes(include=[np.number]).columns:
            df[col] = df[col].astype(np.float32)
        ds = tf.data.Dataset.from_tensor_slices(dict(df))
    elif mode == 'train':
        # For training, we need the label. Pop it from the dataframe.
        if label_column not in df.columns:
            raise ValueError(f"Label column '{label_column}' not found in DataFrame for training mode.")
        labels = df.pop(label_column).astype(np.int64)
        for col in df.select_dtypes(include=[np.number]).columns:
            df[col] = df[col].astype(np.float32)
        ds = tf.data.Dataset.from_tensor_slices((dict(df), labels))
    else:
        raise ValueError(f"Invalid mode: {mode}. Choose 'train' or 'inference'.")

    # Add the missing dimension to each feature tensor
    # This is necessary for the model to accept the input shape correctly (Keras don't care at trein, TF serving cares)
    def reshape_features(features, *label):
        for key in features.keys():
            # Reshape each scalar feature tensor to have a shape of [1]
            features[key] = tf.expand_dims(features[key], axis=-1)
        if label:
            return (features, *label)
        return features

    ds = ds.map(reshape_features, num_parallel_calls=tf.data.AUTOTUNE)

    if shuffle:
        ds = ds.shuffle(buffer_size=len(df), seed=42)
        
    return ds.batch(batch_size=batch_size).prefetch(tf.data.AUTOTUNE)
