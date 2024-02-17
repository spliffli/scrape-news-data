from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import warnings
import chromedriver_autoinstaller_fix
import pandas as pd
import time
from datetime import datetime, timezone
import pytz


def get_trading_symbols(underlying_currency):
    match underlying_currency:
        case 'USD':
            symbols = ['USDJPY', 'XAUUSD']
        case 'CAD':
            symbols = ['USDCAD']
        case 'EUR':
            symbols = ['EURUSD']
        case 'AUD':
            symbols = ['AUDUSD']
        case 'NZD':
            symbols = ['NZDUSD']
        case 'MXN':
            symbols = ['MXNUSD']
        case 'CHF':
            symbols = ['USDCHF']
        case 'PLN':
            symbols = ['USDPLN']
        case 'GBP':
            symbols = ['GBPUSD']
        case 'SEK':
            symbols = ['USDSEK']
        case 'NOK':
            symbols = ['USDNOK']
        case 'TRY':
            symbols = ['USDTRY']

    return symbols


def expand_table_until_beginning_of_data(driver, table, event_attr_id):
    while True:
        rows_count_before = len(table.find_elements(By.XPATH, ".//tbody/tr"))
        driver.execute_script(f"ecEvent.moreHistory({event_attr_id}, this, 0)")  # JavaScript to expand the table
        time.sleep(0.5)
        rows_count_after = len(table.find_elements(By.XPATH, ".//tbody/tr"))
        if rows_count_after == rows_count_before:
            break

    return


def get_datetime(release_date: str, release_time: str):
    if ' (' in release_date:
        release_date = release_date.split(" (")[0]

    # !CAUSES CRASH
    dt = datetime.strptime(f"{release_date} {release_time}".strip() + " -0500", "%b %d, %Y %H:%M %z")
    return dt


def scrape_all_table_values(driver, table):
    df = pd.DataFrame(columns=['Date', 'Time (ET)' 'Prelim', 'Actual', 'Forecast', 'Previous'])
    row_count = len(table.find_elements(By.XPATH, ".//tbody/tr"))
    current_row = 0
    for row in table.find_elements(By.XPATH, ".//tbody/tr"):
        # print(row.find_element(By.XPATH, "./td[1]").text)
        current_row += 1
        print(f"scraping row {current_row}/{row_count}")
        release_date = row.find_element(By.XPATH, "./td[1]").text
        release_time = row.find_element(By.XPATH, "./td[2]").text
        datetime_et = get_datetime(release_date, release_time).astimezone(pytz.timezone('US/Eastern'))
        datetime_utc = datetime_et.astimezone(pytz.timezone('UTC'))
        datetime_cet = datetime_et.astimezone(pytz.timezone('CET'))

        if row.find_elements(By.XPATH, "./td[2]/span[@class='smallGrayP']"):
            prelim = True
        else:
            prelim = False




def scrape_historic_indicator_data(event_attr_id):
    warnings.simplefilter(action='ignore', category=FutureWarning)
    chromedriver_autoinstaller_fix.install()
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    # options.add_argument("--headless")  # hide GUI
    # options.add_argument("--window-size=1920,1080")  # set window size to native GUI size
    options.add_argument("start-maximized")  # ensure window is full-screen
    options.add_experimental_option("prefs",
                                    {"profile.managed_default_content_settings.images": 2})  # Load without images
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://www.investing.com/economic-calendar/" + event_attr_id)

    table = driver.find_element(By.ID, f"eventHistoryTable{event_attr_id}")
    expand_table_until_beginning_of_data(driver, table, event_attr_id)
    scrape_all_table_values(driver, table)
    breakpoint()


def extract_data_from_table(html_table):
    soup = BeautifulSoup(html_table, "html.parser")

    table = soup.table
    table_rows = table.find_all('tr')

    events = table.find_all(class_='js-event-item')

    print(events)
    print("--------------------------------")
    print(events[0])

    events_list = {}



    for event in events:
        event_title = event.find(class_='event').text.strip()
        data_event_datetime = event['data-event-datetime']
        event_attr_id = event['event_attr_id']
        importance_stars = len(event.find_all('i', class_='grayFullBullishIcon'))
        country = event.find('td', class_='flagCur').find('span', class_='ceFlags').attrs['data-img_key']
        underlying_currency = event.find('td', class_='flagCur').text.strip()
        trading_symbols = get_trading_symbols(underlying_currency)

        print(data_event_datetime + " | " + event_attr_id + " | " + event_title)

        events_list[event_attr_id] = {
            "event-title": event_title,
            "data-event-datetime": data_event_datetime,
            "event-attr-id": event_attr_id,
            "importance-stars": importance_stars,
            "country": country,
            "underlying-currency": underlying_currency,
            "trading-symbols": trading_symbols,
        }

    unique_events = {}

    for event in events_list.items():
        if event[1]['event-attr-id'] not in unique_events:
            unique_events[event[1]['event-attr-id']] = event

    for event in unique_events:
        scraped_data = scrape_historic_indicator_data(event)
        breakpoint()


extract_data_from_table(open("./economic-calendar-table.html", encoding="utf8"))
