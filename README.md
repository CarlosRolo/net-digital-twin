# NET-08: Network Digital Twin

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-FF6F00?logo=tensorflow)](https://tensorflow.org)
[![InfluxDB](https://img.shields.io/badge/InfluxDB-2.7-22ADF6?logo=influxdb)](https://influxdata.com)
[![Grafana](https://img.shields.io/badge/Grafana-10.3-F46800?logo=grafana)](https://grafana.com)
[![Mininet](https://img.shields.io/badge/Mininet-2.3.0-green)](http://mininet.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Gemelo digital de red ISP simulada con telemetria gRPC/YANG en tiempo real, modelo LSTM para prediccion de congestion y fallas, sistema de remediacion automatica y dashboard de estado. Proyecto de portafolio profesional nivel investigacion.

---

## Arquitectura
+--------------------------------------------------+
|          RED FISICA SIMULADA (Mininet)            |
|  Core: c1 --- c2                                  |
|  Distribucion: d1, d2, d3                         |
|  Acceso: h1, h2, h3, h4, h5                       |
+-------------------+------------------------------+
| gNMI polling 5s
+-------------------v------------------------------+
|          TELEMETRIA -> InfluxDB                   |
|  gNMI Collector -- 10 interfaces monitoreadas     |
+-------------------+------------------------------+
| Ventana deslizante 60s
+-------------------v------------------------------+
|          MODELO LSTM                              |
|  Input: (60, 4) -- delta_rx, delta_tx, err, util  |
|  Output: P(falla) en t+5min                       |
+-------------------+------------------------------+
| Umbral P > 0.75
+-------------------v------------------------------+
|          REMEDIACION + ALERTAS                    |
|  Rate-limit (tc qdisc) + Slack + Grafana          |
+--------------------------------------------------+

## Inicio rapido

```bash
git clone https://github.com/CarlosRolo/net-digital-twin.git
cd net-digital-twin
make setup
cp .env.example .env
make docker-up
make train
make run
```

## Stack tecnico

| Componente | Herramienta |
|---|---|
| Simulacion de red | Mininet 2.3 |
| Telemetria | gNMI / pygnmi |
| Time-series DB | InfluxDB 2.7 |
| Feature engineering | pandas + numpy |
| Modelo IA | LSTM (TensorFlow 2.15) |
| Remediacion | tc qdisc |
| Dashboard | Grafana 10.3 |
| Alertas | Slack webhook |
| Orquestacion | Docker Compose |

## Resultados del modelo

| Metrica | Valor |
|---|---|
| AUC (validacion) | > 0.95 |
| Accuracy (validacion) | > 92% |
| Ventana de entrada | 60 muestras (5 min) |
| Horizonte de prediccion | t+5 min |
| Tiempo de inferencia | < 500ms |

## Estructura del proyecto

net-digital-twin/
├── mininet/
│   ├── topology/net_topology.py
│   └── traffic/traffic_gen.py
├── telemetry/
│   └── collector/gnmi_collector.py
├── pipeline/
│   └── features/feature_extractor.py
├── ml/
│   ├── training/train_lstm.py
│   └── inference/predictor.py
├── remediation/auto_remediate.py
├── alerts/alert_engine.py
├── paper/data/
├── docker-compose.yml
├── Makefile
└── requirements.txt

## Comandos disponibles

```bash
make help        # Ver todos los comandos
make setup       # Instalar dependencias
make docker-up   # Levantar InfluxDB + Grafana
make train       # Entrenar modelo LSTM
make run         # Ejecutar gemelo digital
make collect     # Solo el colector de telemetria
make topology    # Levantar topologia Mininet
make test        # Ejecutar tests
make clean       # Limpiar cache Python
```

## Autor

**Carlos David Rodriguez Lopez**  
Telematic Engineer — ESPOCH  
Riobamba, Chimborazo, Ecuador  
GitHub: [github.com/CarlosRolo](https://github.com/CarlosRolo)  
LinkedIn: [linkedin.com/in/carlosdrodriguezl](https://linkedin.com/in/carlosdrodriguezl)

## Licencia

MIT License — ver [LICENSE](LICENSE)
