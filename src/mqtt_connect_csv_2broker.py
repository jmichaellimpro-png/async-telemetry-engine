import warnings
import json
import paho.mqtt.client as mqtt
import csv
import time
import os
import re
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import socket

warnings.filterwarnings("ignore", category=DeprecationWarning)

# MQTT Broker details
BROKER_1 = "test.mosquitto.org"
PORT_1 = 1883
TOPIC_1 = "TOPIC/#"

BROKER_2 = "hiveID.s1.eu.hivemq.cloud"
PORT_2 = 8883
TOPIC_2 = "TOPIC/#"

USERNAME_2 = "username"
PASSWORD_2 = "password"

retry_interval = 20
client_id_1 = "CSVWriter_topic1_vm1_new_distinctdate"
client_id_2 = "CSVWriter_topic2_vm1_new_distinctdate"

# Directory where CSV files will be saved
csv_directory = r"C:\\Users\\Administrator\\Desktop\\mqtt_csv_data"
if not os.path.exists(csv_directory):
    os.makedirs(csv_directory)

# Set up a rotating log handler
log_file = os.path.join(csv_directory, 'mqtt_connect_csv.log')
log_size = 10 * 1024 * 1024
backup_count = 5

logging.basicConfig(
    handlers=[RotatingFileHandler(log_file, maxBytes=log_size, backupCount=backup_count)],
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def print_with_timestamp(message):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
    logging.info(message)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print_with_timestamp("Connected successfully")
        client.subscribe(userdata['topic'], qos=1)
    else:
        print_with_timestamp(f"Failed to connect, return code {rc}")

def on_message(client, userdata, message):
    print_with_timestamp(f"Received message on topic {message.topic}")
    
    if re.match(r"^topic/Site\d+(/.*)?$", message.topic):
        try:
            data = json.loads(message.payload.decode("utf-8"))
            datalogger_id = message.topic.split("/")[1]
            observation_names = data["properties"]["observationNames"]
            observations = data["properties"]["observations"]

            f_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = os.path.join(csv_directory, f"{datalogger_id}_{f_timestamp}.csv")

            if not observations:
                print_with_timestamp("No observations found.")
                return

            headers = ["Timestamp"] + observation_names
            with open(csv_filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                for obs_timestamp, values in observations.items():
                    formatted_timestamp = obs_timestamp.replace("T", " ").replace("Z", "")
                    row = [formatted_timestamp] + values
                    writer.writerow(row)

            if os.path.getsize(csv_filename) == 0:
                os.remove(csv_filename)
                print_with_timestamp(f"Deleted empty file: {csv_filename}")
            else:
                print_with_timestamp(f"Data written to CSV: {csv_filename}")

        except json.JSONDecodeError:
            print_with_timestamp(f"Failed to decode JSON from message: {message.payload}")
        except KeyError as e:
            print_with_timestamp(f"Key error: {e}")

# Create two MQTT clients
client1 = mqtt.Client(client_id=client_id_1, protocol=mqtt.MQTTv311, clean_session=False)
client2 = mqtt.Client(client_id=client_id_2, protocol=mqtt.MQTTv5)

client1.user_data_set({"topic": TOPIC_1})
client2.user_data_set({"topic": TOPIC_2})

client1.on_connect = on_connect
client2.on_connect = on_connect
client1.on_message = on_message
client2.on_message = on_message

# SSL/TLS setup for second broker
client2.username_pw_set(USERNAME_2, PASSWORD_2)
client2.tls_set()

# Function to handle connection retries
def connect_with_retry(client, broker, port):
    while True:
        try:
            print_with_timestamp(f"Attempting to connect to MQTT broker {broker} on port {port}...")
            client.connect(broker, port)
            break
        except (socket.gaierror, socket.error) as e:
            print_with_timestamp(f"Connection failed: {e}. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)

# Start the clients
client1.loop_start()
client2.loop_start()

# Connect to brokers
connect_with_retry(client1, BROKER_1, PORT_1)
connect_with_retry(client2, BROKER_2, PORT_2)

# client1.subscribe(TOPIC_1)
# client2.subscribe(TOPIC_2)

while True:
    print_with_timestamp("Script running...")
    time.sleep(8)  # Sleep for 8 seconds before printing status

# Monitor connection status and reconnect if needed
while True:
    if not client1.is_connected():
        print_with_timestamp("Disconnected from broker 1. Attempting to reconnect...")
        connect_with_retry(client1, BROKER_1, PORT_1)

    if not client2.is_connected():
        print_with_timestamp("Disconnected from broker 2. Attempting to reconnect...")
        connect_with_retry(client2, BROKER_2, PORT_2)

    time.sleep(2)
