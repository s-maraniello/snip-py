import tensorflow as tf
import pandas as pd
import numpy as np

# --- 1. Create a Sample Dataset ---
# We'll use a dictionary, similar to how you would feed data to feature columns.
# This simulates reading from a Pandas DataFrame or a tf.data.Dataset.
data = {
    'price': np.array([15.0, 22.0, 31.0, 45.0, 50.0]),
    'product_type': ['shirt', 'jeans', 'shirt', 'shoes', 'jeans'],
    'brand': ['brand_a', 'brand_b', 'brand_c', 'brand_b', 'brand_a'],
    'age_group': ['adult', 'teen', 'adult', 'adult', 'teen'],
    'clicks': np.array([102, 345, 189, 450, 210])
}

# Convert the dictionary to a TensorFlow Dataset
# In a real-world scenario, you might use tf.data.experimental.make_csv_dataset
# or tf.data.Dataset.from_tensor_slices.
dataset = tf.data.Dataset.from_tensor_slices(data)

# --- 2. Define Feature Preprocessing using Keras Layers ---

# Create separate input layers for each feature. This is the standard Keras approach.
inputs = {
    'price': tf.keras.Input(shape=(1,), name='price', dtype=tf.float32),
    'product_type': tf.keras.Input(shape=(1,), name='product_type', dtype=tf.string),
    'brand': tf.keras.Input(shape=(1,), name='brand', dtype=tf.string),
    'age_group': tf.keras.Input(shape=(1,), name='age_group', dtype=tf.string),
    'clicks': tf.keras.Input(shape=(1,), name='clicks', dtype=tf.int64),
}

# --- A. Numeric Column (Normalization) ---
# Replaces: tf.feature_column.numeric_column
price_input = inputs['price']
normalized_price = tf.keras.layers.Normalization(axis=None)(price_input)

# --- B. Categorical Vocabulary Column (One-Hot Encoded) ---
# Replaces: tf.feature_column.indicator_column(tf.feature_column.categorical_column_with_vocabulary_list)
product_type_input = inputs['product_type']
product_vocab = ['shirt', 'jeans', 'shoes']
# First, map strings to integer indices
product_lookup = tf.keras.layers.StringLookup(vocabulary=product_vocab, output_mode='int')(product_type_input)
# Then, one-hot encode the indices
one_hot_product = tf.keras.layers.CategoryEncoding(num_tokens=len(product_vocab) + 1, output_mode='one_hot')(product_lookup)


# --- C. Categorical Hashed Column (Hashed then Embedded) ---
# Replaces: tf.feature_column.embedding_column(tf.feature_column.categorical_column_with_hash_bucket)
brand_input = inputs['brand']
hash_bins = 10  # Number of hash buckets
embedding_dim = 4 # Dimension of the embedding vector
# Hash the string input into integer bins
hashed_brand = tf.keras.layers.Hashing(num_bins=hash_bins)(brand_input)
# Turn the hashed integer into a dense embedding vector
embedded_brand = tf.keras.layers.Embedding(input_dim=hash_bins, output_dim=embedding_dim)(hashed_brand)
# Flatten the embedding for concatenation with other features
embedded_brand_flat = tf.keras.layers.Flatten()(embedded_brand)


# --- D. Bucketized Column ---
# Replaces: tf.feature_column.bucketized_column
clicks_input = inputs['clicks']
click_boundaries = [100, 200, 300, 400] # Define bucket boundaries
# Discretize the continuous 'clicks' feature into buckets
bucketized_clicks = tf.keras.layers.Discretization(bin_boundaries=click_boundaries)(clicks_input)


# --- E. Crossed Column ---
# Replaces: tf.feature_column.crossed_column
age_group_input = inputs['age_group']
age_group_vocab = ['teen', 'adult', 'senior']
# First, lookup the string to create integer categories for crossing
age_group_lookup = tf.keras.layers.StringLookup(vocabulary=age_group_vocab, output_mode='int')(age_group_input)
# Cross the two categorical features
# Note: HashedCrossing is used as the direct replacement.
crossed_feature = tf.keras.layers.HashedCrossing(num_bins=15)([age_group_lookup, product_lookup])
# Typically, a crossed feature is then embedded
embedded_crossed = tf.keras.layers.Embedding(input_dim=15, output_dim=5)(crossed_feature)
embedded_crossed_flat = tf.keras.layers.Flatten()(embedded_crossed)


# --- 3. Concatenate Processed Features and Build the Model ---

# Concatenate all our processed features into a single vector
all_features = tf.keras.layers.Concatenate()(
    [normalized_price,
     one_hot_product,
     embedded_brand_flat,
     bucketized_clicks,
     embedded_crossed_flat]
)

# Create a simple Functional API model
preprocessing_layer = tf.keras.Model(inputs=inputs, outputs=all_features)

# You can now use this preprocessing_layer as the first layer in a larger model
# For demonstration, we'll create a simple classification model
model_input = preprocessing_layer.input
model_output = tf.keras.layers.Dense(32, activation='relu')(preprocessing_layer(model_input))
model_output = tf.keras.layers.Dense(1, activation='sigmoid')(model_output) # e.g., predict purchase probability

model = tf.keras.Model(inputs=model_input, outputs=model_output)

# Compile the model
model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])

# Print the model summary to see the architecture
print("--- Model Summary ---")
model.summary()


# --- 4. Use the Model ---
# To use the model, you feed it the original, unprocessed dictionary of data.
# The preprocessing happens inside the model.

# Let's create some dummy labels for a runnable example
dummy_labels = np.array([1, 0, 1, 1, 0])
training_dataset = dataset.batch(2).map(lambda x: (x, dummy_labels[:len(x['price'])]))

# You would typically train the model like this:
# print("\n--- Model Training (Example) ---")
# model.fit(training_dataset, epochs=1)

# Let's just predict on a batch to show it works
print("\n--- Model Prediction on a Sample Batch ---")
sample_batch = next(iter(dataset.batch(5)))
prediction = model.predict(sample_batch)
print(prediction)