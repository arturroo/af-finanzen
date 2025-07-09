import numpy as np
import tensorflow as tf
from tensorflow.keras import layers # type: ignore


@tf.keras.utils.register_keras_serializable()
class CyclicalFeature(layers.Layer):
    """
    A custom Keras layer to perform sin/cos cyclical transformation.
    Outputs a tensor with two features: [sin_value, cos_value].
    """
    def __init__(self, period, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        # We store the period as part of the layer's configuration.
        self.period = float(period)

    def call(self, inputs):
        """Feature transformation logic."""
        # We handle the logic for 0-based weekdays vs. 1-based days/months for sin/cos to catch the cyclical nature. If not then 1 is faraway from 0, which is far from 12 or 31
        adjusted_inputs = inputs if self.period == 7.0 else inputs - 1
        
        # Calculate sin and cos transformations
        sin_transformed = tf.math.sin(2 * np.pi * adjusted_inputs / self.period)
        cos_transformed = tf.math.cos(2 * np.pi * adjusted_inputs / self.period)
        
        # Concatenate the results into a single output tensor of shape (None, 2)
        return layers.concatenate([sin_transformed, cos_transformed], axis=-1)

    def get_config(self):
        """Save and load the layer correctly."""
        config = super().get_config()
        config.update({"period": self.period})
        return config
    

@tf.keras.utils.register_keras_serializable()
class AmountFeatures(layers.Layer):
    """
    A custom layer to create log and sign features from an amount input.
    Outputs a tensor: [log1p_abs_amount, sign_flag].
    """
    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

    def call(self, inputs):
        """The feature transformation logic."""
        # 1. The robust log transform
        log1p_abs_amount = tf.math.log1p(tf.abs(inputs))
        
        # 2. The binary sign feature
        sign_flag = tf.cast(inputs >= 0, dtype=tf.float32)

        # 3. Concatenate the results and return them as a single tensor
        return layers.concatenate([log1p_abs_amount, sign_flag], axis=-1)

    def get_config(self):
        # This layer has no custom arguments in __init__, so we just call the parent
        config = super().get_config()
        return config

def create_stateful_preprocessing_layers(hyperparams:dict) -> dict:
    """Instantiates all the stateful preprocessing layers that need to be adapted.
    Args:
        hyperparams: A dictionary of hyperparameters.
    Returns:
        A dictionary of instantiated layer objects.
    """
    preprocessing_layers = {
        'description_text_vectorizer': layers.TextVectorization(
            max_tokens=hyperparams['desc_vocab_size'],
            standardize="lower_and_strip_punctuation",
            split="whitespace",
            ngrams=(1,3),
            output_mode="int",
            name="description_text_vectorizerization"),
        'type_lookup': layers.StringLookup(num_oov_indices=2, output_mode="int"),
        'currency_lookup': layers.StringLookup(num_oov_indices=1, output_mode="int"),
        'normalizer': layers.Normalization()
    }
    print("--- Preprocessing layers created successfully ---")
    return preprocessing_layers

# main model building function
def build_model(preprocessing_layers: dict, hyperparams:dict) -> tf.keras.Model:
    """Builds the complete Wide & Deep Keras model.
    Args:
        hyperparameters: A dictionary of hyperparameters.    
    Returns:
        A compiled Keras model.
    """
    # --- Input Layers ---
    inputs = {
        'started_month': tf.keras.Input(shape=(1,), name="started_month", dtype="float32"),
        'started_day': tf.keras.Input(shape=(1,), name="started_day", dtype="float32"),
        'started_weekday': tf.keras.Input(shape=(1,), name="started_weekday", dtype="float32"),
        'first_started_month': tf.keras.Input(shape=(1,), name="first_started_month", dtype="float32"),
        'first_started_day': tf.keras.Input(shape=(1,), name="first_started_day", dtype="float32"),
        'first_started_weekday': tf.keras.Input(shape=(1,), name="first_started_weekday", dtype="float32"),
        'started_year': tf.keras.Input(shape=(1,), name="started_year", dtype="float32"),
        'first_started_year': tf.keras.Input(shape=(1,), name="first_started_year", dtype="float32"),
        'amount': tf.keras.Input(shape=(1,), name="amount", dtype="float32"),
        'type': tf.keras.Input(shape=(1,), name="type", dtype="string"),
        'currency': tf.keras.Input(shape=(1,), name="currency", dtype="string"),
        'description': tf.keras.Input(shape=(1,), name="description", dtype="string"),
    }

    # --- Wide Path ---
    description_hashed = layers.Hashing(num_bins=hyperparams['desc_hash_bins'])(inputs['description'])
    type_lookup = preprocessing_layers['type_lookup'](inputs['type'])
    type_desc_cross = layers.HashedCrossing(num_bins=hyperparams['cross_bins'])([description_hashed, type_lookup])
    wide_one_hot = layers.CategoryEncoding(num_tokens=hyperparams['cross_bins'] + 1, output_mode='one_hot')(type_desc_cross)
    wide_logits = layers.Dense(units=hyperparams['num_classes'], activation=None)(wide_one_hot)

    # --- Deep Path ---
    # Numerical features
    started_month = CyclicalFeature(period=12)(inputs['started_month'])
    started_day = CyclicalFeature(period=31)(inputs['started_day'])
    started_weekday = CyclicalFeature(period=7)(inputs['started_weekday'])
    first_started_month = CyclicalFeature(period=12)(inputs['first_started_month'])
    first_started_day = CyclicalFeature(period=31)(inputs['first_started_day'])
    first_started_weekday = CyclicalFeature(period=7)(inputs['first_started_weekday'])

    amount_features = AmountFeatures(name='amount_features')(inputs['amount'])

    # Concatenate numeric features for normalization
    features_to_normalize = layers.concatenate([
        inputs['started_year'],
        inputs['first_started_year'],
        amount_features
    ])
    scaled_numeric_features = preprocessing_layers['normalizer'](features_to_normalize)

    # Concatenate untouched numeric and cyclic features
    all_numeric_features = layers.concatenate([
        scaled_numeric_features,
        started_month,
        started_day,
        started_weekday,
        first_started_month,
        first_started_day,
        first_started_weekday
    ])

    # Text features
    description_text_vectorizer = preprocessing_layers['description_text_vectorizer'](inputs['description'])
    description_embedding = layers.Embedding(
        input_dim=preprocessing_layers['description_text_vectorizer'].vocabulary_size(),
        output_dim=hyperparams['desc_embedding_dim'],
        mask_zero=True
    )(description_text_vectorizer)
    description_embedding_reduced = layers.GlobalAveragePooling1D()(description_embedding)

    # Categorical features
    type_embedding = layers.Embedding(
        input_dim=preprocessing_layers['type_lookup'].vocabulary_size(),
        output_dim=hyperparams['type_embedding_dim']
    )(type_lookup)
    type_embedding_flat = layers.Flatten()(type_embedding)

    currency_lookup = preprocessing_layers['currency_lookup'](inputs['currency'])
    currency_embedding = layers.Embedding(
        input_dim=preprocessing_layers['currency_lookup'].vocabulary_size(),
        output_dim=hyperparams['currency_embedding_dim']
    )(currency_lookup)
    currency_embedding_flat = layers.Flatten()(currency_embedding)

    # Combine all deep features
    deep_features_head = layers.concatenate([
        all_numeric_features,
        description_embedding_reduced,
        type_embedding_flat,
        currency_embedding_flat
    ])

    # DNN head
    h1 = layers.Dense(units=64, activation="relu")(deep_features_head)
    drop1 = layers.Dropout(rate=0.2)(h1)
    h2 = layers.Dense(units=32, activation="relu")(drop1)
    deep_logits = layers.Dense(units=hyperparams['num_classes'], activation=None)(h2)

    # Combine Heads
    combined_logits = layers.Add()([wide_logits, deep_logits])
    # final_output = layers.Activation("softmax")(combined_logits)

    # Final Model
    model = tf.keras.Model(inputs=inputs, outputs=combined_logits)

    # Compile Model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=hyperparams['learning_rate']),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), # from_logits=True is important for numerical stability, that's why we combined_logits instead final_output
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")]
    )

    return model