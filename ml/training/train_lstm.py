#!/usr/bin/env python3
"""
Entrenamiento del modelo LSTM para predicción de congestión/fallas.
Genera sintéticamente el dataset de entrenamiento si no existe.
"""
import os
import json
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

WINDOW_SIZE   = 60
N_FEATURES    = 4
MODEL_DIR     = Path('ml/models')
MODEL_PATH    = MODEL_DIR / 'lstm_failure.h5'
SCALER_PATH   = MODEL_DIR / 'scaler.pkl'


def generate_synthetic_dataset(n_samples: int = 2000) -> tuple:
    """
    Genera dataset sintético que simula:
      - Clase 0: tráfico normal (utilización < 70%)
      - Clase 1: congestión / falla inminente (utilización > 85%)
    """
    np.random.seed(42)
    X, y = [], []

    for _ in range(n_samples):
        label = np.random.randint(0, 2)
        base_util = np.random.uniform(0.1, 0.6) if label == 0 else np.random.uniform(0.75, 1.0)

        window = []
        for t in range(WINDOW_SIZE):
            util      = base_util + np.random.normal(0, 0.05)
            delta_rx  = util * 10e6 * 5 * np.random.uniform(0.8, 1.2)
            delta_tx  = delta_rx * np.random.uniform(0.6, 1.0)
            err_ratio = np.random.uniform(0, 0.01) if label == 0 else np.random.uniform(0.05, 0.2)
            window.append([delta_rx, delta_tx, err_ratio, np.clip(util, 0, 1)])

        X.append(window)
        y.append(label)

    return np.array(X), np.array(y)


def build_lstm_model() -> tf.keras.Model:
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(WINDOW_SIZE, N_FEATURES)),
        BatchNormalization(),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        BatchNormalization(),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    return model


def train():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print('[LSTM] Generando dataset sintético...')
    X, y = generate_synthetic_dataset(n_samples=3000)
    print(f'[LSTM] Dataset: {X.shape}, labels: {y.sum()} positivos / {len(y)-y.sum()} negativos')

    # Normalizar
    X_flat = X.reshape(-1, N_FEATURES)
    scaler = StandardScaler()
    X_flat_scaled = scaler.fit_transform(X_flat)
    X_scaled = X_flat_scaled.reshape(X.shape)
    joblib.dump(scaler, SCALER_PATH)
    print(f'[LSTM] Scaler guardado en {SCALER_PATH}')

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)

    model = build_lstm_model()
    model.summary()

    callbacks = [
        EarlyStopping(monitor='val_auc', patience=5, restore_best_weights=True, mode='max'),
        ModelCheckpoint(str(MODEL_PATH), monitor='val_auc', save_best_only=True, mode='max')
    ]

    history = model.fit(
        X_train, y_train,
        epochs=30,
        batch_size=64,
        validation_split=0.2,
        callbacks=callbacks,
        verbose=1
    )

    # Evaluación
    y_pred = (model.predict(X_test) > 0.5).astype(int).flatten()
    print('\n[LSTM] Reporte de clasificación:')
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Falla']))

    # Guardar métricas para el paper
    metrics = {
        'accuracy':  float(history.history['accuracy'][-1]),
        'val_accuracy': float(history.history['val_accuracy'][-1]),
        'val_auc':   float(history.history['val_auc'][-1]),
        'epochs_trained': len(history.history['loss'])
    }
    with open('paper/data/model_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f'\n[LSTM] Modelo guardado en {MODEL_PATH}')
    print(f'[LSTM] Métricas: {metrics}')


if __name__ == '__main__':
    train()
