#!/usr/bin/env python3
"""
NET-08: Predictor en tiempo real
Carga el modelo LSTM y predice probabilidad de falla por ventana.
"""
import os
import numpy as np
import joblib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf

MODEL_PATH  = os.getenv('MODEL_PATH', 'ml/models/lstm_failure.h5')
SCALER_PATH = 'ml/models/scaler.pkl'
THRESHOLD   = float(os.getenv('ALERT_THRESHOLD', 0.75))


class FailurePredictor:

    def __init__(self):
        self.model  = None
        self.scaler = None
        self._load()

    def _load(self):
        if Path(MODEL_PATH).exists() and Path(SCALER_PATH).exists():
            self.model  = tf.keras.models.load_model(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            print(f'[Predictor] Modelo cargado desde {MODEL_PATH}')
        else:
            print('[Predictor] Modelo no encontrado. Ejecuta: make train')

    def predict(self, window: np.ndarray) -> dict:
        """
        window: array (WINDOW_SIZE, N_FEATURES)
        Returns: probability, alert, risk_level
        """
        if self.model is None:
            return {'probability': 0.0, 'alert': False, 'risk_level': 'unknown'}

        window_flat   = window.reshape(-1, window.shape[-1])
        window_scaled = self.scaler.transform(window_flat).reshape(1, *window.shape)
        prob = float(self.model.predict(window_scaled, verbose=0)[0][0])

        if prob > THRESHOLD:
            risk = 'CRITICAL'
        elif prob > 0.5:
            risk = 'WARNING'
        else:
            risk = 'NORMAL'

        return {
            'probability': round(prob, 4),
            'alert':       prob > THRESHOLD,
            'risk_level':  risk
        }


if __name__ == '__main__':
    predictor = FailurePredictor()
    test_window = np.random.rand(60, 4)
    result = predictor.predict(test_window)
    print(f'[Predictor] Test resultado: {result}')
