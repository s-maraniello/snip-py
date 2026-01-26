# Copyright 2024 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This script trains a text classification model using a pre-trained BERT model
from TensorFlow Hub. It is a Python script version of the original
Google Cloud ASL ML Immersion notebook classify_text_with_bert.ipynb

https://github.com/GoogleCloudPlatform/asl-ml-immersion/blob/master/notebooks/text_models/solutions/classify_text_with_bert.ipynb
"""

# --- 0. Preamble and Imports ---
# This script requires the following packages. You can install them with:
# pip install "tensorflow-text==2.16.*" "tf-models-official==2.16.*"

import shutil
from pathlib import Path
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text         # Registers the ops
from official.nlp import optimization  # to create AdamW optimizer

tf.get_logger().setLevel('ERROR')


# --- 2. Model Building ---

def build_classifier_model(tfhub_handle_encoder, tfhub_handle_preprocess):
    """
    Builds a Keras Sequential model with a BERT encoder.

    Args:
      tfhub_handle_encoder: URL handle for the pre-trained BERT encoder.
      tfhub_handle_preprocess: URL handle for the BERT text preprocessor.

    Returns:
      A compiled Keras model.
    """
    text_input = tf.keras.layers.Input(shape=(), dtype=tf.string, name='text')
    preprocessing_layer = hub.KerasLayer(tfhub_handle_preprocess, name='preprocessing')
    encoder_inputs = preprocessing_layer(text_input)
    encoder = hub.KerasLayer(tfhub_handle_encoder, trainable=True, name='BERT_encoder')
    outputs = encoder(encoder_inputs)
    net = outputs['pooled_output']
    net = tf.keras.layers.Dropout(0.1)(net)
    net = tf.keras.layers.Dense(1, activation=None, name='classifier')(net)
    
    return tf.keras.Model(text_input, net)


# --- 3. Main Execution Block ---

if __name__ == "__main__":

    # --- Setup BERT Model Handles ---
    # This script uses a smaller, faster BERT model for demonstration.
    # For higher accuracy, you could use a larger model.
    bert_model_name = 'small_bert/bert_en_uncased_L-4_H-512_A-8'
    
    tfhub_handle_encoder = f'https://tfhub.dev/tensorflow/{bert_model_name}/1'
    tfhub_handle_preprocess = f'https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3'

    print(f"BERT model selected         : {tfhub_handle_encoder}")
    print(f"Preprocessing model selected: {tfhub_handle_preprocess}")


    # --- Load Data ---
    print("\nLoading IMDB dataset...")
    # train_ds, val_ds, test_ds, class_names = download_and_prepare_dataset()

    """Downloads the IMDB dataset, extracts it, and creates a tf.data.Dataset."""
    url = 'https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz'
    

    # Download and extract the dataset. 
    # By default the file at the url `origin` is downloaded to the cache_dir `~/.keras`, placed in 
    # the cache_subdir `datasets`, and given the filename `fname`. The final location of a file
    # `example.txt` would therefore be `~/.keras/datasets/example.txt`.
    # we render these variable explicit here.
    cache_dir, cache_subdir, fname = '.keras', 'datasets', 'aclImdb_v1.tar.gz'



    dataset_path_str = tf.keras.utils.get_file(fname, url, untar=True, 
                                               cache_dir=cache_dir, cache_subdir=cache_subdir)
    # dataset_path = Path(dataset_path_str)
    dataset_dir = dataset_path.parent / 'aclImdb'
    train_dir = dataset_dir / 'train'
    test_dir = dataset_dir / 'test'

    1/0
    
    # The 'unsup' directory contains unlabeled reviews, which we don't need.
    # We remove it to prevent it from being loaded.
    remove_dir = train_dir / 'unsup'
    shutil.rmtree(remove_dir)

    # Create the main training dataset from the text files
    # The directory structure is used to infer labels (pos/neg).
    AUTOTUNE = tf.data.AUTOTUNE
    batch_size = 32
    seed = 42

    raw_train_ds = tf.keras.utils.text_dataset_from_directory(
        train_dir,
        batch_size=batch_size,
        validation_split=0.2,
        subset='training',
        seed=seed
    )
    
    class_names = raw_train_ds.class_names
    train_ds = raw_train_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # Create the validation dataset
    val_ds = tf.keras.utils.text_dataset_from_directory(
        train_dir,
        batch_size=batch_size,
        validation_split=0.2,
        subset='validation',
        seed=seed
    ).cache().prefetch(buffer_size=AUTOTUNE)

    # Create the test dataset
    test_ds = tf.keras.utils.text_dataset_from_directory(
        test_dir,
        batch_size=batch_size
    ).cache().prefetch(buffer_size=AUTOTUNE)
    
    # return train_ds, val_ds, test_ds, class_names

    
    
    
    print("Dataset loaded successfully.")

    # --- Build and Compile the Model ---
    print("\nBuilding the classifier model...")
    classifier_model = build_classifier_model(tfhub_handle_encoder, tfhub_handle_preprocess)
    
    loss = tf.keras.losses.BinaryCrossentropy(from_logits=True)
    metrics = tf.metrics.BinaryAccuracy()
    
    epochs = 5
    steps_per_epoch = tf.data.experimental.cardinality(train_ds).numpy()
    num_train_steps = steps_per_epoch * epochs
    num_warmup_steps = int(0.1 * num_train_steps)

    optimizer = optimization.create_optimizer(
        init_lr=3e-5,
        num_train_steps=num_train_steps,
        num_warmup_steps=num_warmup_steps,
        optimizer_type='adamw'
    )
    
    classifier_model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
    print("Model built and compiled successfully.")
    classifier_model.summary()

    # --- Train the Model ---
    print(f"\nTraining model for {epochs} epochs...")
    history = classifier_model.fit(
        x=train_ds,
        validation_data=val_ds,
        epochs=epochs
    )
    print("Training finished.")
    
    # --- Evaluate the Model ---
    print("\nEvaluating model on the test set...")
    loss, accuracy = classifier_model.evaluate(test_ds)
    print(f"Loss: {loss}")
    print(f"Accuracy: {accuracy}")

    # --- Demonstrate Prediction ---
    print("\nRunning a prediction on new examples...")
    dataset_name = 'imdb'
    saved_model_path = Path(f'./{dataset_name.replace("/", "_")}_bert')

    # Create the directory for the saved model if it doesn't already exist.
    # The exist_ok=True argument prevents an error if the directory is already there.
    saved_model_path.mkdir(parents=True, exist_ok=True)
    
    classifier_model.save(saved_model_path, include_optimizer=False)

    reloaded_model = tf.saved_model.load(saved_model_path)
    
    examples = [
        'This is a fantastic movie!',
        'The film was a complete waste of time.',
        'I cannot recommend this enough, it was brilliant.'
    ]
    
    results = tf.sigmoid(reloaded_model(tf.constant(examples)))

    print("Prediction results (0=Negative, 1=Positive):")
    for i, text in enumerate(examples):
        print(f'Text: {text}')
        print(f'Score: {results[i][0]:.4f}')
        print(f'Prediction: {"Positive" if results[i][0] > 0.5 else "Negative"}')
        print('---')



