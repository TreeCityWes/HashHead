import requests
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API endpoints
LEADERBOARD_API = 'https://explorer.xenblocks.io/api/leaderboard?limit=10000'
STATS_API = 'https://explorer.xenblocks.io/api/stats'

# Function to fetch data from API
def fetch_api_data(url):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from {url}: {e}")
        return None

# Fetch leaderboard data
leaderboard_data = fetch_api_data(LEADERBOARD_API)

# Fetch stats data
stats_data = fetch_api_data(STATS_API)

if leaderboard_data is None or stats_data is None:
    logging.error("Failed to fetch required data. Exiting.")
    exit(1)

# Process network stats
network_stats = {
    'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    'Total Blocks': str(stats_data.get('totalBlocks', 0)),
    'Mining Blockrate': f"{stats_data.get('blockRate', 0)} BLOCKS PER MINUTE",
    'Current miners': str(stats_data.get('activeMiners', 0)),
    'Current difficulty': str(stats_data.get('difficulty', 0))
}

# Process account data
account_data = []
for entry in leaderboard_data:
    account_data.append({
        'rank': entry['rank'],
        'account': entry['address'],
        'total_blocks': entry['totalBlocks'],
        'super_blocks': entry['superBlocks'],
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

# Write network stats to file
with open('network_stats.json', 'w') as f:
    json.dump(network_stats, f, indent=4)

# Write account data to file
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
account_output_data = {'timestamp': timestamp, 'data': account_data}
with open('accounts.json', 'w') as f:
    json.dump(account_output_data, f, indent=4)

logging.info("Data scraping and writing completed successfully.")
