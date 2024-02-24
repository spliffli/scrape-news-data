import influxdb_client_3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import warnings
import chromedriver_autoinstaller_fix
import pandas as pd
import sys
import time
from datetime import datetime, timezone
import pytz
import re
from influxdb_client_3 import InfluxDBClient3, Point
from influxdb_client_3.write_client.client.write_api import SYNCHRONOUS
import os
from datetime import datetime

bucket = "News Data"
with open('influxdb-token.txt', 'r') as file:
    token = file.read()
org = "Scraped News Data"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"

client = InfluxDBClient3(host=host, token=token, org=org)


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
    print("Expanding table...")
    no_new_data_count = 0
    while True:
        rows_count_before = len(table.find_elements(By.XPATH, ".//tbody/tr"))
        driver.execute_script(f"ecEvent.moreHistory({event_attr_id}, this, 0)")  # JavaScript to expand the table
        time.sleep(0.5)
        rows_count_after = len(table.find_elements(By.XPATH, ".//tbody/tr"))

        if rows_count_after == rows_count_before:
            no_new_data_count += 1

        if no_new_data_count == 5:
            break

    return


def get_datetime(release_date: str, release_time: str):
    if ' (' in release_date:
        release_date = release_date.split(" (")[0]

    # !CAUSES CRASH
    dt = datetime.strptime(f"{release_date} {release_time}".strip() + " -0500", "%b %d, %Y %H:%M %z")
    return dt


def calc_deviation(forecast, actual):
    forecast = re.findall(r'\d+', forecast)
    if len(forecast) == 0:
        forecast = None
    elif len(forecast) == 1:
        forecast = forecast[0]
    elif len(forecast) == 2:
        forecast = float(forecast[0] + "." + forecast[1])
    else:
        raise ValueError("Invalid forecast number")

    actual = re.findall(r'\d+', actual)
    if len(actual) == 0:
        actual = None
    elif len(actual) == 1:
        actual = actual[0]
    elif len(actual) == 2:
        actual = float(actual[0] + "." + actual[1])
    else:
        raise ValueError("Invalid actual number")

    if forecast is not None and actual is not None:
        deviation = actual - forecast
    else:
        deviation = None

    return deviation


def scrape_all_table_values(driver, table):
    # Initialize variables
    df = pd.DataFrame(
        columns=['datetime-utc', 'prelim', 'actual', 'forecast', 'previous', 'datetime-cet', 'datetime-gmt',
                 'datetime-est', 'timestamp'])
    row_count = len(table.find_elements(By.XPATH, ".//tbody/tr"))
    current_row = 0

    # Iterate through the table and find the values for each column
    for row in table.find_elements(By.XPATH, ".//tbody/tr"):
        # print(row.find_element(By.XPATH, "./td[1]").text)
        current_row += 1
        print(f"scraping row {current_row}/{row_count}", end="\r", flush=True)
        release_date = row.find_element(By.XPATH, "./td[1]").text
        release_time = row.find_element(By.XPATH, "./td[2]").text

        # The default timezone on investing.com is EST so all datetimes are converted to UTC & CET
        datetime_est = get_datetime(release_date, release_time).astimezone(pytz.timezone('US/Eastern'))
        datetime_utc = datetime_est.astimezone(pytz.timezone('UTC'))
        datetime_gmt = datetime_est.astimezone(pytz.timezone('GMT'))
        datetime_cet = datetime_est.astimezone(pytz.timezone('CET'))

        timestamp_seconds = datetime_utc.timestamp()
        timestamp_nanoseconds = timestamp_seconds * 1000




        if row.find_elements(By.XPATH, "./td[2]/span[@class='smallGrayP']"):
            prelim = True
        else:
            prelim = False

        try:
            actual = row.find_element(By.XPATH, "./td[3]/span").text
        except NoSuchElementException:
            actual = None
        try:
            forecast = row.find_element(By.XPATH, "./td[4]").text
        except NoSuchElementException:
            forecast = None
        try:
            previous = row.find_element(By.XPATH, "./td[5]").text
        except NoSuchElementException:
            previous = None

        if actual is not None and forecast is not None:
            deviation = calc_deviation(forecast, actual)
        else:
            deviation = None

        df = df._append({
            "datetime-utc": datetime_utc,
            "prelim": prelim,
            "actual": actual,
            "forecast": forecast,
            "deviation": deviation,
            "previous": previous,
            "datetime-cet": datetime_cet,
            "datetime-gmt": datetime_gmt,
            "datetime-est": datetime_est,
            "timestamp_ns": timestamp_nanoseconds
        }, ignore_index=True)

    print("\n")

    return df


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

    event_title = driver.find_element(By.CLASS_NAME, "ecTitle").text

    table = driver.find_element(By.ID, f"eventHistoryTable{event_attr_id}")
    expand_table_until_beginning_of_data(driver, table, event_attr_id)
    table_df = scrape_all_table_values(driver, table)

    print("\n" + event_title + ": \n")
    print(table_df)
    print("--------------------------------")

    driver.close()

    return table_df, event_title


def successful_write_callback(self, data):
    print(f"{data}")
    print(f"WRITE FINISHED")


def extract_data_from_table(html_table):
    soup = BeautifulSoup(html_table, "html.parser")

    table = soup.table
    table_rows = table.find_all('tr')

    events = table.find_all(class_='js-event-item')

    print(events)
    print("--------------------------------")
    print(events[0])

    events_list = {}

    for event_id in events:
        indicator_title = event_id.find(class_='event').text.strip()
        data_event_datetime = event_id['data-event-datetime']
        event_attr_id = event_id['event_attr_id']
        importance_stars = len(event_id.find_all('i', class_='grayFullBullishIcon'))
        country = event_id.find('td', class_='flagCur').find('span', class_='ceFlags').attrs['data-img_key']
        underlying_currency = event_id.find('td', class_='flagCur').text.strip()
        trading_symbols = get_trading_symbols(underlying_currency)

        print(data_event_datetime + " | " + event_attr_id + " | " + indicator_title)

        events_list[event_attr_id] = {
            "event-title": indicator_title,
            "data-event-datetime": data_event_datetime,
            "event-attr-id": event_attr_id,
            "importance-stars": importance_stars,
            "country": country,
            "underlying-currency": underlying_currency,
            "trading-symbols": trading_symbols,
        }

    unique_events = {}

    for event_id in events_list.items():
        if event_id[1]['event-attr-id'] not in unique_events:
            unique_events[event_id[1]['event-attr-id']] = event_id

    for event_id in unique_events:

        scraped_data_df, indicator_title = scrape_historic_indicator_data(event_id)
        breakpoint()

        points = []

        json_body = []

        for index, row in scraped_data_df.iterrows():

            json_body.append({
                "measurement": "news_data",
                "tags": {
                    "event_attr_id": event_id,
                    "indicator_title": indicator_title
                },
                "time": int(row['timestamp_ns']),
                "fields": {
                    "prelim": row['prelim'],
                    "forecast": row['forecast'],
                    "actual": row['actual'],
                    "deviation": row['deviation'],
                    "previous": row['previous'],
                    "push_timestamp": int(datetime.utcnow().timestamp()),
                }
            })

            response = client.write(database="News Data",
                                    record=json_body)

            """
            # Returns None for some reason & no data is written. Stepping into the code reveals it's a 204 http error
            write_http_status = client.write(database="News Data",
                                             record=point,
                                             write_precision='s',
                                             write_options=SYNCHRONOUS)
            """

            breakpoint()



extract_data_from_table(open("./economic-calendar-table.html", encoding="utf8"))

#testing testing testing
