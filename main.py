#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2010-2013 Roger Light <roger@atchoo.org>
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Distribution License v1.0
# which accompanies this distribution.
#
# The Eclipse Distribution License is available at
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#    Roger Light - initial implementation
# Copyright (c) 2010,2011 Roger Light <roger@atchoo.org>
# All rights reserved.

# This shows a simple example of an MQTT subscriber.

# import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt
import datetime
import psycopg2

import os


def load_credentials():
    # Check to make sure database information is defined in the environment variables
    if not (
        os.getenv("db_user")
        and os.getenv("db_password")
        and os.getenv("database")
        and os.getenv("db_host")
        and os.getenv("mqtt_host")
    ):
        print("Database credentials are not set in environment variables.")
        print(
            "Make sure all of the variables are set: db_user, db_password, database, db_host, db_port (optional), mqtt_host, mqtt_port (optional)"
        )
        import sys  # We don't use sys anywhere else, so import it only when we need it, which should be never.

        # Stop execution due to no credentials
        sys.exit()

    # Save credentials into a dictionary for use later
    env = {
        "user": os.getenv("db_user"),
        "password": os.getenv("db_password"),
        "database": os.getenv("database"),
        "host": os.getenv("db_host"),
        "port": int(os.environ.get("db_port", 5432)),
        "mqtt_host": os.getenv("mqtt_host"),
        "mqtt_port": int(os.environ.get("mqtt_port", 1883)),
    }

    return env


def on_connect(mqttc, obj, flags, rc):
    """ Called when a connection to the MQTT server is established. """
    print(f"Connected to MQTT server {env['mqtt_host']}:{env['mqtt_port']}")


def on_message(mqttc, obj, msg):
    global last_update, update_frequency

    # Check if enough time has elapsed to do the next database update
    now = datetime.datetime.now()
    time_since_update = now - last_update.get(
        msg.topic, datetime.datetime.utcfromtimestamp(0)
    )

    if time_since_update < update_frequency:
        print(
            f"Next database update for {msg.topic} no sooner than",
            update_frequency - (now - last_update.get(msg.topic, 0)),
        )
        return
    else:
        last_update[msg.topic] = now

    # Establish database connection and do INSERT
    conn = None
    try:
        conn = psycopg2.connect(
            user=env["user"],
            password=env["password"],
            host=env["host"],
            port=env["port"],
            database=env["database"],
        )

        cur = conn.cursor()

        tank = msg.topic.split("/")[1]
        sensor = msg.topic.split("/")[2]
        value = msg.payload.decode("utf-8")

        query = f"INSERT INTO aquariums (time, tank, sensor, value) VALUES (%s, %s, %s, %s);"
        query_values = (datetime.datetime.now(), tank, sensor, value)

        cur.execute(query, query_values)
        conn.commit()

        print(query_values)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    finally:
        if conn is not None:
            cur.close()
            conn.close()


def on_publish(mqttc, obj, mid):
    """ Called when a publish message is sent. """
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    """ Needed MQTT function. """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    """ Needed MQTT function. """
    print(string)


def main():

    # If you want to use a specific client id, use
    # mqttc = mqtt.Client("client-id")
    # but note that the client id must be unique on the broker. Leaving the client
    # id parameter empty will generate a random id for you.
    mqttc = mqtt.Client()
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_publish = on_publish
    mqttc.on_subscribe = on_subscribe
    # Uncomment to enable debug messages
    # mqttc.on_log = on_log
    try:
        mqttc.connect(env["mqtt_host"], env["mqtt_port"], 60)

    except ConnectionRefusedError as error:
        print(error)
        print(
            f"Connection Refused for MQTT Server: {env['mqtt_host']}:{env['mqtt_port']}"
        )

    except OSError as error:
        print(error)

    mqttc.subscribe("aquariums/#", 0)

    mqttc.loop_forever()


# Load credentials from environment variables
env = load_credentials()

# Used for tracking how long between database updates.
last_update = dict()
update_frequency = datetime.timedelta(minutes=5)

if __name__ == "__main__":
    main()
