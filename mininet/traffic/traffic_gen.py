#!/usr/bin/env python3
"""
Generador de trafico sintetico con patrones normales y anomalos.
Genera datos etiquetados para entrenamiento del LSTM.
"""
import random
import json
import argparse
from datetime import datetime
from pathlib import Path

TRAFFIC_PATTERNS = {
    'normal':     {'bandwidth': '1M',   'duration': 10},
    'high_load':  {'bandwidth': '8M',   'duration': 15},
    'congestion': {'bandwidth': '9.5M', 'duration': 20},
    'burst':      {'bandwidth': '9M',   'duration': 5},
}


def generate_labeled_traffic(output_dir: str = 'paper/data'):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    records = []

    for pattern_name, params in TRAFFIC_PATTERNS.items():
        for i in range(10):
            bw_num = float(params['bandwidth'].replace('M', ''))
            record = {
                'timestamp': datetime.utcnow().isoformat(),
                'pattern': pattern_name,
                'bandwidth_mbps': round(bw_num + random.uniform(-0.2, 0.2), 3),
                'packet_loss': round(
                    random.uniform(0, 0.05) if pattern_name != 'congestion'
                    else random.uniform(0.1, 0.3), 4
                ),
                'latency_ms': round(
                    random.uniform(2, 8) if pattern_name != 'congestion'
                    else random.uniform(20, 80), 2
                ),
                'jitter_ms': round(random.uniform(0.1, 2.0), 3),
                'label': 1 if pattern_name in ['congestion', 'burst'] else 0
            }
            records.append(record)

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    output_file = f'{output_dir}/traffic_labeled_{ts}.json'
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2)

    print(f'[Traffic Gen] {len(records)} registros guardados en {output_file}')
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generador de trafico NET-08')
    parser.add_argument('--output', default='paper/data')
    args = parser.parse_args()
    generate_labeled_traffic(args.output)
