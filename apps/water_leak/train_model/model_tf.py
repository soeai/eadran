import tensorflow as tf
from tensorflow.keras import layers, models

model = None


class SelfAttention(layers.Layer):
    def __init__(self):
        super(SelfAttention, self).__init__()
        self.W_v = None
        self.W_k = None
        self.W_q = None

    def build(self, input_shape):
        # Define weights for query, key, and value
        self.W_q = self.add_weight(shape=(input_shape[-1], input_shape[-1]), initializer='random_normal',
                                   trainable=True)
        self.W_k = self.add_weight(shape=(input_shape[-1], input_shape[-1]), initializer='random_normal',
                                   trainable=True)
        self.W_v = self.add_weight(shape=(input_shape[-1], input_shape[-1]), initializer='random_normal',
                                   trainable=True)

    def call(self, inputs):
        Q = tf.matmul(inputs, self.W_q)  # Query
        K = tf.matmul(inputs, self.W_k)  # Key
        V = tf.matmul(inputs, self.W_v)  # Value

        # Calculate attention scores
        attention_scores = tf.matmul(Q, K, transpose_b=True) / tf.math.sqrt(tf.cast(inputs.shape[-1], tf.float32))
        attention_weights = tf.nn.softmax(attention_scores, axis=-1)

        # Compute the context vector
        context_vector = tf.matmul(attention_weights, V)
        return context_vector


def create_model(input_shape):
    global model
    inputs = layers.Input(shape=input_shape)

    # Add self-attention layer
    x = SelfAttention()(inputs)

    # Flatten and add dense layers
    x = layers.Flatten()(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dense(32, activation='relu')(x)
    outputs = layers.Dense(1, activation='sigmoid')(x)  # Binary classification

    model = models.Model(inputs, outputs)
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=[tf.keras.metrics.Precision()])


def fit(x, y):
    history = model.fit(x, y, epochs=1, batch_size=32)
    return history.history["precision"][0], history.history["loss"][0]


def evaluate(x, y):
    loss, precision = model.evaluate(x, y, 32)
    return precision, loss


def get_weights():
    return model.get_weights()


def set_weights(params):
    model.set_weights(params)


create_model((10, 100))  # Example input shape: (timesteps, features)
