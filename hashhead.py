import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

access_token = os.getenv('ACCESS_TOKEN')

# Define the URLs
url1 = "http://xenminer.mooo.com:4448/leaderboard"
url2 = "http://xenminer.mooo.com/leaderboard"
total_blocks_url = "http://xenminer.mooo.com/total_blocks"  
url_xuni = "http://xenminer.mooo.com/get_xuni_counts"


# Send HTTP request and parse the HTML content of the page with BeautifulSoup
response1 = requests.get(url1)
response2 = requests.get(url2)
soup1 = BeautifulSoup(response1.text, 'html.parser')
soup2 = BeautifulSoup(response2.text, 'html.parser')

# Initialize a list to store the account data
account_data = []

# Fetch Xuni Counts
response_xuni = requests.get(url_xuni)
xuni_counts = {}
if response_xuni.status_code == 200:
    try:
        xuni_data = response_xuni.json()
        xuni_counts = {entry['account']: entry['count'] for entry in xuni_data}
    except json.JSONDecodeError:
        print("Error decoding JSON from /get_xuni_counts endpoint")

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
# After fetching the account_data, append the Xuni Counts
for entry in account_data:
    account = entry.get('account', '')
    entry['total_xuni'] = xuni_counts.get(account, '0')


# Extract Network Stats
network_stats = {}

# Add timestamp
network_stats['timestamp'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

# Send GET request to get total_blocks
total_blocks_response = requests.get(total_blocks_url)

if total_blocks_response.status_code == 200:
    try:
        total_blocks_data = total_blocks_response.json()
        network_stats['Total Blocks'] = total_blocks_data.get('total_blocks_top100', '0')
    except json.JSONDecodeError:
        print("Error decoding JSON from /total_blocks endpoint")
else:
    print(f"Error: Received status code {total_blocks_response.status_code} from /total_blocks endpoint")

# Extracting other stats from both soup1 and soup2
for soup in [soup1, soup2]:
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        text = heading.text.strip()
        if heading.name == 'h4':
            parts = text.split('Current difficulty:')
            network_stats['Current miners'] = parts[0].replace('Current miners:', '').strip()
            if len(parts) > 1:
                network_stats['Current difficulty'] = parts[1].strip()
        else:
            key, value = text.split(':') if ':' in text else (text, None)
            network_stats[key.strip()] = value.strip() if value else None

# Write the network stats to a separate JSON file
with open('network_stats.json', 'w') as f:
    json.dump(network_stats, f, indent=4)
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
        if rank <= 5000:
            account_data.append({
                'rank': rank,
                'account': account,
                'total_blocks': total_blocks,
                'super_blocks': super_blocks,
                'total_hashes_per_second': total_hashes_per_second,
                'daily_blocks': 'Sub-500 Rank'
            })

account_data = account_data[:5000] + [{'account': entry['account'], 'status': 'Out of top 5000'} for entry in account_data[5000:]]
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
account_output_data = {'timestamp': timestamp, 'data': account_data}

with open('accounts.json', 'w') as f:
    json.dump(account_output_data, f, indent=4)
