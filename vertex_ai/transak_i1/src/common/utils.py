import pandas as pd
import numpy as np
import tensorflow as tf

def df2dataset(df: pd.DataFrame, shuffle=True, batch_size=32, labels_id_column: str = "i1_true_label_id"):
    """Converts a pandas DataFrame to a tf.data.Dataset."""
    labels_name_column = "i1_true_label"
    df = df.copy()
    if labels_id_column and labels_id_column in df.columns:
        labels = df.pop(labels_id_column).astype(np.int64)
    else:
        labels = None

    if labels_name_column in df.columns:
        df = df.drop(columns=[labels_name_column])

    if labels is not None:
        ds = tf.data.Dataset.from_tensor_slices((dict(df), labels))
    else:
        ds = tf.data.Dataset.from_tensor_slices(dict(df))

    if shuffle:
        ds = ds.shuffle(buffer_size=len(df), seed=42)
    return ds.batch(batch_size=batch_size)
