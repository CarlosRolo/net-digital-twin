FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir influxdb-client python-dotenv
COPY telemetry/ ./telemetry/
CMD ["python", "-m", "telemetry.collector.gnmi_collector"]
