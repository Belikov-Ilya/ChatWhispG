import json
import os
import hashlib
import asyncio
import re
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Embedding, LSTM
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import logging

logging.basicConfig(level=logging.INFO)

# Constants for tokenization and model
MAX_NUM_WORDS = 10000
MAX_SEQUENCE_LENGTH = 100
EMBEDDING_DIM = 128

tokenizer = Tokenizer(num_words=MAX_NUM_WORDS, oov_token="<UNK>")
model = None

# Save and load functions for tokenizer
def save_tokenizer():
    with open("models/tokenizer.json", "w", encoding="utf-8") as f:
        json.dump(tokenizer.to_json(), f)


def load_tokenizer():
    global tokenizer
    with open("models/tokenizer.json", "r", encoding="utf-8") as f:
        tokenizer_config = json.load(f)
    tokenizer = Tokenizer(num_words=MAX_NUM_WORDS, oov_token="<UNK>")
    tokenizer.word_index = json.loads(tokenizer_config).get("word_index", {})


# Model training function
async def train_model():
    global model, tokenizer

    os.makedirs("models", exist_ok=True)

    logging.info("Loading training data...")
    neutral_data = load_dataset("dataset/ru/neutral.json", 0)
    ad_data = load_dataset("dataset/ru/ads.json", 2)
    profanity_data = load_dataset("dataset/ru/profanity.json", 1)

    texts, labels = (
        neutral_data[0] + ad_data[0] + profanity_data[0],
        neutral_data[1] + ad_data[1] + profanity_data[1],
    )

    tokenizer.fit_on_texts(texts)
    save_tokenizer()

    sequences = tokenizer.texts_to_sequences(texts)
    X = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)
    y = np.array(labels)

    indices = np.arange(len(X))
    np.random.shuffle(indices)
    X = X[indices]
    y = y[indices]

    split_at = int(len(X) * 0.8)
    X_train, X_test = X[:split_at], X[split_at:]
    y_train, y_test = y[:split_at], y[split_at:]

    model = Sequential([
        Embedding(MAX_NUM_WORDS, EMBEDDING_DIM),
        LSTM(128, return_sequences=True),
        Dropout(0.2),
        LSTM(64),
        Dropout(0.2),
        Dense(3, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    logging.info("Training model...")
    model.fit(X_train, y_train, batch_size=32, epochs=10, validation_split=0.1, verbose=1)

    y_pred = np.argmax(model.predict(X_test), axis=-1)
    accuracy = np.mean(y_pred == y_test)
    logging.info(f"Model accuracy: {accuracy:.2%}")

    model.save("models/profanity_ad_filter.keras")


# Dataset loading function
def load_dataset(filepath, label):
    texts, labels = [], []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for line in data:
            texts.append(preprocess_text(line))
            labels.append(label)
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in {filepath}: {e}")
    return texts, labels


# Text preprocessing function
def preprocess_text(text):
    if not isinstance(text, str):
        logging.warning(f"Invalid text for preprocessing: {text}")
        return ""
    return re.sub(r"[^а-яА-Яa-zA-Z0-9]", " ", text).strip().lower()


# Asynchronous text classification
async def detect_profanity_or_ad(text):
    global model, tokenizer

    # Проверяем наличие модели
    if model is None:
        if not os.path.exists("models/profanity_ad_filter.keras"):
            logging.warning("Model file not found. Initiating training...")
            asyncio.create_task(train_model())
            return "Model is training. Please try later."
        try:
            model = tf.keras.models.load_model("models/profanity_ad_filter.keras")
            load_tokenizer()
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            return "Error loading model."

    # Проверяем текст
    if not text or not isinstance(text, str):
        logging.error(f"Invalid input text for classification: {text}")
        return "Invalid text"

    try:
        # Токенизация
        sequence = tokenizer.texts_to_sequences([text])
        if not sequence or all(len(seq) == 0 for seq in sequence):
            logging.warning(f"Unable to tokenize text: {text}")
            return "Invalid text"

        padded = pad_sequences(sequence, maxlen=MAX_SEQUENCE_LENGTH)
        logging.info(f"Tokenized text: {sequence}, Padded: {padded}")

        # Предсказание
        prediction = model.predict(padded)
        logging.info(f"Prediction: {prediction}")

        prediction_class = np.argmax(prediction, axis=-1)[0]
        if prediction_class == 1:
            return "Нецензурная брань"
        elif prediction_class == 2:
            return "Реклама"
        return "Нормальный текст"

    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        return "Error processing text"



# Monitor dataset changes and trigger retraining
async def monitor_dataset_changes(reload_interval=10):
    dataset_files = [
        "dataset/ru/neutral.json",
        "dataset/ru/ads.json",
        "dataset/ru/profanity.json",
    ]
    file_hashes = {file: get_file_hash(file) for file in dataset_files}

    while True:
        await asyncio.sleep(reload_interval)
        for file in dataset_files:
            new_hash = get_file_hash(file)
            if new_hash != file_hashes[file]:
                logging.info(f"Changes detected in {file}. Retraining model.")
                await train_model()
                file_hashes[file] = new_hash


# Get file hash
def get_file_hash(filepath):
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except FileNotFoundError:
        return None


if __name__ == "__main__":
    if not os.path.exists("models/profanity_ad_filter.keras"):
        asyncio.run(train_model())
    asyncio.run(monitor_dataset_changes())
