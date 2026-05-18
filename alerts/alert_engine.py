#!/usr/bin/env python3
"""
Motor de alertas — integra predictor + remediador + notificaciones.
Loop principal del gemelo digital.
"""
import os
import time
import numpy as np
import requests
from datetime import datetime
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

load_dotenv()

from ml.inference.predictor import FailurePredictor
from remediation.auto_remediate import AutoRemediator

console = Console()
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL', '')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 5))


def send_slack_alert(node: str, probability: float, action: str):
    if not SLACK_WEBHOOK:
        return
    payload = {
        "text": f"🚨 *NET-08 Digital Twin Alert*\n"
                f"Nodo: `{node}` | P(falla): `{probability:.3f}`\n"
                f"Acción: `{action}`\n"
                f"Timestamp: `{datetime.utcnow().isoformat()}`"
    }
    try:
        requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
    except Exception:
        pass


def print_status_table(results: list):
    table = Table(title=f"[NET-08] Estado @ {datetime.utcnow().strftime('%H:%M:%S')}")
    table.add_column("Nodo",        style="cyan")
    table.add_column("P(falla)",    style="magenta")
    table.add_column("Nivel riesgo",style="bold")
    table.add_column("Alerta",      style="red")

    for r in results:
        level = r['risk_level']
        color = 'red' if level == 'CRITICAL' else 'yellow' if level == 'WARNING' else 'green'
        table.add_row(
            r['node'], f"{r['probability']:.4f}",
            f"[{color}]{level}[/{color}]",
            "⚠️ SÍ" if r['alert'] else "✅ NO"
        )
    console.print(table)


def run_digital_twin():
    """Loop principal del gemelo digital."""
    predictor   = FailurePredictor()
    remediator  = AutoRemediator()
    NODES = ['c1', 'c2', 'd1', 'd2', 'd3', 'h1', 'h2', 'h3', 'h4', 'h5']

    console.print('[bold green]NET-08 Digital Twin iniciado[/bold green]')

    while True:
        results = []
        for node in NODES:
            # En producción: obtener ventana real de InfluxDB
            # En demo: ventana aleatoria con distribución realista
            window = np.random.rand(60, 4)
            window[:, 3] = np.clip(np.random.normal(0.3, 0.2, 60), 0, 1)  # utilización

            prediction = predictor.predict(window)
            prediction['node'] = node

            if prediction['alert']:
                record = remediator.handle_alert(node, prediction['probability'])
                send_slack_alert(node, prediction['probability'], record['action'])

            results.append(prediction)

        print_status_table(results)
        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    run_digital_twin()
