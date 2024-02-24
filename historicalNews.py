from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import os, time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from influxdb_client_3 import InfluxDBClient3

# Initialize the Chrome WebDriver
driver = webdriver.Chrome()

# Open the webpage with the date inputs
driver.get("https://uk.investing.com/economic-calendar/")

# Holday for 5 seconds to load page
time.sleep(2)

# Close Pop Ups
closePrivacy = driver.find_element(By.ID, "onetrust-accept-btn-handler")
closePrivacy.click()
print("Privacy Pop Up Closed")

# Define function for checking and closing pop ups
def closePopUp(driver):
    try:
        close_button = driver.find_element(By.CLASS_NAME, "popupCloseIcon.largeBannerCloser")
        if close_button.is_displayed():  # Check if the element is visible
            close_button.click()
            print("Closed the pop-up")
    except NoSuchElementException:
        print("No pop-up found or pop-up closed already")

# Call Close Pop Up function
closePopUp(driver)

# Define the scraping period
calendarDate = datetime.strptime("26/02/2024", "%d/%m/%Y") # Should be a Monday
calendarEnd = datetime.strptime("08/01/2024", "%d/%m/%Y") # Best to also make it a Monday


client = InfluxDBClient3(token="my8rZkaEz77qmkoxhathhKbYT4bEYB4qjJGjuktX6GI6lPZdIVWwLKMJBPfn53V67Y6Z18my-DjL7uCXGz_n0g==",
                        host="eu-central-1-1.aws.cloud2.influxdata.com",
                        database="economicCalendar",
                        org="V2")


# Loop to go back one week at a time and scrape data
while calendarDate >= calendarEnd:  # loop continues within scraping period     
    calendarWeekDate = calendarDate + timedelta(weeks=1) # Used to set the second calendar date

    # Define looped function for setting calendar operation, includes function for closing pop up.
    def set_calendar_date(driver, calendarDate):
        while True:
            try:
                closePopUp(driver)
                openCalendar = driver.find_element(By.ID, "datePickerToggleBtn")
                openCalendar.click()
                print("Calendar Opened")

                startDate = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "startDate")))
                startDate.clear()
                startDate.send_keys(calendarDate.strftime("%d/%m/%Y"))  # Format date as DD/MM/YYYY
                print("Start Date Set")

                endDate = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "endDate")))
                endDate.clear()
                endDate.send_keys(calendarWeekDate.strftime("%d/%m/%Y"))  # Format date as DD/MM/YYYY
                print("End Date Set")

                applyCalendar = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "applyBtn")))
                applyCalendar.click()
                print("Date Applied")

                break  # Break the loop if everything executed successfully
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                print("Retrying...")

    # Call Calendar Function       
    set_calendar_date(driver,calendarDate)

    # Wait for the page to update with the new data (adjust the sleep time as needed)
    time.sleep(1)

    # Get the page source after the date is applied
    page_source = driver.page_source

    # Now, parse the page source using Beautiful Soup
    soup = BeautifulSoup(page_source, "html.parser")
    
    # Find all event rows in the table
    rows = soup.find_all('tr')

    # Filter rows based on id attribute
    filtered_rows = [row for row in rows if 'eventRowId' in row.get('id', '')]

    # Process the filtered rows
    for row in filtered_rows:
        # Extract data from each cell (td) in the row
        cells = row.find_all('td')
        
        if len(cells) >= 7 and cells[0].text.strip():  # Ensure there are enough cells and time is not empty
                
            # Extract relevant data from event row
            event_datetime = row.get('data-event-datetime', '')
            event_datetime = datetime.strptime(event_datetime, "%Y/%m/%d %H:%M:%S")
            eventID = row.get('event_attr_id', '')
            
            # Extract relevant data from cells within event row
            country_cell = cells[1].find('span', class_='ceFlags')
            country = country_cell.get('title', '') if country_cell else ''
            currency = cells[1].text.strip()
            volatility_cell = cells[2]
            volatility = volatility_cell.get('title', '') if volatility_cell else ''
            event = cells[3].text.strip()
            actual = cells[4].text.strip()
            forecast = cells[5].text.strip()
            previous = cells[6].text.strip()
            timeWriteDB = datetime.now()
            
            # Assign data to point structure for InfluxDB
            points = {
                "measurement": "EconomicNews",
                "tags": {"Event": event, "Country": country, "Currency": currency, "Volatility": volatility, "Event ID": eventID, "Time of DB Write": timeWriteDB},
                "fields": {"Actual": actual, "Forecast": forecast, "Previous": previous},
                "time": event_datetime
            }

            # Write data to InfluxDB
            client.write(record=points, write_precision="s")
        
    print(calendarDate.strftime("%d-%m-%y") + " Weekly Scrape Complete")

    # Go back 7 days and start next iteration
    calendarDate -= timedelta(days=7)