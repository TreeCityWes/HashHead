import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os


url1 = "http://xenminer.mooo.com/leaderboard"
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
total_blocks_response = requests.get(total_blocks_url)
if total_blocks_response.status_code == 200:
    try:
        total_blocks_data = total_blocks_response.json()
        network_stats['Total Blocks'] = total_blocks_data.get('total_blocks_top100', '0')
    except json.JSONDecodeError:
        print("Error decoding JSON from /total_blocks endpoint")
else:
    print(f"Error: Received status code {total_blocks_response.status_code} from /total_blocks endpoint")

for soup in [soup1, soup2]:
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        text = heading.text.strip()
        if ':' in text:
            parts = text.split(':')
            key = parts[0].strip()
            value = ':'.join(parts[1:]).strip()
            network_stats[key] = value
        elif 'Current miners' in text and 'Current difficulty' in text:
            # Split the text into two parts for 'Current miners' and 'Current difficulty'
            miners, difficulty = text.split('Current difficulty:')
            network_stats['Current miners'] = miners.replace('Current miners', '').strip()
            network_stats['Current difficulty'] = difficulty.strip()
        elif 'Current miners' in text:
            network_stats['Current miners'] = text.replace('Current miners', '').strip()
        elif 'Current difficulty' in text:
            network_stats['Current difficulty'] = text.replace('Current difficulty', '').strip()


for key, value in network_stats.items():
    print(f"{key}: {value}")

# Write data to files
with open('network_stats.json', 'w') as f:
    json.dump(network_stats, f, indent=4)

account_data = account_data[:25000] + [{'account': entry['account'], 'status': 'Out of top 25000'} for entry in account_data[25000:]]
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
account_output_data = {'timestamp': timestamp, 'data': account_data}

with open('accounts.json', 'w') as f:
    json.dump(account_output_data, f, indent=4)
