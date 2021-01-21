# import RPi.GPIO as GPIO
# import time
import json


# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# print("IR Sensor Ready.....")

# try:
#     while True:
#         time.sleep(0.2)

#         if GPIO.input(sensor):
#             print("Object Detected")
#         else:
#             print("No Object detected")


# except KeyboardInterrupt:
#     GPIO.cleanup()


def getSensors():
    s = open('sensors.json',)
    sensor_list = json.load(s)['sensor_list']
    s.close()

    return sensor_list


getSensors()
