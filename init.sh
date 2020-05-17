#!/bin/bash

git -C /usr/src/app/Aquarium_MQTT_Link pull 

python -m pip install -U -r /usr/src/app/Aquarium_MQTT_Link/requirements.txt

python /usr/src/app/Aquarium_MQTT_Link/main.py

