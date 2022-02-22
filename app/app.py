import logging
import os
import time
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from RPi import GPIO

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
GPIO_PIN = int(os.getenv('GPIO_PIN'))
BIP_INTERVAL = int(os.getenv('BIP_INTERVAL'))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "home/alarm")
MQTT_HOSTNAME = os.getenv("MQTT_HOSTNAME", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TIMEOUT = int(os.getenv("MQTT_TIMEOUT", 60))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "buzzer-mqtt")
MQTT_CLEAN_SESSION = os.getenv("CLIENT_CLEAN_SESSION", False)
MQTT_TLS_INSECURE = os.getenv("CLIENT_TLS_INSECURE", True)
MQTT_CLIENT_QOS = int(os.getenv("CLIENT_QOS", 0))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)

RING = False

def configure_logging():

    level_map={
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR
    }

    log_level=level_map.get(LOG_LEVEL, "Unsupported log level provided!")
    logging.basicConfig(level=log_level)


def on_connect(client, userdata, flags, rc):
    logging.info("Connected to the MQTT broker!")


def on_disconnect(client, userdata, flags, rc):
    logging.warn(f"Disconnected from the MQTT broker. End state - '{rc}'")


def on_message(client, userdata, message):
    message = str(message.payload.decode("utf-8"))
    logging.info("Message received from alarm : "+message)
    global RING
    if message == 'triggered':
        RING = True
    else:
        RING = False


configure_logging()

if MQTT_HOSTNAME is None or MQTT_PORT is None:
    logging.error("Could not acquire MQTT broker connection parameters...")
    exit(1)

client = mqtt.Client(MQTT_CLIENT_ID, MQTT_CLEAN_SESSION)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect(MQTT_HOSTNAME, MQTT_PORT, MQTT_TIMEOUT)
client.loop_start()

logging.info("Listen to changes on "+MQTT_TOPIC)
client.subscribe(MQTT_TOPIC)

logging.info("Will ring on PIN "+str(GPIO_PIN)+" with interval of "+str(BIP_INTERVAL)+"ms")

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.IN)
    while True:
        if RING:
            GPIO.setup(GPIO_PIN, GPIO.OUT)
            time.sleep(BIP_INTERVAL/1000)
            GPIO.setup(GPIO_PIN, GPIO.IN)
            time.sleep(BIP_INTERVAL/1000)
        else:
            time.sleep(BIP_INTERVAL/1000)
except Exception as e:
    logging.error(f"Something went wrong and this shouldn't happen... Details: {e}")

client.disconnect()
client.loop_stop()
GPIO.cleanup()
