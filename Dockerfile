FROM python:3

USER root

WORKDIR /usr/src/app

ENV db_user mqtt_py
ENV db_password password
ENV database mqtt
ENV db_host 192.168.2.240
ENV db_port 5432
ENV mqtt_host 192.168.2.240
ENV mqtt_port 1883

RUN git clone https://github.com/tisboyo/Aquarium-MQTT-Link.git && chmod +x ./Aquarium_MQTT_Link/init.sh

ENTRYPOINT ["/usr/src/app/Aquarium_MQTT_Link/init.sh"]
