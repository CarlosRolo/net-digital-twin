#!/usr/bin/env python3
"""
Generador de tráfico sintético con patrones normales y anómalos.
Genera datos etiquetados para entrenamiento del LSTM.
"""
import subprocess
import time
import random
import json
import argparse
from datetime import datetime
from pathlib import Path


TRAFFIC_PATTERNS = {
    'normal': {'bandwidth': '1M', 'duration': 10},
    'high_load': {'bandwidth': '8M', 'duration': 15},
    'congestion': {'bandwidth': '9.5M', 'duration': 20},
    'burst': {'bandwidth': '9M', 'duration': 5},
}


def generate_labeled_traffic(output_dir: str = 'paper/data'):
    """Genera tráfico etiquetado para el dataset del paper."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    records = []

    for pattern_name, params in TRAFFIC_PATTERNS.items():
        for i in range(10):  # 10 muestras por patrón
            timestamp = datetime.utcnow().isoformat()
            bw = params['bandwidth']
            dur = params['duration']

            # Simular métricas (en entorno real usaría iperf3)
            bw_num = float(bw.replace('M', ''))
            record = {
                'timestamp': timestamp,
                'pattern': pattern_name,
                'bandwidth_mbps': bw_num + random.uniform(-0.2, 0.2),
                'packet_loss': random.uniform(0, 0.05) if pattern_name != 'congestion' else random.uniform(0.1, 0.3),
                'latency_ms': random.uniform(2, 8) if pattern_name != 'congestion' else random.uniform(20, 80),
                'jitter_ms': random.uniform(0.1, 2.0),
                'label': 1 if pattern_name in ['congestion', 'burst'] else 0
            }
            records.append(record)

    output_file = f'{output_dir}/traffic_labeled_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2)

    print(f'[Traffic Gen] {len(records)} registros guardados en {output_file}')
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generador de tráfico NET-08')
    parser.add_argument('--output', default='paper/data', help='Directorio de salida')
    args = parser.parse_args()
    generate_labeled_traffic(args.output)
