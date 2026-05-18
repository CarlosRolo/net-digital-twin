#!/usr/bin/env python3
"""
Motor de remediación automática.
Cuando el predictor supera el umbral de alerta, actúa sobre la red.
"""
import subprocess
import time
import json
from datetime import datetime
from rich.console import Console

console = Console()


class AutoRemediator:
    """
    Acciones disponibles cuando se detecta congestión inminente:
      1. Rate-limiting en el enlace congestionado (tc qdisc)
      2. Rerouting (modificar flujos OpenFlow via ovs-ofctl)
      3. Logging para el paper
    """

    def __init__(self, log_file: str = 'paper/data/remediation_log.jsonl'):
        self.log_file = log_file
        self.actions_taken = 0

    def apply_rate_limit(self, interface: str, rate_mbps: int = 5):
        """Aplica rate-limit via tc qdisc en la interfaz congestionada."""
        cmd = f"tc qdisc add dev {interface} root tbf rate {rate_mbps}mbit burst 32kbit latency 400ms"
        try:
            subprocess.run(cmd.split(), capture_output=True, timeout=5)
            console.print(f'[bold yellow][Remediación][/bold yellow] Rate-limit {rate_mbps}Mbps en {interface}')
            return True
        except Exception as e:
            console.print(f'[bold red][Remediación][/bold red] Error: {e}')
            return False

    def remove_rate_limit(self, interface: str):
        """Elimina rate-limit cuando la situación se normaliza."""
        cmd = f"tc qdisc del dev {interface} root"
        try:
            subprocess.run(cmd.split(), capture_output=True, timeout=5)
            console.print(f'[green][Remediación][/green] Rate-limit removido en {interface}')
        except Exception:
            pass

    def log_action(self, action: str, node: str, probability: float, result: str):
        """Registra cada acción para análisis posterior (paper)."""
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'node': node,
            'failure_probability': probability,
            'result': result,
            'action_id': self.actions_taken
        }
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
        self.actions_taken += 1
        return record

    def handle_alert(self, node: str, probability: float):
        """Punto de entrada principal cuando el predictor lanza alerta."""
        console.print(
            f'[bold red]🚨 ALERTA[/bold red] Nodo {node} | P(falla)={probability:.3f}'
        )
        interface = f'{node}-eth0'
        success = self.apply_rate_limit(interface, rate_mbps=3)
        action = 'rate_limit_applied' if success else 'rate_limit_failed'
        record = self.log_action(action, node, probability, 'ok' if success else 'failed')
        console.print(f'[Remediación] Acción registrada: {record["action_id"]}')
        return record


if __name__ == '__main__':
    remediator = AutoRemediator()
    remediator.handle_alert('d2', probability=0.92)
