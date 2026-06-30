import os
import random

import numpy as np
import scipy.io as scio
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras.layers import (
    Input,
    Conv2D,
    MaxPooling2D,
    Dense,
    Dropout,
    Flatten,
    GRU,
    TimeDistributed,
)
from tensorflow.keras.models import Model, load_model

from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split


SEED = 1

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)


# Parameters
use_existing_model = False
fraction_for_test = 0.1
data_dir = 'BVP/'
ALL_MOTION = [1, 2, 3, 4, 5, 6]
N_MOTION = len(ALL_MOTION)
T_MAX = 0
n_epochs = 30
f_dropout_ratio = 0.5
n_gru_hidden_units = 128
n_batch_size = 32
f_learning_rate = 0.001


def normalize_data(data_1):
    # data(ndarray)=>data_norm(ndarray): [20,20,T]=>[20,20,T]
    data_1_max = np.concatenate((data_1.max(axis=0), data_1.max(axis=1)), axis=0).max(axis=0)
    data_1_min = np.concatenate((data_1.min(axis=0), data_1.min(axis=1)), axis=0).min(axis=0)
    if (len(np.where((data_1_max - data_1_min) == 0)[0]) > 0):
        return data_1
    data_1_max_rep = np.tile(data_1_max, (data_1.shape[0], data_1.shape[1], 1))
    data_1_min_rep = np.tile(data_1_min, (data_1.shape[0], data_1.shape[1], 1))
    data_1_norm = (data_1 - data_1_min_rep) / (data_1_max_rep - data_1_min_rep)
    return data_1_norm


def zero_padding(data, t_max):
    # data(list)=>data_pad(ndarray): [20,20,T1/T2/...]=>[20,20,T_MAX]
    data_pad = []
    for i in range(len(data)):
        t = np.array(data[i]).shape[2]
        data_pad.append(
            np.pad(
                data[i],
                ((0, 0), (0, 0), (t_max - t, 0)),
                mode="constant",
            )
        )
    return np.asarray(data_pad, dtype=np.float32)


def load_data(path_to_data, motion_sel):
    global T_MAX
    data = []
    label = []
    n_skipped = 0
    for data_root, data_dirs, data_files in os.walk(path_to_data):
        for data_file_name in data_files:
            if not data_file_name.endswith('.mat'):
                continue

            file_path = os.path.join(data_root, data_file_name)
            try:
                mat = scio.loadmat(file_path)['velocity_spectrum_ro']
                label_1 = int(data_file_name.split('-')[1])

                # Select Motion
                if label_1 not in motion_sel:
                    continue

                # Normalization
                data_normed_1 = normalize_data(mat)

                # Update T_MAX
                if T_MAX < data_normed_1.shape[2]:
                    T_MAX = data_normed_1.shape[2]
            except Exception as exc:
                n_skipped += 1
                print(f"Skipping {file_path}: {exc}")
                continue

            # Save List -- the actual fix: append label_1, not the whole list
            data.append(data_normed_1.astype(np.float32))
            label.append(label_1)

    if n_skipped:
        print(f"Skipped {n_skipped} files due to parse errors.")
    if not data:
        raise RuntimeError(
            f"No matching .mat files found under '{path_to_data}'. "
            "Check that filenames follow 'name-motion-location-orientation-rep...mat' "
            "and contain a 'velocity_spectrum_ro' variable."
        )

    # Zero-padding (now that T_MAX is final)
    data = zero_padding(data, T_MAX)

    # Swap axes
    data = np.swapaxes(np.swapaxes(data, 1, 3), 2, 3)   # [N,20,20,T_MAX]=>[N,T_MAX,20,20]
    data = np.expand_dims(data, axis=-1)                # [N,T_MAX,20,20]=>[N,T_MAX,20,20,1]

    label = np.array(label, dtype=np.int32)

    # data(ndarray): [N,T_MAX,20,20,1], label(ndarray): [N,]
    return data, label


def assemble_model(input_shape, n_class):
    model_input = Input(shape=input_shape, dtype='float32', name='name_model_input')  # (@,T_MAX,20,20,1)

    # Feature extraction part
    x = TimeDistributed(Conv2D(16, kernel_size=(5, 5), activation='relu', data_format='channels_last'))(model_input)
    x = TimeDistributed(MaxPooling2D(pool_size=(2, 2)))(x)
    x = TimeDistributed(Flatten())(x)
    x = TimeDistributed(Dense(64, activation='relu'))(x)
    x = TimeDistributed(Dropout(f_dropout_ratio))(x)
    x = TimeDistributed(Dense(64, activation='relu'))(x)
    x = GRU(n_gru_hidden_units, return_sequences=False)(x)
    x = Dropout(f_dropout_ratio)(x)
    model_output = Dense(n_class, activation='softmax', name='name_model_output')(x)

    model = Model(inputs=model_input, outputs=model_output)
    model.compile(
        optimizer=keras.optimizers.RMSprop(learning_rate=f_learning_rate),
        loss='categorical_crossentropy',
        metrics=['accuracy'],
    )
    return model


# ==============================================================
# Let's BEGIN >>>>
print("TensorFlow:", tf.__version__)

gpus = tf.config.list_physical_devices("GPU")
print("GPUs:", gpus)

# Load data
data, label = load_data(data_dir, ALL_MOTION)

print(f"Loaded {len(label)} samples")
print(data.shape)

data_train, data_test, label_train, label_test = train_test_split(
    data,
    label,
    test_size=fraction_for_test,
    random_state=SEED,
    shuffle=True,
    stratify=label,  # keeps class balance consistent across the split
)

label_train_oh = keras.utils.to_categorical(label_train - 1, num_classes=N_MOTION)

if use_existing_model:
    model = load_model("model_widar3.keras")
else:
    model = assemble_model(
        input_shape=(T_MAX, 20, 20, 1),
        n_class=N_MOTION,
    )

    model.summary()

    history = model.fit(
        data_train,
        label_train_oh,
        batch_size=n_batch_size,
        epochs=n_epochs,
        validation_split=0.1,
        shuffle=True,
        verbose=1,
    )

    model.save("model_widar3.keras")

pred = model.predict(data_test, verbose=0)
pred = np.argmax(pred, axis=1) + 1

cm = confusion_matrix(label_test, pred)
print(cm)

cm = cm.astype(np.float32)
cm /= cm.sum(axis=1, keepdims=True)
print(np.round(cm, 2))

accuracy = np.mean(pred == label_test)
print("Accuracy:", accuracy)