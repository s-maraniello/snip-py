import tensorflow as tf

# 1. Creating Datasets from Tensors
#    - tf.data.Dataset.from_tensor: combines the tnsor into one element.

#   - Simplest way when all data fits in memory
dataset = tf.data.Dataset.from_tensor_slices([1, 2, 3, 4, 5])
#   - For more complex data
dataset = tf.data.Dataset.from_tensor_slices(
    (tf.constant([1, 2, 3]), tf.constant(['a', 'b', 'c']))
)

# 2. Creating Datasets from Files
#   - For text data (e.g., lines in a file)
dataset3 = tf.data.TextLineDataset("my_file.txt")
#   - For TFRecord files (TensorFlow's preferred format for efficiency)
dataset4 = tf.data.TFRecordDataset("my_data.tfrecord")
#   - Other options available:
#      - FixedLengthRecordDataset
#      - Build your custom loader.

# 3. Transforming Datasets
#   - Use map and filter.
#   - You can chain multiple transformations together
dataset = dataset.map(lambda record: parse(record)).map(lambda x: x * 2).filter(lambda x: x < 8)


# 4. Configure how data is fed into a model
# Note: shuffle is for training only
batch_size, epochs = 10, 10
dataset = dataset.\
    shuffle(buffer_size=10).\
    repeat(epochs).\
    batch(batch_size,drop_remainder=True)

# You can iterate through elements of the dataset.
for element in dataset:
    print(element.numpy())  # Use .numpy() to get the value

#   - `prefetch()`: Prefetch elements to improve performance
dataset10 = dataset1.prefetch(tf.data.AUTOTUNE)

# Example (replace with your actual model and data)
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(10, input_shape=(1,), activation='relu'),
    tf.keras.layers.Dense(1)
])

model.compile(optimizer='adam', loss='mse')

# Assuming `dataset1` is suitable for your model's input
model.fit(dataset1.batch(2), epochs=5)