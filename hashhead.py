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

# New leaderboard URL for top 10,000 entries
LEADERBOARD_URL = os.getenv('LEADERBOARD_URL', 'https://explorer.xenblocks.io/leaderboard?limit=10000')

# Create a session
session = create_session()

# Send HTTP request and parse the HTML content of the page with BeautifulSoup
try:
    response = session.get(LEADERBOARD_URL, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching data: {e}")
    raise

# Initialize a list to store the account data
account_data = []

# Extract and Process Account Data from the leaderboard
# Assuming the leaderboard is a table similar to before
for row in soup.select('table tbody tr'):
    cols = row.select('td')
    if not cols:
        continue

    # Extract the data from the row
    rank = int(cols[0].text.strip())       # Rank of the miner
    account = cols[1].text.strip()         # ETH Address (Account)
    total_blocks = int(cols[2].text.strip())  # Total blocks mined
    super_blocks = int(cols[3].text.strip())  # Super blocks mined

    # Add this account's data to the list
    account_data.append({
        'rank': rank,
        'account': account,
        'total_blocks': total_blocks,
        'super_blocks': super_blocks,
        'total_xuni': '(Coming Soon)'  # Placeholder for Xuni
    })

# Extract Network Stats (if present in the HTML)
network_stats = {}
network_stats['timestamp'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

try:
    for stat in soup.select('.stat'):
        stat_title = stat.select_one('.stat-title').text.strip().lower()
        stat_value = stat.select_one('.stat-value').text.strip()

        if 'total blocks' in stat_title:
            network_stats['Total Blocks'] = stat_value
        elif 'mining blockrate' in stat_title:
            network_stats['Mining Blockrate'] = stat_value
        elif 'current miners' in stat_title:
            network_stats['Current Miners'] = stat_value
        elif 'current difficulty' in stat_title:
            network_stats['Current Difficulty'] = stat_value
except Exception as e:
    logging.error(f"Error parsing stats: {e}")

# Log the extracted network stats
for key, value in network_stats.items():
    logging.info(f"{key}: {value}")

# Write the network stats to a JSON file
with open('network_stats.json', 'w') as f:
    json.dump(network_stats, f, indent=4)

# Limit the account data to 10,000 and add status for entries out of range (if needed)
account_data = account_data[:10000] + [{'account': entry['account'], 'status': 'Out of top 10000'} for entry in account_data[10000:]]

# Create a timestamp for the export
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
account_output_data = {'timestamp': timestamp, 'data': account_data}

# Write the account data to a JSON file
with open('accounts.json', 'w') as f:
    json.dump(account_output_data, f, indent=4)
