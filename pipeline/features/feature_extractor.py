#!/usr/bin/env python3
"""
Feature extractor — consulta InfluxDB y construye ventanas temporales
para alimentar el modelo LSTM.
"""
import os
import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv

load_dotenv()

WINDOW_SIZE = int(os.getenv('WINDOW_SIZE', 60))   # 60 muestras = 5 min
PREDICTION_HORIZON = int(os.getenv('PREDICTION_HORIZON', 5))


def query_metrics(client: InfluxDBClient, minutes: int = 120) -> pd.DataFrame:
    """Consulta las últimas N minutos de métricas de todas las interfaces."""
    query = f'''
    from(bucket: "network-metrics")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r._measurement == "interface_metrics")
      |> filter(fn: (r) => r._field == "rx_bytes" or r._field == "tx_bytes" or r._field == "rx_errors")
      |> aggregateWindow(every: 5s, fn: mean, createEmpty: false)
      |> pivot(rowKey: ["_time", "node"], columnKey: ["_field"], valueColumn: "_value")
    '''
    result = client.query_api().query_data_frame(query, org=os.getenv('INFLUXDB_ORG'))
    return result


def extract_features(df: pd.DataFrame) -> np.ndarray:
    """
    Calcula features derivadas por nodo:
      - Tasa de cambio de bytes (delta_rx, delta_tx)
      - Ratio de errores
      - Utilización estimada (%)
    """
    if df.empty:
        return np.array([])

    features = []
    for node in df['node'].unique():
        node_df = df[df['node'] == node].sort_values('_time').copy()
        node_df['delta_rx']    = node_df['rx_bytes'].diff().fillna(0)
        node_df['delta_tx']    = node_df['tx_bytes'].diff().fillna(0)
        node_df['error_ratio'] = (node_df['rx_errors'] / (node_df['rx_bytes'] + 1)).fillna(0)
        node_df['utilization'] = (node_df['delta_rx'] / (10e6 * 5)).clip(0, 1)  # 10 Mbps / 5s
        features.append(node_df[['delta_rx', 'delta_tx', 'error_ratio', 'utilization']].values)

    return np.array(features)


def build_lstm_windows(features: np.ndarray) -> tuple:
    """
    Convierte features en ventanas deslizantes para LSTM.
    Returns: (X, shapes) donde X.shape = (samples, WINDOW_SIZE, n_features)
    """
    X = []
    for node_features in features:
        if len(node_features) < WINDOW_SIZE:
            continue
        for i in range(len(node_features) - WINDOW_SIZE):
            window = node_features[i:i + WINDOW_SIZE]
            X.append(window)
    return np.array(X)


if __name__ == '__main__':
    client = InfluxDBClient(
        url=os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
        token=os.getenv('INFLUXDB_TOKEN', 'my-super-secret-token'),
        org=os.getenv('INFLUXDB_ORG', 'telecom-lab')
    )
    df = query_metrics(client, minutes=60)
    print(f'[Features] {len(df)} registros consultados')
    features = extract_features(df)
    print(f'[Features] Shape: {features.shape}')
    X = build_lstm_windows(features)
    print(f'[Features] Ventanas LSTM: {X.shape}')
    client.close()
