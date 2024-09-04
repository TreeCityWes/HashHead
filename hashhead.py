import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to create a session
def create_session():
    session = requests.Session()
    return session

# Fetch environment variables or use default values
URL = os.getenv('URL', 'https://explorer.xenblocks.io/leaderboard')

# Create a session
session = create_session()

# Send HTTP request and parse the HTML content of the page with BeautifulSoup
try:
    response = session.get(URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching data: {e}")
    raise

# Initialize a list to store the account data
account_data = []

# Extract Network Stats
network_stats = {}
network_stats['timestamp'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

stat_boxes = soup.select('.stat')
for box in stat_boxes:
    title = box.select_one('.stat-title').text.strip()
    value = box.select_one('.stat-value').text.strip()
    if 'Total Blocks' in title:
        network_stats['Total Blocks'] = value
    elif 'Mining Blockrate' in title:
        network_stats['Mining Blockrate'] = f"{value} BLOCKS PER MINUTE"
    elif 'Current Miners' in title:
        network_stats['Current miners'] = value
    elif 'Current Difficulty' in title:
        network_stats['Current difficulty'] = value

# Extract and Process Account Data
table = soup.select_one('table')
if table:
    rows = table.select('tbody tr')
    for row in rows:
        cols = row.select('td')
        if len(cols) >= 4:
            rank = int(cols[0].text.strip())
            account = cols[1].text.strip()
            total_blocks = int(cols[2].text.strip().replace(',', ''))
            super_blocks = int(cols[3].text.strip().replace(',', ''))
            
            account_data.append({
                'rank': rank,
                'account': account,
                'total_blocks': total_blocks,
                'super_blocks': super_blocks,
                'daily_blocks': 'Sub-500 Rank',
                'total_hashes_per_second': 'N/A',
                'total_xuni': '(Coming Soon)'
            })

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
