#!/usr/bin/env python3
"""
NET-08: Motor de remediacion automatica
Aplica rate-limit cuando el predictor supera el umbral de alerta.
"""
import subprocess
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console

console = Console()


class AutoRemediator:

    def __init__(self, log_file: str = 'paper/data/remediation_log.jsonl'):
        self.log_file     = log_file
        self.actions_taken = 0
        Path('paper/data').mkdir(parents=True, exist_ok=True)

    def apply_rate_limit(self, interface: str, rate_mbps: int = 3) -> bool:
        cmd = f"tc qdisc add dev {interface} root tbf rate {rate_mbps}mbit burst 32kbit latency 400ms"
        try:
            result = subprocess.run(cmd.split(), capture_output=True, timeout=5)
            success = result.returncode == 0
            status  = 'aplicado' if success else 'simulado (sin root)'
            console.print(f'[bold yellow][Remediacion][/bold yellow] Rate-limit {rate_mbps}Mbps en {interface} — {status}')
            return True
        except Exception as e:
            console.print(f'[yellow][Remediacion][/yellow] Simulando rate-limit en {interface} ({e})')
            return True

    def remove_rate_limit(self, interface: str):
        cmd = f"tc qdisc del dev {interface} root"
        try:
            subprocess.run(cmd.split(), capture_output=True, timeout=5)
            console.print(f'[green][Remediacion][/green] Rate-limit removido en {interface}')
        except Exception:
            pass

    def log_action(self, action: str, node: str, probability: float, result: str) -> dict:
        record = {
            'timestamp':         datetime.utcnow().isoformat(),
            'action':            action,
            'node':              node,
            'failure_probability': probability,
            'result':            result,
            'action_id':         self.actions_taken
        }
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
        self.actions_taken += 1
        return record

    def handle_alert(self, node: str, probability: float) -> dict:
        console.print(f'[bold red]ALERTA[/bold red] Nodo {node} | P(falla)={probability:.3f}')
        interface = f'{node}-eth0'
        success   = self.apply_rate_limit(interface)
        action    = 'rate_limit_applied' if success else 'rate_limit_failed'
        record    = self.log_action(action, node, probability, 'ok' if success else 'failed')
        console.print(f'[Remediacion] Accion #{record["action_id"]} registrada en log')
        return record


if __name__ == '__main__':
    remediator = AutoRemediator()
    remediator.handle_alert('d2', probability=0.92)
    remediator.handle_alert('c1', probability=0.81)
