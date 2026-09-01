# High-Availability Asynchronous Telemetry Ingestion Engine

An asynchronous Python-based daemon designed for fault-tolerant telemetry data collection from remote environmental and water-resource sensor networks (e.g., PDRRMO river and rain gauges).

## Key Features
* **Asynchronous Concurrency:** Built on `asyncio` and `httpx` to poll hundreds of remote edge devices concurrently without blocking thread execution.
* **Exponential Backoff & Jitter:** Prevents connection stampedes by utilizing adaptive exponential retry delays during network degradation or field outage events.
* **Packet Loss Resilience:** Maintains continuous polling loops with zero data frame drops, routing permanently unreachable nodes to a Dead-Letter Queue (DLQ) pattern.
* **Clean Configuration Management:** Zero hardcoded endpoints; fully driven by environment variables (`.env`).

## System Architecture

```text
+-------------------+      +-----------------------+      +---------------------+
| Remote SCADA /    | ---> | Async Telemetry       | ---> | Central Time-Series |
| Sensor Edge Nodes |      | Daemon (Python/Async) |      | Database / Storage  |
+-------------------+      +-----------------------+      +---------------------+

Quickstart
Clone & Setup Virtual Environment:

Bash
git clone [https://github.com/jmichaellimpro-png/pdrrmo-async-telemetry-engine.git](https://github.com/jmichaellimpro-png/pdrrmo-async-telemetry-engine.git)
cd pdrrmo-async-telemetry-engine
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
Configure Environment:

Bash
cp .env.example .env
Run Ingestion Daemon:

Bash
python src/telemetry_engine.py
