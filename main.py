import os, time
import datetime
from selenium.webdriver.remote.webelement import WebElement
import time
import pandas as pd
import chromedriver_autoinstaller_fix
import os
import warnings
from influxdb_client_3 import InfluxDBClient3, Point
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup


def prepare_calendar(driver, custom_date=True):
    time.sleep(1)

    print("Setting filters:\nClearing all countries")
    driver.execute_script("clearAll('country[]');")

    # Click country checkboxes for USD, CAD, NOK, SEK, PLN, TRY & EUR
    print("Clicking checkboxes for USD, CAD, NOK, SEK, PLN, TRY & EUR")
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "country5"))  # USA (USD)
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "country6"))  # Canada (CAD)
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "country60"))  # Norway (NOK)
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "country9"))  # Sweden (SEK)
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "country53"))  # Poland (PLN)
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "country63"))  # Turkey (TRY)
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "country72"))  # Europe (EUR)

    # Display time only instead of remaining time until announcement
    print("Showing time only instead of remaining time until announcements")
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "timetimeOnly"))

    # Select all categories
    print("Selecting all categories")
    driver.execute_script("selectAll('category[]');")

    # Select all importance levels
    print("Selecting all importance levels")
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "importance1"))
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "importance2"))
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "importance3"))

    # Apply filters
    print("Applying filters")
    driver.execute_script("calendarFilters.innerFiltersSubmit();")

    # Close popup
    popup = None
    while popup is None:
        try:
            print("Waiting for popup...")
            popup = WebDriverWait(driver, 1,).until(EC.presence_of_element_located((By.CLASS_NAME, "signupWrap")))
        except TimeoutException:
            continue
    print("Closing popup")
    driver.execute_script("arguments[0].click();", driver.find_element(By.CLASS_NAME, "popupCloseIcon"))
    # driver.execute_script("return window.stop")

    if custom_date:
        input_str = "."

        while input_str != "":
            input_str = input("Press enter after manually selecting dates on investing.com...")


def scrape_all_inv_ids():
    pass


def run():
    warnings.simplefilter(action='ignore', category=FutureWarning)
    chromedriver_autoinstaller_fix.install()
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    # options.add_argument("--headless")  # hide GUI
    # options.add_argument("--window-size=1920,1080")  # set window size to native GUI size
    options.add_argument("start-maximized")  # ensure window is full-screen
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})  # Load without images
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://www.investing.com/economic-calendar/")
    prepare_calendar(driver)
    scrape_all_inv_ids()

run()
