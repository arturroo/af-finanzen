import pandas as pd
import numpy as np
import tensorflow as tf

def df2dataset(df: pd.DataFrame, shuffle=True, batch_size=32):
    """Converts a pandas DataFrame to a tf.data.Dataset."""
    df = df.copy()
    labels = df.pop("i1_true_label_id").astype(np.int64)
    if "i1_true_label" in df.columns:
        df = df.drop(columns=["i1_true_label"])
    ds = tf.data.Dataset.from_tensor_slices((dict(df), labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(df), seed=42)
    return ds.batch(batch_size=batch_size)
