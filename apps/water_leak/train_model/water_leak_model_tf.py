import random
import time
import tensorflow as tf
from tensorflow.keras import layers, models
import os

tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)
os.environ["OMP_NUM_THREADS"] = "1"

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


def create_model(input_shape, num_class):
    global model
    inputs = layers.Input(shape=(input_shape,))

    # Add self-attention layer
    x = SelfAttention()(inputs)

    # Flatten and add dense layers
    x = layers.Flatten()(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.Dense(128, activation='relu')(x)
    outputs = layers.Dense(num_class, activation='softmax')(x)

    model = models.Model(inputs, outputs)
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=["accuracy"])


def fit(x, y, epoch=10, batch_size=128):
    history = model.fit(x, y, epochs=epoch, batch_size=batch_size)
    time.sleep(random.randint(10, 15))
    return history.history["accuracy"][-1], history.history["loss"][-1]


def evaluate(x, y, batch_size=128):
    loss, acc = model.evaluate(x, y, batch_size)
    return acc, loss


def get_weights():
    return model.get_weights()


def set_weights(params):
    model.set_weights(params)


create_model(99, 5)  # (features_size, num_class)
