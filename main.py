#!/usr/bin/python

from collections import deque
from threading import Thread
import datetime
import time
import json
import math


from flask import Flask, jsonify, request
import RPi.GPIO as GPIO


app = Flask(__name__)
counts = deque()
start = 0

# This is for the J305 tube, I don't think this is proper calibration
usvh_ratio = 0.00812037037037


def counter(channel):
    global counts
    counts.append(datetime.datetime.now())


def sensor_loop():
    time.sleep(2)
    while True:
        try:
            while counts[0] < datetime.datetime.now() - datetime.timedelta(seconds=60):
                counts.popleft()
        except IndexError:
            pass

        time.sleep(1)


@app.route('/api/v1/sensor', methods=['GET'])
# return sensor data like microsieverts per hour, cpm, and calibration factor
def query_sensor():
    microSieverts = round(len(counts) * usvh_ratio, 3)

    return jsonify(
        microSieverts=microSieverts,
        cpm=len(counts),
        calibrate=usvh_ratio
    )


@app.route('/api/v1/rng', methods=['GET'])
def get_rng():
    try:
        interval = 0
        for i, event in enumerate(counts):
            interval += (counts[-1] - counts[i]).total_seconds()

        interval = interval / len(counts)
        interval = int(str(interval).split('.')[1])

    except IndexError:
        interval = "Not enough data"

    return jsonify(
        number=interval,
    )


GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN)
GPIO.add_event_detect(26, GPIO.FALLING, callback=counter)

if __name__ == '__main__':
    Thread(target=sensor_loop).start()
    app.run(host='0.0.0.0', port=8080, debug=True)
