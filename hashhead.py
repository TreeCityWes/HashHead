import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to create a session
def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Fetch environment variables or use default values
URL = os.getenv('URL', 'https://explorer.xenblocks.io/leaderboard?limit=10000')

# Create a session
session = create_session()

# Send HTTP request and parse the HTML content of the page with BeautifulSoup
try:
    response = session.get(URL, timeout=30)  # Increased timeout for larger dataset
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching data: {e}")
    raise

# Extract Network Stats
network_stats = {}
network_stats['timestamp'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

stats_boxes = soup.select('.stats-box')
for box in stats_boxes:
    title = box.select_one('.title').text.strip()
    value = box.select_one('.value').text.strip()
    if title == 'TOTAL BLOCKS':
        network_stats['Total Blocks'] = value
    elif title == 'MINING BLOCKRATE':
        network_stats['Mining Blockrate'] = f"{value} BLOCKS PER MINUTE"
    elif title == 'CURRENT MINERS':
        network_stats['Current miners'] = value
    elif title == 'CURRENT DIFFICULTY':
        network_stats['Current difficulty'] = value

# Initialize a list to store the account data
account_data = []

# Extract and Process Account Data
for row in soup.select('table tr')[1:]:  # Skip header row
    cols = row.select('td')
    if not cols or len(cols) < 4:
        continue
    rank = int(cols[0].text.strip())
    account = cols[1].text.strip()
    total_blocks = int(cols[2].text.strip().replace(',', ''))
    super_blocks = int(cols[3].text.strip().replace(',', ''))
    
    entry = {
        'rank': rank,
        'account': account,
        'total_blocks': total_blocks,
        'super_blocks': super_blocks,
        'daily_blocks': 'Sub-500 Rank',
        'total_hashes_per_second': 'N/A',
        'total_xuni': '(Coming Soon)'
    }
    account_data.append(entry)

# Ensure we have exactly 25,000 entries
if len(account_data) < 25000:
    for i in range(len(account_data), 25000):
        account_data.append({
            'account': f'placeholder_{i}',
            'status': 'Out of top 25000'
        })
elif len(account_data) > 25000:
    account_data = account_data[:25000]

for key, value in network_stats.items():
    logging.info(f"{key}: {value}")

# Write data to files
with open('network_stats.json', 'w') as f:
    json.dump(network_stats, f, indent=4)

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
account_output_data = {'timestamp': timestamp, 'data': account_data}

with open('accounts.json', 'w') as f:
    json.dump(account_output_data, f, indent=4)

logging.info("Data scraping and writing completed successfully.")
