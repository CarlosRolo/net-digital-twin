#!/usr/bin/env python3
"""
NET-08: Motor de alertas — loop principal del gemelo digital
Integra predictor + remediador + notificaciones en tiempo real.
"""
import os
import sys
import time
import numpy as np
import requests
from datetime import datetime
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.inference.predictor import FailurePredictor
from remediation.auto_remediate import AutoRemediator

console       = Console()
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL', '')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 5))

NODES = ['c1', 'c2', 'd1', 'd2', 'd3', 'h1', 'h2', 'h3', 'h4', 'h5']


def send_slack_alert(node: str, probability: float, action: str):
    if not SLACK_WEBHOOK or SLACK_WEBHOOK.endswith('...'):
        return
    payload = {
        "text": (
            f"NET-08 Digital Twin Alert\n"
            f"Nodo: `{node}` | P(falla): `{probability:.3f}`\n"
            f"Accion: `{action}` | {datetime.utcnow().isoformat()}"
        )
    }
    try:
        requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
    except Exception:
        pass


def make_status_table(results: list) -> Table:
    table = Table(title=f"NET-08 Digital Twin @ {datetime.utcnow().strftime('%H:%M:%S')}")
    table.add_column("Nodo",       style="cyan",    width=8)
    table.add_column("P(falla)",   style="magenta", width=10)
    table.add_column("Riesgo",     style="bold",    width=10)
    table.add_column("Alerta",     style="red",     width=8)

    for r in results:
        level = r['risk_level']
        color = 'red' if level == 'CRITICAL' else 'yellow' if level == 'WARNING' else 'green'
        table.add_row(
            r['node'],
            f"{r['probability']:.4f}",
            f"[{color}]{level}[/{color}]",
            "SI" if r['alert'] else "no"
        )
    return table


def simulate_window(node: str) -> np.ndarray:
    """Genera ventana sintetica realista por nodo."""
    is_core = node in ['c1', 'c2']
    base_util = np.random.uniform(0.1, 0.4) if is_core else np.random.uniform(0.2, 0.7)
    util = np.clip(np.random.normal(base_util, 0.1, 60), 0, 1)
    delta_rx  = util * 10e6 * 5 * np.random.uniform(0.9, 1.1, 60)
    delta_tx  = delta_rx * np.random.uniform(0.6, 1.0, 60)
    err_ratio = np.random.uniform(0, 0.01, 60)
    return np.column_stack([delta_rx, delta_tx, err_ratio, util])


def run():
    predictor  = FailurePredictor()
    remediator = AutoRemediator()

    console.print('[bold green]NET-08 Network Digital Twin iniciado[/bold green]')
    console.print(f'Monitoreando {len(NODES)} nodos cada {POLL_INTERVAL}s\n')

    cycle = 0
    while True:
        cycle += 1
        results = []

        for node in NODES:
            window     = simulate_window(node)
            prediction = predictor.predict(window)
            prediction['node'] = node

            if prediction['alert']:
                record = remediator.handle_alert(node, prediction['probability'])
                send_slack_alert(node, prediction['probability'], record['action'])

            results.append(prediction)

        console.print(make_status_table(results))
        console.print(f'[dim]Ciclo {cycle} — siguiente en {POLL_INTERVAL}s[/dim]\n')
        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    run()
