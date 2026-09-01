# combined for MQTT and Geolux Hydroview API
import asyncio
import logging
import os
import json
import csv
from datetime import datetime
import httpx
import gmqtt  # Asynchronous MQTT client built for asyncio
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==========================================
# 1. GEOLUX HTTP POLLING TASK (PULL)
# ==========================================
async def geolux_polling_loop():
    """Polls Geolux / HydroView REST endpoints on a scheduled interval."""
    sites = [
        {"site_name": "02_30163", "site_id": os.getenv("GEOLUX_SITE_1_ID")},
        {"site_name": "04_30164", "site_id": os.getenv("GEOLUX_SITE_2_ID")},
    ]
    token = os.getenv("GEOLUX_AUTH_TOKEN")
    base_url = "https://hydro-view.com/api/v1/data/export"
    poll_interval = int(os.getenv("HTTP_POLL_INTERVAL_SEC", "900"))  # Default 15 mins

    async with httpx.AsyncClient(verify=False) as client:
        while True:
            logging.info("Starting Geolux HTTP polling sweep...")
            for site in sites:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    url = f"{base_url}?site_id={site['site_id']}&measurements=0,1,2,3,4,5&time_format=text"
                    
                    response = await client.get(url, headers=headers, timeout=15.0)
                    if response.status_code == 200:
                        logging.info(f"[Geolux] Telemetry received for site: {site['site_name']}")
                        # Process and write CSV / InfluxDB logic here
                    else:
                        logging.error(f"[Geolux] Failed site {site['site_name']}: HTTP {response.status_code}")
                except Exception as e:
                    logging.error(f"[Geolux] Error fetching {site['site_name']}: {str(e)}")

            await asyncio.sleep(poll_interval)


# ==========================================
# 2. CAMPBELLSCI MQTT LISTENER TASK (PUSH)
# ==========================================
def on_mqtt_message(client, topic, payload, qos, properties):
    """Processes incoming Campbell Scientific telemetry messages."""
    try:
        data = json.loads(payload.decode('utf-8'))
        logging.info(f"[CampbellSci MQTT] Message received on topic: {topic}")
        # Parse observations and save CSV logic here
    except Exception as e:
        logging.error(f"[CampbellSci MQTT] Error parsing payload: {str(e)}")

async def campbellsci_mqtt_loop():
    """Maintains an persistent, async MQTT connection for Campbell Scientific streams."""
    client = gmqtt.Client(client_id="Async_Telemetry_Engine_Node")
    client.on_message = on_mqtt_message

    broker = os.getenv("MQTT_BROKER_HOST", "test.mosquitto.org")
    port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    topic = os.getenv("MQTT_TOPIC", "PDRRMO/#")

    logging.info(f"[CampbellSci MQTT] Connecting to {broker}:{port}...")
    await client.connect(broker, port=port)
    client.subscribe(topic)

    # Keep MQTT connection alive indefinitely
    while True:
        await asyncio.sleep(3600)


# ==========================================
# 3. UNIFIED ENGINE ENTRYPOINT
# ==========================================
async def main():
    logging.info("Initializing Unified Async Telemetry Engine (Geolux + CampbellSci)...")
    
    # Run HTTP Polling and MQTT Listening simultaneously
    await asyncio.gather(
        geolux_polling_loop(),
        campbellsci_mqtt_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Telemetry Engine stopped gracefully.")
