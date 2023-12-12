import random
import time

import requests
from requests.auth import HTTPBasicAuth
import json
import logging
from random import choice
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

C8Y_BASEURL = 'https://xxx.eu-latest.cumulocity.com'
C8Y_TENANT = ''
C8Y_USER = ''
C8Y_PASSWORD = ''
C8Y_AUTH = HTTPBasicAuth(C8Y_TENANT + '/' + C8Y_USER, C8Y_PASSWORD)
C8Y_HEADERS = {
    'Accept': 'application/json'
}
client = requests.Session()

alarm_types = ['c8y_UnavailabilityAlarm', 'c8y_OverheatAlarm', 'c8y_OverspeedAlarm']
alarm_severties = ['MAJOR', 'CRITICAL', 'MINOR', 'WARNING']
event_types = ['c8y_OutgoingSmsLog', 'c8y_minuteAggregation', 'c8y_deviceRestart', 'c8y_deviceStop']
device_list = ['123456', '234567']

def alarms_create():
    type_alarm = choice(alarm_types)
    alarm_json = {
        "source": {
            "id": choice(device_list)
        },
        "type": type_alarm,
        "text": f"This is a {type_alarm} alarm",
        "severity": choice(alarm_severties),
        "status": "ACTIVE",
        "time": datetime.now().isoformat()[:-3]+'Z'
    }
    response = client.post(
        C8Y_BASEURL + '/alarm/alarms',
        auth=C8Y_AUTH,
        headers=C8Y_HEADERS,
        data=json.dumps(alarm_json)
    )
    if response.status_code == 201:
        logging.info('Alarm created')
    else:
        logging.error('Alarm creation failed')


def events_create():
    event_type = choice(event_types)
    event_json = {
        "source": {
            "id": choice(device_list)
        },
        "text": f"Event with type {event_type}",
        "time": datetime.now().isoformat()[:-3]+'Z',
        "type": event_type
    }
    response = client.post(
        C8Y_BASEURL + '/event/events',
        auth=C8Y_AUTH,
        headers=C8Y_HEADERS,
        data=json.dumps(event_json)
    )
    if response.status_code == 201:
        logging.info('Event created')
    else:
        logging.error('Event creation failed')


def devices_create():
    device_json = {
        "name": f"btdevice-{random.randint(10, 100)}",
        "c8y_IsDevice": {}
        }
    response = client.post(
        C8Y_BASEURL + '/inventory/managedObjects',
        auth=C8Y_AUTH,
        headers=C8Y_HEADERS,
        data=json.dumps(device_json)
    )
    if response.status_code == 201:
        device_id = response.json()['id']
        device_list.append(device_id)
        logging.info('Device created')
    else:
        logging.error('Device creation failed')


if __name__ == '__main__':
    while True:
        alarms_create()
        events_create()
        time.sleep(random.randint(3, 10))
        if datetime.now().second % 5 == 0:
            devices_create()
            time.sleep(random.randint(3, 10))