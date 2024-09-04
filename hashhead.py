import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL of the leaderboard
URL = 'https://explorer.xenblocks.io/leaderboard'

# Setup Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)  # Set page load timeout to 30 seconds
    logging.info("WebDriver initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize WebDriver: {e}")
    raise

try:
    # Navigate to the page
    logging.info(f"Navigating to {URL}")
    driver.get(URL)
    logging.info("Page loaded successfully")

    # Wait for the stats to load
    logging.info("Waiting for stats to load")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "stat-box"))
    )
    logging.info("Stats loaded successfully")

    # Extract network stats
    network_stats = {
        'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    }
    stat_boxes = driver.find_elements(By.CLASS_NAME, "stat")
    for box in stat_boxes:
        title = box.find_element(By.CLASS_NAME, "stat-title").text.strip()
        value = box.find_element(By.CLASS_NAME, "stat-value").text.strip()
        if 'Total Blocks' in title:
            network_stats['Total Blocks'] = value
        elif 'Mining Blockrate' in title:
            network_stats['Mining Blockrate'] = f"{value} BLOCKS PER MINUTE"
        elif 'Current Miners' in title:
            network_stats['Current miners'] = value
        elif 'Current Difficulty' in title:
            network_stats['Current difficulty'] = value
    logging.info("Network stats extracted successfully")

    # Wait for the table to load
    logging.info("Waiting for table to load")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )
    logging.info("Table loaded successfully")

    # Extract account data
    account_data = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
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
    logging.info(f"Extracted data for {len(account_data)} accounts")

    # Ensure we have exactly 25,000 entries
    if len(account_data) < 25000:
        for i in range(len(account_data), 25000):
            account_data.append({
                'account': f'placeholder_{i}',
                'status': 'Out of top 25000'
            })
    elif len(account_data) > 25000:
        account_data = account_data[:25000]
    logging.info(f"Final account data count: {len(account_data)}")

    # Write network stats to file
    with open('network_stats.json', 'w') as f:
        json.dump(network_stats, f, indent=4)
    logging.info("Network stats written to file")

    # Write account data to file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    account_output_data = {'timestamp': timestamp, 'data': account_data}
    with open('accounts.json', 'w') as f:
        json.dump(account_output_data, f, indent=4)
    logging.info("Account data written to file")

    logging.info("Data scraping and writing completed successfully.")

except Exception as e:
    logging.error(f"An error occurred: {e}")

finally:
    driver.quit()
    logging.info("WebDriver closed")
