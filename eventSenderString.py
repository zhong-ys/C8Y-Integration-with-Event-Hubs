from azure.eventhub import EventHubProducerClient, EventData
# from azure.eventhub.aio import EventHubProducerClient

import logging
import os
import json
import websocket
import requests
from requests.auth import HTTPBasicAuth
import ssl

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EVENT_HUB_CONNECTION_STR = "ConnectionString"
EVENT_HUB_NAME = "<<EventHubName>>"

C8Y_BASEURL = 'https://xxxx.eu-latest.cumulocity.com'
C8Y_TENANT = ''
C8Y_USER = ''
C8Y_PASSWORD = ''
C8Y_AUTH = HTTPBasicAuth(C8Y_TENANT + '/' + C8Y_USER, C8Y_PASSWORD)
C8Y_HEADERS = {
    'Accept': 'application/json'
}
C8Y_BASEURL_WEBSOCKET = C8Y_BASEURL.replace('http://', 'ws://').replace('https://', 'wss://')
C8Y_SUBSCRIPTION_NAME = '<<SubscriptionName>>'
C8Y_SUBSCRIBER_NAME = '<<SubscriberName>>'
C8Y_SUBSCRIPTION_EXPIRATION_MIN = 1440
client = requests.Session()

subscription_json = {
    "context": "tenant",
    "subscription": C8Y_SUBSCRIPTION_NAME,
}

# Create subscription
response = client.post(
    C8Y_BASEURL + '/notification2/subscriptions',
    auth=C8Y_AUTH,
    headers=C8Y_HEADERS,
    data=json.dumps(subscription_json)
)
subscription_response = response.json()
subscription_id = subscription_response['id']
logging.info('Subscription: %s', subscription_response)

token_json = {
    'subscription': C8Y_SUBSCRIPTION_NAME,
    'subscriber': C8Y_SUBSCRIBER_NAME,
    'expiresInMinutes': C8Y_SUBSCRIPTION_EXPIRATION_MIN
}

# Create token
response = client.post(
    C8Y_BASEURL + '/notification2/token',
    auth=C8Y_AUTH,
    headers=C8Y_HEADERS,
    data=json.dumps(token_json)
)
token_response = response.json()
logging.info('Token: %s', token_response)

producer = EventHubProducerClient.from_connection_string(
    conn_str=EVENT_HUB_CONNECTION_STR, eventhub_name=EVENT_HUB_NAME, auth_timeout=180,
)


def send_event_data(message_data):
    with producer:
        event_data_batch = producer.create_batch()
        event_data = EventData(message_data)
        event_data_batch.add(event_data)
        producer.send_batch(event_data_batch)


def open_handler(ws):
    logging.info('Connected')


def message_handler(ws, message):
    parts = message.split('\n\n')
    headers = parts[0].split('\n')
    body = parts[1]
    # Send acknowledgement
    ws.send(headers[0])
    logging.info('New message: %s', headers[0])
    logging.info('Channel: %s', headers[1])
    logging.info('Action: %s', headers[2])
    logging.info('Body: %s', body)

    body_json = json.loads(body)
    event_data_json = {
        'message': headers[0],
        'channel': headers[1],
        'action': headers[2]
    }
    event_data_json.update(body_json)
    event_data = json.dumps(event_data_json)
    send_event_data(event_data)


def error_handler(ws, error):
    logging.error(error)


def close_handler(ws, close_status_code, close_msg):
    logging.info('Close websocket')
    # Delete subscription
    client.delete(
        C8Y_BASEURL + '/notification2/subscriptions/' + subscription_id,
        auth=C8Y_AUTH,
        data=json.dumps(subscription_json)
    )

    # Unsubscribe subscriber
    unsub_response = client.post(
        C8Y_BASEURL + '/notification2/unsubscribe/?token=' + token_response['token'],
        auth=C8Y_AUTH,
    )
    logging.info(str(unsub_response.status_code))
    if unsub_response.status_code == 200:
        logging.info('Subscriber unsubscribed')


ws_client = websocket.WebSocketApp(
    C8Y_BASEURL_WEBSOCKET + '/notification2/consumer/?token=' + token_response['token'],
    on_open=open_handler,
    on_message=message_handler,
    on_error=error_handler,
    on_close=close_handler
)

ws_client.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=60)

