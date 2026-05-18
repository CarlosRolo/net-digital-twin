#!/usr/bin/env python3
"""
NET-08: InfluxDB Writer
Escribe datos de trafico etiquetado desde traffic_gen al bucket.
"""
import os
import json
import glob
from datetime import datetime
from pathlib import Path
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

load_dotenv()

INFLUX_URL    = os.getenv('INFLUXDB_URL',    'http://localhost:8086')
INFLUX_TOKEN  = os.getenv('INFLUXDB_TOKEN',  'my-super-secret-token')
INFLUX_ORG    = os.getenv('INFLUXDB_ORG',    'telecom-lab')
INFLUX_BUCKET = os.getenv('INFLUXDB_BUCKET', 'network-metrics')


def write_labeled_traffic(json_file: str):
    """Lee un archivo JSON de traffic_gen y lo escribe en InfluxDB."""
    with open(json_file) as f:
        records = json.load(f)

    client    = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    points    = []

    for r in records:
        point = (
            Point("labeled_traffic")
            .tag("pattern", r['pattern'])
            .tag("label",   str(r['label']))
            .field("bandwidth_mbps", float(r['bandwidth_mbps']))
            .field("packet_loss",    float(r['packet_loss']))
            .field("latency_ms",     float(r['latency_ms']))
            .field("jitter_ms",      float(r['jitter_ms']))
            .field("label",          int(r['label']))
        )
        points.append(point)

    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
    print(f'[InfluxWriter] {len(points)} registros escritos desde {json_file}')
    client.close()


def write_all(data_dir: str = 'paper/data'):
    """Procesa todos los JSON de trafico en el directorio."""
    files = glob.glob(f'{data_dir}/traffic_labeled_*.json')
    if not files:
        print(f'[InfluxWriter] No se encontraron archivos en {data_dir}')
        return
    for f in files:
        write_labeled_traffic(f)


if __name__ == '__main__':
    write_all()
