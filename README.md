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

```
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
```

---

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

---

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

---

## Resultados del modelo

| Metrica | Valor |
|---|---|
| AUC (validacion) | > 0.95 |
| Accuracy (validacion) | > 92% |
| Ventana de entrada | 60 muestras (5 min) |
| Horizonte de prediccion | t+5 min |
| Tiempo de inferencia | < 500ms |
| Dataset sintetico | 3000 muestras balanceadas |

---

## Estructura del proyecto

```
net-digital-twin/
├── mininet/
│   ├── topology/
│   │   └── net_topology.py          # Topologia ISP 10 nodos (3 capas)
│   └── traffic/
│       └── traffic_gen.py           # Generador de trafico etiquetado
├── telemetry/
│   ├── Dockerfile
│   └── collector/
│       ├── gnmi_collector.py        # Colector gNMI -> InfluxDB
│       └── metrics_publisher.py
├── pipeline/
│   ├── ingestion/
│   │   └── influx_writer.py
│   ├── features/
│   │   └── feature_extractor.py     # Ventanas deslizantes LSTM
│   └── anomaly/
│       └── anomaly_detector.py
├── ml/
│   ├── models/                      # Modelos entrenados (.h5, .pkl)
│   ├── training/
│   │   └── train_lstm.py            # Entrenamiento + evaluacion
│   └── inference/
│       └── predictor.py             # Inferencia en tiempo real
├── remediation/
│   └── auto_remediate.py            # Rate-limit automatico (tc qdisc)
├── alerts/
│   └── alert_engine.py             # Loop principal del gemelo
├── dashboard/
│   └── grafana/
│       ├── dashboards/
│       └── provisioning/
├── paper/
│   ├── data/                        # Metricas, logs y datasets
│   ├── figures/
│   └── notebooks/
├── tests/
│   └── __init__.py
├── docs/
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── .env.example
```

---

## Comandos disponibles

```bash
make help        # Ver todos los comandos
make setup       # Instalar dependencias en venv
make docker-up   # Levantar InfluxDB + Grafana
make docker-down # Detener servicios Docker
make train       # Entrenar modelo LSTM
make run         # Ejecutar gemelo digital (loop principal)
make collect     # Solo el colector de telemetria
make topology    # Levantar topologia Mininet
make test        # Ejecutar tests con pytest
make clean       # Limpiar cache Python
```

---

## Variables de entorno

Copia `.env.example` a `.env` y configura:

```env
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-token
INFLUXDB_ORG=telecom-lab
INFLUXDB_BUCKET=network-metrics
GRAFANA_URL=http://localhost:3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ALERT_THRESHOLD=0.75
MODEL_PATH=ml/models/lstm_failure.h5
WINDOW_SIZE=60
PREDICTION_HORIZON=5
POLL_INTERVAL=5
```

---

## Flujo de datos

```
Mininet (10 nodos)
    |
    | ovs-vsctl / gNMI polling cada 5s
    v
gnmi_collector.py
    |
    | InfluxDB write API
    v
InfluxDB 2.7 (bucket: network-metrics)
    |
    | Flux query — ultimos 120 min
    v
feature_extractor.py
    |
    | Ventana deslizante (60, 4)
    | features: delta_rx, delta_tx, error_ratio, utilization
    v
predictor.py — LSTM inference
    |
    | P(falla) por nodo
    v
alert_engine.py
    |-- P < 0.50  --> NORMAL   (log solamente)
    |-- P 0.50-0.75 -> WARNING  (log + consola)
    +-- P > 0.75  --> CRITICAL  (remediacion + Slack + log)
                          |
                          v
                  auto_remediate.py
                  tc qdisc rate-limit en interfaz
```

---

## Autor

**Carlos David Rodriguez Lopez**  
Telematic Engineer — ESPOCH  
Riobamba, Chimborazo, Ecuador  
GitHub: [github.com/CarlosRolo](https://github.com/CarlosRolo)  
LinkedIn: [linkedin.com/in/carlosdrodriguezl](https://linkedin.com/in/carlosdrodriguezl)

---

## Licencia

MIT License — ver [LICENSE](LICENSE)
