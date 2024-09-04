import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL of the leaderboard
URL = 'https://explorer.xenblocks.io/leaderboard'

# Function to fetch and parse the page
def fetch_and_parse(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None

# Fetch and parse the page
soup = fetch_and_parse(URL)

if soup is None:
    logging.error("Failed to fetch and parse the page. Exiting.")
    exit(1)

# Extract network stats
network_stats = {
    'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
}

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

# Extract account data
account_data = []
rows = soup.select('table tbody tr')
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

# Write network stats to file
with open('network_stats.json', 'w') as f:
    json.dump(network_stats, f, indent=4)

# Write account data to file
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
account_output_data = {'timestamp': timestamp, 'data': account_data}
with open('accounts.json', 'w') as f:
    json.dump(account_output_data, f, indent=4)

logging.info("Data scraping and writing completed successfully.")
