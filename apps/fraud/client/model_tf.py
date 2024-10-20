import tensorflow as tf
import time
model = None
import random as rd

def init(in_shape=10):
    global model
    inputs = tf.keras.Input(shape=(in_shape, ))
    x = tf.keras.layers.Dense(128, activation=tf.nn.relu)(inputs)
    x = tf.keras.layers.Dense(256, activation=tf.nn.relu)(x)
    x = tf.keras.layers.Dense(64, activation=tf.nn.relu)(x)
    outputs = tf.keras.layers.Dense(1, activation=tf.nn.sigmoid)(x)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile("adam", tf.keras.losses.BinaryCrossentropy(), metrics=[tf.keras.metrics.Precision()])


def fit(x, y):
    history = model.fit(x, y, epochs=1, batch_size=32)
    time.sleep(rd.randint(5,10))
    return history.history["precision"][0], history.history["loss"][0]


def evaluate(x, y):
    loss, precision = model.evaluate(x, y, 32)
    time.sleep(rd.randint(2,5))
    return precision, loss


def get_weights():
    return model.get_weights()


def set_weights(params):
    model.set_weights(params)


init()
