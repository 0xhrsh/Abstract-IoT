import RPi.GPIO as GPIO
import requests
import time
import json
import socket

HEADER = 'RAP\r\n\r\n\r\n\r\n\r\n\r\nPI_ID: 42069\r\nconfig_version: {}\r\n\r\n'


HOST = "192.168.1.6"
PORT = 8888
HUB_DOMAIN = "http://" + HOST + ":" + str(PORT)


def setupPi(sensor_list):
    GPIO.setmode(GPIO.BOARD)
    for sensor in sensor_list:
        GPIO.setup(sensor["SENSOR_PORT"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print("{} is ready!".format(sensor["SENSOR_NAME"]))

    return


def getConfig():

    response = requests.get(HUB_DOMAIN + "/config")
    data = json.loads(response.content.decode())

    return data['send_data_regularly'], data['ptime'], data['SENSOR_LIST'], str(data['version'])


def sendDataRegularly(sensor_list, ptime, version):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(HEADER.format(version).encode('utf8'))
    data = s.recv(1024)
    print(data.decode())
    time.sleep(1)
    try:
        while True:
            for sensor in sensor_list:
                data = GPIO.input(sensor["SENSOR_PORT"])
                body = {}
                body['SENSOR_NAME'] = sensor["SENSOR_NAME"]
                body['SENSOR_PORT'] = sensor["SENSOR_PORT"]
                body['SENSOR_DATA'] = data
                print("Sending data to hub...")
                print("\t" + str(json.dumps(body)))
                s.sendall(str(json.dumps(body)).encode('utf8'))
                ret = s.recv(1024)
                print("\t Current Version:", ret.decode())
                if(ret.decode('utf8') != str(version)):
                    return

            time.sleep(ptime)

    except KeyboardInterrupt:
        GPIO.cleanup()


def sendDataUpdates(sensor_list, ptime, version):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(HEADER.format(version).encode('utf8'))
    data = s.recv(1024)
    print(data.decode())
    time.sleep(1)

    data = {}
    for sensor in sensor_list:
        data[sensor["SENSOR_PORT"]] = None
    try:
        while True:
            for sensor in sensor_list:
                port_data = GPIO.input(sensor["SENSOR_PORT"])
                if port_data != data[sensor["SENSOR_PORT"]]:
                    data[sensor["SENSOR_PORT"]] = port_data
                    body = {}
                    body['SENSOR_NAME'] = sensor["SENSOR_NAME"]
                    body['SENSOR_PORT'] = sensor["SENSOR_PORT"]
                    body['SENSOR_DATA'] = port_data
                    print("Sending data to hub...")
                    print("\t" + str(json.dumps(body)))
                    s.sendall(str(json.dumps(body)).encode('utf8'))
                    ret = s.recv(1024)
                    print("\t Current Version:", ret.decode())
                    if(ret.decode('utf8') != str(version)):
                        return

            time.sleep(ptime)

    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == '__main__':
    while True:
        send_data_regularly, ptime, sensor_list, version = getConfig()
        setupPi(sensor_list)

        if send_data_regularly:
            sendDataRegularly(sensor_list, ptime, version)
        else:
            sendDataUpdates(sensor_list, ptime, version)

        print("Starting Client.....")
