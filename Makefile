.PHONY: help setup train run test clean docker-up docker-down collect topology

help:
	@echo "NET-08: Network Digital Twin"
	@echo "make setup       - Instalar dependencias"
	@echo "make train       - Entrenar modelo LSTM"
	@echo "make run         - Ejecutar gemelo digital"
	@echo "make test        - Ejecutar tests"
	@echo "make docker-up   - Levantar InfluxDB + Grafana"
	@echo "make docker-down - Detener servicios"
	@echo "make collect     - Iniciar colector de telemetria"
	@echo "make topology    - Levantar topologia Mininet"

setup:
	python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt

train:
	python3 ml/training/train_lstm.py

run:
	python3 alerts/alert_engine.py

test:
	pytest tests/ -v

docker-up:
	docker compose up -d influxdb grafana
	@echo "InfluxDB: http://localhost:8086"
	@echo "Grafana:  http://localhost:3000"

docker-down:
	docker compose down

collect:
	python3 telemetry/collector/gnmi_collector.py

topology:
	sudo python3 mininet/topology/net_topology.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
