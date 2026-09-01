# for importing from 6 Geolux Hydrostations through API. you have to have an API key to be generated inside hydroview
import os
import requests
import csv
from datetime import datetime, timedelta
import time
import urllib3
import logging
from logging.handlers import RotatingFileHandler

#should be same or +1 the scan interval in hydroview
scan_interval = 15 #in minutes

#amount of data to process in minutes, should be as low as possible
dataintrvl = 30 #in minutes

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# List of dataloggers with URLs, tokens, and site numbers
dataloggers = [
    #Site 2: 
    {
        "url": "https://hydro-view.com/api/v1/data/export?site_id=(site 2 id)&measurements=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15&time_format=text",
        "auth_token": "Bearer (auth token)",
        "site_name": "02_SN",
    },
    #Site 4: 
    {
        "url": "https://hydro-view.com/api/v1/data/export?site_id=(site 4 id)&measurements=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15&time_format=text",
        "auth_token": "Bearer (auth token)",
        "site_name": "04_SN",
    },
    #Site 6: 
    {
        "url": "https://hydro-view.com/api/v1/data/export?site_id=(site 6 id)&measurements=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15&time_format=text",
        "auth_token": "Bearer (auth token)",
        "site_name": "06_SN",
    },
    #Site 8: 
    {
        "url": "https://hydro-view.com/api/v1/data/export?site_id=(site 8 id)&measurements=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15&time_format=text",
        "auth_token": "Bearer (auth token)",
        "site_name": "08_SN",
    },
    #Site 10: 
    {
        "url": "https://hydro-view.com/api/v1/data/export?site_id=(site 10 id)&measurements=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15&time_format=text",
        "auth_token": "Bearer (auth token)",
        "site_name": "10_SN",
    },
    #Site 12: 
    {
        "url": "https://hydro-view.com/api/v1/data/export?site_id=(site 12 id)&measurements=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15&time_format=text",
        "auth_token": "Bearer (auth token)",
        "site_name": "12_SN",
    },    
    # Add more dataloggers here with correct `site_number`, `site_id`, and `auth_token`
]

# Function to print with timestamp
def print_with_timestamp(message):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

# Define the path to save the files including logfile
save_folder = r"C:\Users\administrator\Desktop\httpget_csv_data"
# save_folder = r"X:\Users\Administrator\Desktop\httpget_csv_data"
log_file = os.path.join(save_folder, 'httpget_connect_csv.log')
os.makedirs(save_folder, exist_ok=True)

# Set up logging with rotation (10MB max per file, keeping 5 backups)
logging.basicConfig(
    handlers=[RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)],  # 10MB max size
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Mapping for special measurement renaming
measurement_renames = {
    11: "SNR Velocity",
    14: "SNR Level"
}

#while True:
def run_dataloggers():
    now = datetime.now().astimezone()

    logging.info(f"Running data retrieval at {now}")
    print_with_timestamp(f"Running data retrieval at {now}")
    start_time = int((now - timedelta(minutes=dataintrvl)).timestamp()) #default use dataintrvl
    #start_time = int((now - timedelta(hours=24)).timestamp()) #backfill 1 day
    #start_time = int((now - timedelta(hours=200)).timestamp()) #backfill 1 week
    #end_time = int((now - timedelta(hours=4464)).timestamp())
    end_time = int(now.timestamp())

    for datalogger in dataloggers:
        url = f"{datalogger['url']}&start={start_time}&end={end_time}"
        headers = {
            "Authorization": datalogger["auth_token"]
        }

        try:
            response = requests.get(url, headers=headers, verify=False)

            if response.status_code == 200:
                # Define the filename and save path
                file_name = f"data_{datalogger['site_name']}.csv"
                save_path = os.path.join(save_folder, file_name)

                # Convert response content to text for processing
                content = response.content.decode('utf-8')
                lines = content.splitlines()

                # Prepare CSV reader and writer
                reader = csv.reader(lines)
                rows = list(reader)

                # Extract headers and rename based on measurements
                headers = rows[0]
                measurement_ids = [int(x) for x in url.split("measurements=")[1].split("&")[0].split(',')]

                for i, measurement_id in enumerate(measurement_ids):
                    if measurement_id in measurement_renames:
                        headers[i] = measurement_renames[measurement_id]

                # Adjust the timestamp by adding 8 hours
                for row in rows[1:]:
                    row[0] = (datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

                # Write the modified content to the new CSV
                with open(save_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(rows)

                logging.info(f"CSV file saved to: {save_path}")
                print_with_timestamp(f"CSV file saved to: {save_path}")

            elif response.status_code == 403:
                logging.error(f"Access forbidden: Check your Authorization token and site_id for {datalogger['site_name']}.")
                print_with_timestamp(f"Access forbidden: Check your Authorization token for {datalogger['site_name']}.")
            else:
                logging.error(f"Failed to retrieve data for {datalogger['site_name']}. Status code: {response.status_code}")
                print_with_timestamp(f"Failed to retrieve data for {datalogger['site_name']}. Status code: {response.status_code}")

        except Exception as e:
            logging.error(f"An error occurred for {datalogger['site_name']}: {str(e)}")
            print_with_timestamp(f"An error occurred for {datalogger['site_name']}: {str(e)}")
  
def wait_until_next_interval():
    now = datetime.now()
    # Round up to the next 15-minute mark
    next_minute = ((now.minute // scan_interval) + 1) * scan_interval
    # Handle wrap-around at the hour or midnight
    next_time = now.replace(second=0, microsecond=0)

    if next_minute >= 60:
        next_time = next_time.replace(minute=0) + timedelta(hours=1)
    else:
        next_time = next_time.replace(minute=next_minute)

    wait_time = (next_time - now).total_seconds()

    print(f"Next interval at: {next_time} (waiting {wait_time:.2f} seconds)")
    logging.info(f"Next interval at: {next_time} (waiting {wait_time:.2f} seconds)")
    time.sleep(wait_time)

while True:
    try:
        run_dataloggers()
        wait_until_next_interval()
    except Exception as e:
        logging.error(f"An error occurred in the main loop: {str(e)}")
        print_with_timestamp(f"An error occurred in the main loop: {str(e)}")
