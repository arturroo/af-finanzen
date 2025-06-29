import argparse
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers

# Import our model-building logic from the same package
from .model import build_model, create_stateful_preprocessing_layers

def _parse_args():
    """Parses command-line arguments for the training task."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--train-data-path', required=True, type=str, help='GCS path to the training CSV file.')
    parser.add_argument('--val-data-path', required=True, type=str, help='GCS path to the validation CSV file.')
    parser.add_argument('--output-model-path', required=True, type=str, help='GCS path to save the exported model.')
    parser.add_argument('--num-epochs', required=True, type=int, help='Number of training epochs.')
    parser.add_argument('--learning-rate', required=True, type=float, help='Learning rate for the optimizer.')
    parser.add_argument('--batch-size', required=True, type=int, help='Training and validation batch size.')
    parser.add_argument('--num-classes', required=True, type=int, help='Number of output classes.')
    return parser.parse_args()


def main():
    """Main entrypoint for the training task."""
    args = _parse_args()
    
    # 1. Load Data
    train_df = pd.read_csv(args.train_data_path)
    val_df = pd.read_csv(args.val_data_path)
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
    
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.num_epochs,
        callbacks=[early_stopping]
    )
    
    # 5. Export Model for Deployment
    model.export(args.output_model_path)
    


if __name__ == '__main__':
    main()
