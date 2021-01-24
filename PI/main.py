import RPi.GPIO as GPIO
import requests
import time
import json


HUB_DOMAIN = "example.com"


def setupPi(sensor_list):
    GPIO.setmode(GPIO.BOARD)
    for sensor in sensor_list:
        GPIO.setup(sensor["sensor_port"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print("{} is ready!".format(sensor["sensor_name"]))

    return


def getConfig():

    response = requests.get(HUB_DOMAIN + "/config")
    data = json.loads(response)

    return data['send_data_regularly'], data['ptime'], data['sensor_list']


def sendDataRegularly(sensor_list, ptime):
    try:
        while True:
            time.sleep(ptime)
            for sensor in sensor_list:
                data = GPIO.input(sensor["sensor_port"])
                print(data)
                # send data

    except KeyboardInterrupt:
        GPIO.cleanup()


def sendDataUpdates(sensor_list, ptime):
    data = {}

    for sensor in sensor_list:
        data[sensor["sensor_port"]] = GPIO.input(sensor["sensor_port"])

    try:
        while True:
            send_update = False
            time.sleep(ptime)
            for sensor in sensor_list:
                port_data = GPIO.input(sensor["sensor_port"])
                if port_data != data[sensor["sensor_port"]]:
                    data[sensor["sensor_port"]]
                    send_update = True

            if send_update:
                print(data)
                # Send data here

    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == '__main__':
    send_data_regularly, ptime, sensor_list = getConfig()
    setupPi(sensor_list)
    # connect to server (send PI_ID)
    if send_data_regularly:
        sendDataRegularly(sensor_list, ptime)
    else:
        sendDataUpdates(sensor_list, ptime)
