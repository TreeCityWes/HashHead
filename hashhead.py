import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import datetime
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL of the leaderboard with 10,000 limit
URL = 'https://explorer.xenblocks.io/leaderboard?limit=10000'

# Setup Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = None
try:
    logging.info("Initializing WebDriver")
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)  # Set page load timeout to 60 seconds
    logging.info("WebDriver initialized successfully")

    logging.info(f"Navigating to {URL}")
    driver.get(URL)
    logging.info("Page loaded successfully")

    logging.info("Waiting for stats to load")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "stat"))
    )
    logging.info("Stats loaded successfully")

    network_stats = {
        'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    }
    stat_boxes = driver.find_elements(By.CLASS_NAME, "stat")
    logging.info(f"Found {len(stat_boxes)} stat boxes")
    for box in stat_boxes:
        title = box.find_element(By.CLASS_NAME, "stat-title").text.strip()
        value = box.find_element(By.CLASS_NAME, "stat-value").text.strip()
        logging.info(f"Stat: {title} = {value}")
        if 'Total Blocks' in title:
            network_stats['Total Blocks'] = value
        elif 'Mining Blockrate' in title:
            network_stats['Mining Blockrate'] = f"{value} BLOCKS PER MINUTE"
        elif 'Current Miners' in title:
            network_stats['Current miners'] = value
        elif 'Current Difficulty' in title:
            network_stats['Current difficulty'] = value

    logging.info("Waiting for table to load")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )
    logging.info("Table loaded successfully")

    account_data = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    logging.info(f"Found {len(rows)} rows in the table")
    for i, row in enumerate(rows):
        if i % 100 == 0:
            logging.info(f"Processing row {i}")
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

    with open('network_stats.json', 'w') as f:
        json.dump(network_stats, f, indent=4)
    logging.info("Network stats written to file")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    account_output_data = {'timestamp': timestamp, 'data': account_data}
    with open('accounts.json', 'w') as f:
        json.dump(account_output_data, f, indent=4)
    logging.info("Account data written to file")

    logging.info("Data scraping and writing completed successfully.")

except Exception as e:
    logging.error(f"An error occurred: {str(e)}")
    logging.error(traceback.format_exc())

finally:
    if driver:
        driver.quit()
        logging.info("WebDriver closed")
