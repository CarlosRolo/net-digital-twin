#!/usr/bin/env python3
"""
NET-08: Metrics Publisher
Publica metricas resumidas en consola y archivo para el paper.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv

load_dotenv()

INFLUX_URL    = os.getenv('INFLUXDB_URL',    'http://localhost:8086')
INFLUX_TOKEN  = os.getenv('INFLUXDB_TOKEN',  'my-super-secret-token')
INFLUX_ORG    = os.getenv('INFLUXDB_ORG',    'telecom-lab')


def get_latest_metrics(minutes: int = 10) -> list:
    """Consulta las ultimas N metricas por nodo."""
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query = f'''
    from(bucket: "network-metrics")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r._measurement == "interface_metrics")
      |> filter(fn: (r) => r._field == "rx_bytes" or r._field == "tx_bytes")
      |> last()
      |> pivot(rowKey: ["node"], columnKey: ["_field"], valueColumn: "_value")
    '''
    try:
        df = client.query_api().query_data_frame(query, org=INFLUX_ORG)
        records = df.to_dict('records') if not df.empty else []
        return records
    except Exception as e:
        print(f'[Publisher] Error: {e}')
        return []
    finally:
        client.close()


def publish_summary(output_dir: str = 'paper/data'):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    records = get_latest_metrics()
    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'nodes_reporting': len(records),
        'records': records
    }
    out = f'{output_dir}/metrics_summary_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
    with open(out, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'[Publisher] Resumen guardado: {out}')
    return summary


if __name__ == '__main__':
    publish_summary()
