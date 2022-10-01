import random
import time

from paho.mqtt import client as mqtt_client

import irsdk
from irsdk import Flags

broker = '192.168.16.11'
port = 1883
topic = 'iracing'
subtopics = ['SessionLapsRemain', 'SessionTimeRemain', 'IsOnTrack', 'IsInGarage', 'OnPitRoad', 'LapBestLapTime', 'PlayerCarTeamIncidentCount', 'OnPitRoad', 'SessionFlags']
# generate client ID with pub prefix randomly
client_id = f'pyracing'
username = 'username'
password = 'password'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client, ir):
    while True:
        time.sleep(0.1)
        for t in subtopics:
            val = ir[t]
            if t == 'SessionFlags':
                if val & Flags.blue:
                    val = 'blue'
                elif val & Flags.black:
                    val = 'black'
                elif val & Flags.furled:
                    val = 'gray'
                elif val & Flags.red:
                    val = 'red'
                elif val & Flags.white:
                    val = 'white'
                elif val & Flags.yellow or val & Flags.yellow_waving or val & Flags.caution or val & Flags.caution_waving or val & Flags.debris:
                    val = 'yellow'
                elif val & Flags.green or val & Flags.green_held:
                    val = 'green'
                else:
                    val = 'green'
            elif isinstance(val, float):
                val = round(val, 1)
            elif isinstance(val, bool):
                val = str(val)
            elif isinstance(val, object):
                val = str(val)
            msg = f"{t}: {val}"
            result = client.publish(f"{topic}/{t}", val)
            # result: [0, 1]
            status = result[0]
            if status != 0:
                print(f"Failed to send message to topic {topic}/{t}")


def run():
    client = connect_mqtt()
    client.loop_start()

    ir = irsdk.IRSDK()
    ir.startup()

    publish(client, ir)


if __name__ == '__main__':
    run()
