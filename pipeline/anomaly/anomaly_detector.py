#!/usr/bin/env python3
"""
NET-08: Anomaly Detector
Deteccion estadistica de anomalias como capa previa al LSTM.
Usa z-score y umbral de percentil para filtrar ruido.
"""
import numpy as np
from dataclasses import dataclass
from typing import List


@dataclass
class AnomalyResult:
    node:       str
    metric:     str
    value:      float
    z_score:    float
    is_anomaly: bool
    severity:   str


class AnomalyDetector:
    """
    Detector estadistico de anomalias basado en z-score.
    Actua como filtro previo al modelo LSTM para reducir
    falsos positivos en periodos de trafico estable.
    """

    def __init__(self, z_threshold: float = 2.5, window: int = 60):
        self.z_threshold = z_threshold
        self.window      = window
        self.history: dict = {}

    def update(self, node: str, metric: str, value: float):
        """Agrega un nuevo valor al historial del nodo/metrica."""
        key = f'{node}:{metric}'
        if key not in self.history:
            self.history[key] = []
        self.history[key].append(value)
        if len(self.history[key]) > self.window:
            self.history[key].pop(0)

    def detect(self, node: str, metric: str, value: float) -> AnomalyResult:
        """Calcula z-score y determina si el valor es anomalo."""
        self.update(node, metric, value)
        key  = f'{node}:{metric}'
        hist = self.history[key]

        if len(hist) < 10:
            return AnomalyResult(node, metric, value, 0.0, False, 'NORMAL')

        mean   = np.mean(hist)
        std    = np.std(hist) + 1e-9
        z      = abs((value - mean) / std)

        if z > self.z_threshold * 1.5:
            severity = 'CRITICAL'
        elif z > self.z_threshold:
            severity = 'WARNING'
        else:
            severity = 'NORMAL'

        return AnomalyResult(
            node       = node,
            metric     = metric,
            value      = round(value, 4),
            z_score    = round(float(z), 4),
            is_anomaly = z > self.z_threshold,
            severity   = severity
        )

    def scan_window(self, node: str, window: np.ndarray) -> List[AnomalyResult]:
        """
        Escanea una ventana completa (WINDOW_SIZE, N_FEATURES).
        Features: delta_rx, delta_tx, error_ratio, utilization
        """
        metrics  = ['delta_rx', 'delta_tx', 'error_ratio', 'utilization']
        results  = []
        for i, metric in enumerate(metrics):
            last_val = float(window[-1, i])
            result   = self.detect(node, metric, last_val)
            results.append(result)
        return results

    def summary(self, results: List[AnomalyResult]) -> dict:
        """Resumen ejecutivo de una lista de resultados."""
        anomalies = [r for r in results if r.is_anomaly]
        critical  = [r for r in anomalies if r.severity == 'CRITICAL']
        return {
            'total_checked': len(results),
            'anomalies':     len(anomalies),
            'critical':      len(critical),
            'max_z_score':   max((r.z_score for r in results), default=0.0),
            'affected_metrics': [r.metric for r in anomalies]
        }


if __name__ == '__main__':
    import random
    detector = AnomalyDetector()

    print('[AnomalyDetector] Simulando 80 ciclos de trafico normal...')
    for _ in range(80):
        detector.detect('d2', 'utilization', random.uniform(0.2, 0.4))

    print('[AnomalyDetector] Inyectando anomalia...')
    result = detector.detect('d2', 'utilization', 0.97)
    print(f'  Resultado: {result}')

    window = np.random.rand(60, 4)
    window[:, 3] = 0.95
    results = detector.scan_window('d2', window)
    print(f'  Resumen ventana: {detector.summary(results)}')
