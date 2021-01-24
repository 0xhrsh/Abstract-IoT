import RPi.GPIO as GPIO
import requests
import time
import json


HUB_DOMAIN = "http://127.0.0.1:8888"


def setupPi(sensor_list):
    GPIO.setmode(GPIO.BOARD)
    for sensor in sensor_list:
        GPIO.setup(sensor["SENSOR_PORT"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print("{} is ready!".format(sensor["sensor_name"]))

    return


def getConfig():

    response = requests.get(HUB_DOMAIN + "/config")
    data = json.loads(response.content.decode())

    return data['send_data_regularly'], data['ptime'], data['SENSOR_LIST']


def sendDataRegularly(sensor_list, ptime):
    try:
        while True:
            time.sleep(ptime)
            for sensor in sensor_list:
                data = GPIO.input(sensor["SENSOR_PORT"])
                body = {}
                body['SENSOR_NAME'] = "IR Sensor"
                body['SENSOR_PORT'] = sensor["SENSOR_PORT"]
                body['SENSOR_DATA'] = data

                requests.put("http://127.0.0.1:8888", json=body,
                             headers={"PI_ID": "42069", "config_version": "8"})

    except KeyboardInterrupt:
        GPIO.cleanup()


def sendDataUpdates(sensor_list, ptime):
    data = {}
    print(sensor_list)

    for sensor in sensor_list:
        data[sensor["SENSOR_PORT"]] = GPIO.input(sensor["SENSOR_PORT"])

    print(data)

    try:
        while True:
            time.sleep(ptime)
            for sensor in sensor_list:
                port_data = GPIO.input(sensor["SENSOR_PORT"])
                if port_data != data[sensor["SENSOR_PORT"]]:
                    data[sensor["SENSOR_PORT"]] = port_data
                    body = {}
                    body['SENSOR_NAME'] = sensor["SENSOR_NAME"]
                    body['SENSOR_PORT'] = sensor["SENSOR_PORT"]
                    body['SENSOR_DATA'] = port_data

                    requests.put("http://127.0.0.1:8888", json=body, headers={"PI_ID": "42069", "config_version": "8"})

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
