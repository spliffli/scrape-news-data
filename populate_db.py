from bs4 import BeautifulSoup
import pandas as pd

soup = BeautifulSoup(open("./economic-calendar-table.html", encoding="utf8"), "html.parser")

table = soup.table
table_rows = table.find_all('tr')

events = table.find_all(class_='js-event-item')

print(events)
print("--------------------------------")
print(events[0])

events_list = {}

for event in events:
    data_event_datetime = event['data-event-datetime']
    event_attr_id = event['event_attr_id']
    event_title = event.find(class_='event').text

    print(event_title + " | " + data_event_datetime + " | " + event_attr_id)

    events_list[event_attr_id] = {
        "event-title": event_title,
        "data-event-datetime": data_event_datetime,
        "event-attr-id": event_attr_id
    }

unique_events = {}

for event in events_list.items():
    if event[1]['event-attr-id'] not in unique_events:
        unique_events[event[1]['event-attr-id']] = event

breakpoint()
