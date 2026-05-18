#!/usr/bin/env python3
"""
NET-08: Feature extractor
Consulta InfluxDB y construye ventanas temporales para el LSTM.
"""
import os
import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv

load_dotenv()

WINDOW_SIZE        = int(os.getenv('WINDOW_SIZE', 60))
PREDICTION_HORIZON = int(os.getenv('PREDICTION_HORIZON', 5))


def query_metrics(client: InfluxDBClient, minutes: int = 120) -> pd.DataFrame:
    query = f'''
    from(bucket: "network-metrics")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r._measurement == "interface_metrics")
      |> filter(fn: (r) => r._field == "rx_bytes" or r._field == "tx_bytes" or r._field == "rx_errors")
      |> aggregateWindow(every: 5s, fn: mean, createEmpty: false)
      |> pivot(rowKey: ["_time", "node"], columnKey: ["_field"], valueColumn: "_value")
    '''
    try:
        result = client.query_api().query_data_frame(
            query, org=os.getenv('INFLUXDB_ORG', 'telecom-lab')
        )
        return result if isinstance(result, pd.DataFrame) else pd.DataFrame()
    except Exception as e:
        print(f'[Features] Error consultando InfluxDB: {e}')
        return pd.DataFrame()


def extract_features(df: pd.DataFrame) -> np.ndarray:
    """Calcula delta_rx, delta_tx, error_ratio y utilization por nodo."""
    if df.empty:
        return np.array([])

    features = []
    for node in df['node'].unique():
        node_df = df[df['node'] == node].sort_values('_time').copy()
        node_df['delta_rx']    = node_df['rx_bytes'].diff().fillna(0)
        node_df['delta_tx']    = node_df['tx_bytes'].diff().fillna(0)
        node_df['error_ratio'] = (node_df['rx_errors'] / (node_df['rx_bytes'] + 1)).fillna(0)
        node_df['utilization'] = (node_df['delta_rx'] / (10e6 * 5)).clip(0, 1)
        features.append(
            node_df[['delta_rx', 'delta_tx', 'error_ratio', 'utilization']].values
        )
    return np.array(features, dtype=object)


def build_lstm_windows(features: np.ndarray) -> np.ndarray:
    """Convierte features en ventanas (samples, WINDOW_SIZE, n_features)."""
    X = []
    for node_features in features:
        if len(node_features) < WINDOW_SIZE:
            continue
        for i in range(len(node_features) - WINDOW_SIZE):
            X.append(node_features[i:i + WINDOW_SIZE])
    return np.array(X) if X else np.array([])


def generate_demo_features(n_nodes: int = 10, n_steps: int = 120) -> np.ndarray:
    """Genera features sinteticas para demo sin InfluxDB."""
    np.random.seed(42)
    features = []
    for _ in range(n_nodes):
        util     = np.clip(np.random.normal(0.3, 0.15, n_steps), 0, 1)
        delta_rx = util * 10e6 * 5 * np.random.uniform(0.9, 1.1, n_steps)
        delta_tx = delta_rx * np.random.uniform(0.6, 1.0, n_steps)
        err      = np.random.uniform(0, 0.01, n_steps)
        features.append(np.column_stack([delta_rx, delta_tx, err, util]))
    return np.array(features)


if __name__ == '__main__':
    print('[Features] Modo demo — generando features sinteticas...')
    features = generate_demo_features()
    print(f'[Features] Shape features: {features.shape}')
    X = build_lstm_windows(features)
    print(f'[Features] Ventanas LSTM: {X.shape}')
