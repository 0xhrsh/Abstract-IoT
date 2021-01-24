import RPi.GPIO as GPIO
import requests
import time
import json


HUB_DOMAIN = "http://127.0.0.1:8888"


def setupPi(sensor_list):
    GPIO.setmode(GPIO.BOARD)
    for sensor in sensor_list:
        GPIO.setup(sensor["sensor_port"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print("{} is ready!".format(sensor["sensor_name"]))

    return


def getConfig():

    response = requests.get(HUB_DOMAIN + "/config")
    data = json.loads(response.content.decode())

    return data['send_data_regularly'], data['ptime'], data['sensor_list']


def sendDataRegularly(sensor_list, ptime):
    try:
        while True:
            time.sleep(ptime)
            for sensor in sensor_list:
                data = GPIO.input(sensor["sensor_port"])
                body = {}
                body['SENSOR_NAME'] = "IR Sensor"
                body['SENSOR_PORT'] = sensor["sensor_port"]
                body['SENSOR_DATA'] = data

                requests.put("http://127.0.0.1:8888", json=body,
                             headers={"PI_ID": "42069", "config_version": "8"})

    except KeyboardInterrupt:
        GPIO.cleanup()


def sendDataUpdates(sensor_list, ptime):
    data = {}
    print(sensor_list)

    for sensor in sensor_list:
        data[sensor["sensor_port"]] = GPIO.input(sensor["sensor_port"])

    print(data)

    try:
        while True:
            time.sleep(ptime)
            for sensor in sensor_list:
                port_data = GPIO.input(sensor["sensor_port"])
                if port_data != data[sensor["sensor_port"]]:
                    data[sensor["sensor_port"]] = port_data
                    body = {}
                    body['SENSOR_NAME'] = "IR Sensor"
                    body['SENSOR_PORT'] = sensor["sensor_port"]
                    body['SENSOR_DATA'] = port_data

                    requests.put("http://127.0.0.1:8888", json=body,
                                 headers={"PI_ID": "42069", "config_version": "8"})

    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == '__main__':
    send_data_regularly, ptime, sensor_list = getConfig()
    print(sensor_list)
    setupPi(sensor_list)
    # connect to server (send PI_ID)
    if send_data_regularly:
        sendDataRegularly(sensor_list, ptime)
    else:
        sendDataUpdates(sensor_list, ptime)
