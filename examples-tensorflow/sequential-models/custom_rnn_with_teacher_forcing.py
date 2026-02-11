import tensorflow as tf
import numpy as np
import os
import time
import pandas as pd

# --- 1. Define Key Hyperparameters ---

# EMBEDDING_DIM: The size of the vector for each character. This learns a dense
# representation for each character, capturing semantic relationships. A larger
# dimension can capture more complex relationships but increases model size.
EMBEDDING_DIM = 256

# RNN_UNITS: The number of units in the GRU layer. This defines the model's
# "memory" or capacity to remember information from previous timesteps in a
# sequence. More units can handle more complex patterns but increase the
# risk of overfitting and slow down training.
RNN_UNITS = 1024


# --- 2. Note: the following hyperparameters are not needed / set yet.

# VOCAB_SIZE: The total number of unique words/characters/token in your vocabulary.
# This is crucial because the model can only process words it has seen during training.
# It determines the input dimension of the Embedding layer (e.g., if you have 10,000 unique words, this is 10000).
# This param is not set here but is an input for the model (and we will set this based on the sample
# text used for training)
# VOCAB_SIZE = len(vocab)

# MAX_LENGTH (int): The maximum length of the input sequences. This is only needed if using the
# Sequential API. But as we are building a sequence to sequence model (we are using teacher forcing),
# we won't do this. 
# All text inputs will be padded or truncated to this fixed length. RNNs require
# inputs to have a consistent shape, so this parameter is essential.


# --- 3. Build the Custom RNN Model using tf.keras.Model ---
# Subclassing tf.keras.Model gives full control over the model's forward pass,
# which is essential for custom training and inference logic.

class CustomRNN(tf.keras.Model):
    def __init__(self, vocab_size, embedding_dim, rnn_units):
        super().__init__()
        # --- Define the layers ---
        
        # The Embedding layer maps each character's integer ID to a dense vector.
        self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)

        # The GRU (Gated Recurrent Unit) layer processes sequences of vectors.
        # `return_sequences=True` makes it output the hidden state for *every*
        # timestep, which is necessary for predicting the next character after each input.
        # `return_state=True` allows us to manually manage the hidden state during inference.
        self.gru = tf.keras.layers.GRU(
            rnn_units,
            return_sequences=True,
            return_state=True,
            recurrent_initializer='glorot_uniform'
        )

        # The final Dense layer acts as the output. It has one neuron for each
        # character in the vocabulary and outputs raw scores (logits) for the
        # next character prediction.
        self.dense = tf.keras.layers.Dense(vocab_size)

    def call(self, inputs, states=None, return_state=False):
        """Defines the forward pass of the model."""
        # `inputs` is the sequence of character IDs.
        # Shape: (batch_size, sequence_length)
        x = inputs

        # 1. Look up the embedding for the input sequence.
        # Shape: (batch_size, sequence_length) -> (batch_size, sequence_length, embedding_dim)
        x = self.embedding(x)

        # 2. Process the sequence through the GRU.
        # We can pass an initial state, which is useful for inference.
        x, states = self.gru(x, initial_state=states)

        # 3. Apply the final dense layer to get logits for the next character prediction.
        # Shape: (batch_size, sequence_length, rnn_units) -> (batch_size, sequence_length, vocab_size)
        # Basically, for each element of the sequence, we have an array of shape (vocab_size,) where
        # each value (between 0 and 1) is the probability of having that character.
        logits = self.dense(x)

        if return_state:
            return logits, states
        else:
            return logits
        

class TextGenerator: #(tf.keras.Model):
    """Text Generator... if you inherited from tf.keras.Model, it would come with useful features 
    (e.g. allowing you to save the object using the tf.keras API as done for the CustomRNN).
    """


    def __init__(self, model, chars_to_ids, ids_to_chars):
        self.model = model
        self.chars_to_ids = chars_to_ids
        self.ids_to_chars = ids_to_chars

        # Note:
        # The original code from 
        # also has a part to prevent the sequence  "[UNK]" from being generated. As this model 
        # prdicts characters, however, this will work by masking all the [UNK] characters. However,
        # this approach does not only block [UNK]. All output sequences with '[' as first letter, 'U'
        # as second, etc will be blocked.
        # skip_ids = self.ids_from_chars(["[UNK]"])[:, None]
        # sparse_mask = tf.SparseTensor(
        #     # Put a -inf at each bad index.
        #     values=[-float("inf")] * len(skip_ids),
        #     indices=skip_ids,
        #     # Match the shape to the vocabulary
        #     dense_shape=[len(ids_from_chars.get_vocabulary())],
        # )

    
    #@tf.function
    def generate(self, start_string="ROMEO:", num_generate=1000, temperature=1.0):
        """Generates text from a starting string using the loaded model."""
        
        # Convert the start string to numbers (vectorize)
        input_ids = [self.chars_to_ids[s] for s in start_string]
        input_ids = tf.expand_dims(input_ids, 0) # convert to tensor 1 x n_chars
        # Note: you can also use the following, if you defined the map using tf.keras.layers.StringLookup
        # input_chars = tf.strings.unicode_split(inputs, "UTF-8")
        # input_ids = self.ids_from_chars(input_chars).to_tensor()


        # List to store the generated characters
        generated_text = []

        # The initial hidden state of the GRU is reset for each generation call.
        states = None

        # The temperature controls the randomness of predictions.
        # Lower temperature results in more predictable text.
        # Higher temperature results in more surprising text.
        for i in range(num_generate):
            predictions, states = self.model(input_ids, states=states, return_state=True)
            # predictions will have dimention: [1, sequence_lenght, vobac_size)]. The first dimention
            # refers to the batch, with is 1 because we input only one sequence at prediction time.
            # Remove the batch dimension.
            # Now predictions has size sequence_lenght x vobac_size
            predictions = tf.squeeze(predictions, 0)

            # Use a categorical distribution to predict the character returned by the model
            # If temperature is high, all logits will be close to zero, and similar to each other.
            # A very low temperature will max the highest score. 
            predictions = predictions / temperature

            # Apply the prediction mask: prevent "[UNK]" from being generated.
            # predicted_logits = predicted_logits + self.prediction_mask


            # Take the LAST ID only. Remember, if we input "Hell", the encoder/decoder is trained
            # to return "ello".
            predicted_id = tf.random.categorical(predictions, num_samples=1)[-1, 0].numpy()

            # Pass the predicted character as the next input to the model
            # along with the previous hidden state.
            #
            # Note: at the first loop, we will only have 1 letter (ID). However, the indo about the 
            # original prompt is in the state.
            input_ids = tf.expand_dims([predicted_id], 0)
            
            generated_text.append(self.ids_to_chars[predicted_id])

        return start_string + ''.join(generated_text)


# --- 4. Main Training Block ---
# This block will only run when the script is executed directly.
if __name__ == "__main__":
    
    # --- Load and Preprocess the Shakespeare Dataset ---
    path_to_file = tf.keras.utils.get_file(
        "shakespeare.txt",
        "https://storage.googleapis.com/download/tensorflow.org/data/shakespeare.txt",
    )
    
    text = open(path_to_file, "rb").read().decode(encoding="utf-8")
    print(f"Length of text: {len(text)} characters")

    vocab = sorted(set(text))
    VOCAB_SIZE = len(vocab)
    print(f"{VOCAB_SIZE} unique characters")

    # convert characters to ids.

    # using dict...
    chars_to_ids = {u: i for i, u in enumerate(vocab)}
    ids_to_chars = np.array(vocab)
    all_ids = np.array([chars_to_ids[c] for c in text])

    # # using tf built in 
    # ids_from_chars = tf.keras.layers.StringLookup(
    #     vocabulary=list(vocab), mask_token=None
    # )
    # chars_from_ids = tf.keras.layers.StringLookup(
    #     vocabulary=ids_from_chars.get_vocabulary(), invert=True, mask_token=None
    # )

    # --- Create the Training Dataset ---
    SEQ_LENGTH = 100
    ids_dataset = tf.data.Dataset.from_tensor_slices(all_ids)
    sequences = ids_dataset.batch(SEQ_LENGTH + 1, drop_remainder=True)

    def split_input_target(sequence):
        """Creates input -> target pairs for teacher forcing.
        
        Note 1: this function is mapped to the tf dataset. It defines the size of the tensors going 
            into the RNN. In particular, if using a model with fixed lenght input (MAX_LENGHT), we 
            would need to ensure that the lenght of these sequences matches.
        Note 2: The batch size is not determined here - the `dataset` onject will allow us to set
            it at training time.
        """
        input_text = sequence[:-1]
        target_text = sequence[1:]
        return input_text, target_text

    dataset = sequences.map(split_input_target)

    # --- Configure the Dataset for Performance ---
    BATCH_SIZE = 64
    BUFFER_SIZE = 10000

    dataset = (
        dataset.shuffle(BUFFER_SIZE)
        .batch(BATCH_SIZE, drop_remainder=True)
        .prefetch(tf.data.experimental.AUTOTUNE)
    )
    print("Training dataset configured:")
    print(dataset)

    # --- Instantiate and Compile the Model ---
    model = CustomRNN(
        vocab_size=VOCAB_SIZE,
        embedding_dim=EMBEDDING_DIM,
        rnn_units=RNN_UNITS
    )

    # Test the model. 
    # You can call the model like this. Note that, as the model has just been initialised, you want
    # to ensure you take a full batch.
    # [element] = dataset.take(BATCH_SIZE)
    # model.call(element[0])

    # The final layer of the CustomRNN is a Dense layer with no activation function. This means it 
    # outputs raw, un-normalized scores called "logits" (they can be any real number, positive or negative).
    # The `from_logits=True` flag tells the loss function to expect these raw logits. The function 
    # will then apply the softmax activation internally in a way that is numerically stable and optimized. 
    # This is the recommended best practice.
    # The Alternative (from_logits=False): If you had defined your last layer as 
    # tf.keras.layers.Dense(vocab_size, activation='softmax'), it would output probabilities directly. 
    # In that case, you would set from_logits=False. However, separating the final activation from 
    # the loss calculation is generally more stable.
    loss = tf.losses.SparseCategoricalCrossentropy(from_logits=True) 
    optimizer = tf.optimizers.Adam()
    model.compile(optimizer=optimizer, loss=loss)

    # Build the model to print the summary
    model.build(input_shape=(BATCH_SIZE, SEQ_LENGTH))
    model.summary()

    # --- Train the Model ---
    EPOCHS = 10

    # Set checkpoint files
    checkpoint_dir = "./training_checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}.weights.h5")
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_prefix, save_weights_only=True
    )

    print("\nStarting training...")
    RETRAIN_BOOL = False
    path_to_model_weights = os.path.join(checkpoint_dir, 'custom_rnn_weights.weights.h5')

    if RETRAIN_BOOL:
        history = model.fit(dataset, epochs=EPOCHS, callbacks=[checkpoint_callback])

        model.save_weights(path_to_model_weights)
        print(f"Model weights saved to {path_to_model_weights}")

        # --- Save the Training History ---
        print("\nSaving the training history...")
        history_df = pd.DataFrame(history.history)
        history_csv_path = 'training_history.csv'
        with open(history_csv_path, 'w') as f:
            history_df.to_csv(f, index=False)
        print(f"Training history saved to {history_csv_path}")

    else:

        # Before loading weights, the model must be "built".
        # Calling it on a sample input is a robust way to do this.
        # The batch size of 1 is for text generation.
        model.build(tf.TensorShape([1, None]))

        model.load_weights(path_to_model_weights)
        print("Model weights loaded successfully.")


    # --- Generate Text ---
    print("\n--- Generating Text ---")
    generator = TextGenerator(model, chars_to_ids, ids_to_chars)
    generated_text = generator.generate(start_string="JULIET:", num_generate=500)
    print(generated_text)

    # to export the generator...
    # tf.saved_model.save(generator, 'generator')