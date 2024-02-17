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

    return underlying_currency


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
