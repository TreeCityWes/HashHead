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

# Function to create a session with retries
def create_session_with_retries():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Fetch environment variables or use default values
URL1 = os.getenv('URL1', 'http://xenblocks.io/leaderboard')
URL2 = os.getenv('URL2', 'http://xenblocks.io/leaderboard')
TOTAL_BLOCKS_URL = os.getenv('TOTAL_BLOCKS_URL', 'http://xenblocks.io/total_blocks')
URL_XUNI = os.getenv('URL_XUNI', 'http://xenblocks.io/get_xuni_counts')

# Create a session with retries
session = create_session_with_retries()

# Send HTTP request and parse the HTML content of the page with BeautifulSoup
try:
    response1 = session.get(URL1)
    response2 = session.get(URL2)
    response1.raise_for_status()
    response2.raise_for_status()
    soup1 = BeautifulSoup(response1.text, 'html.parser')
    soup2 = BeautifulSoup(response2.text, 'html.parser')
except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching data: {e}")
    raise

# Initialize a list to store the account data
account_data = []

# Fetch Xuni Counts
xuni_counts = {}
try:
    response_xuni = session.get(URL_XUNI)
    response_xuni.raise_for_status()
    xuni_data = response_xuni.json()
    xuni_counts = {entry['account']: entry['count'] for entry in xuni_data}
except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching Xuni counts: {e}")
except json.JSONDecodeError:
    logging.error("Error decoding JSON from /get_xuni_counts endpoint")

# Extract and Process Account Data from the first URL
for row in soup1.select('table tr')[1:]:
    cols = row.select('td')
    if not cols:
        continue
    rank = int(cols[0].text.strip())
    account = cols[1].text.strip()
    total_blocks = int(cols[2].text.strip())
    super_blocks = int(cols[3].text.strip())
    daily_blocks = cols[4].text.strip()
    account_data.append({
        'rank': rank,
        'account': account,
        'total_blocks': total_blocks,
        'super_blocks': super_blocks,
        'daily_blocks': daily_blocks
    })

# Extract and Process Account Data from the second URL
for row in soup2.select('table tr')[1:]:
    cols = row.select('td')
    if not cols:
        continue
    rank = int(cols[0].text.strip())
    account = cols[1].text.strip()
    total_blocks = int(cols[2].text.strip())
    super_blocks = int(cols[3].text.strip())
    total_hashes_per_second = cols[4].text.strip()

    for entry in account_data:
        if entry['account'] == account:
            entry['total_hashes_per_second'] = total_hashes_per_second
            break
    else:
        if rank <= 25000:
            account_data.append({
                'rank': rank,
                'account': account,
                'total_blocks': total_blocks,
                'super_blocks': super_blocks,
                'total_hashes_per_second': total_hashes_per_second,
                'daily_blocks': 'Sub-500 Rank'
            })

# Update the Xuni Counts for all accounts
for entry in account_data:
    account = entry.get('account', '')
    entry['total_xuni'] = xuni_counts.get(account, '0')

# Extract Network Stats
network_stats = {}
network_stats['timestamp'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
try:
    total_blocks_response = session.get(TOTAL_BLOCKS_URL)
    total_blocks_response.raise_for_status()
    total_blocks_data = total_blocks_response.json()
    network_stats['Total Blocks'] = total_blocks_data.get('total_blocks_top100', '0')
except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching total blocks: {e}")
except json.JSONDecodeError:
    logging.error("Error decoding JSON from /total_blocks endpoint")

for soup in [soup1, soup2]:
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        text = heading.text.strip()
        if 'Current miners' in text and 'Current difficulty' in text:
            # Split the text into two parts for 'Current miners' and 'Current difficulty'
            miners_part, difficulty_part = text.split('Current difficulty:')
            # Extract the number of miners
            miners_number = miners_part.split('Current miners:')[1].strip()
            # Extract the difficulty value
            difficulty_number = difficulty_part.strip()
            network_stats['Current miners'] = miners_number
            network_stats['Current difficulty'] = difficulty_number
        elif ':' in text:
            parts = text.split(':')
            key = parts[0].strip()
            value = ':'.join(parts[1:]).strip()
            network_stats[key] = value

for key, value in network_stats.items():
    logging.info(f"{key}: {value}")

# Write data to files
with open('network_stats.json', 'w') as f:
    json.dump(network_stats, f, indent=4)

account_data = account_data[:25000] + [{'account': entry['account'], 'status': 'Out of top 25000'} for entry in account_data[25000:]]
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
account_output_data = {'timestamp': timestamp, 'data': account_data}

with open('accounts.json', 'w') as f:
    json.dump(account_output_data, f, indent=4)
