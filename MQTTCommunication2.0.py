import numpy as np
from numpy import int64
import paho.mqtt.client as mqtt
import sys
import pandas as pd
import time
import os

# Slouzi k prevodu prichoziho stringu pres MQTT na datovy typ dictionary
import ast 


# Program zajisti pripojeni k MQTT brokeru a subscribne se na dany topic, po nasbirani urciteho mnozstvi dat je ulozi do .csv a odpoji se
# Pripad odpojeni od serveru neni nijak zajisten!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


broker_addr = "mqtt.eclipseprojects.io"
port = 1883
topic = "NSI/RSSI"



FILE_LOCATION = "NSI_WiFiProject2.0/signal_data.csv" # Location for the data
SAMPLES_NUMBER = 5 # choose how many samples to collect
FILL_VALUE = 1 # Fill value for 'Room' column 


def on_connect(client, userdata, flags, rc): # rc = return code
    if (rc == 0):
        client.connected_flag = True
        print("connected OK Returned code =",rc)
        client.subscribe(topic, qos = 0) # Pri uspesnem pripojeni se subscribujeme na dany topic
    else:
        print("Bad connection Returned code= ",rc)


data = []
def on_message(client, userdata, message):
    global end_flag
    msg = message.payload.decode('UTF-8')
    msg_as_dict = ast.literal_eval(msg)
    data.append(msg_as_dict) # Ukladani dat do pole
    
    print(len(data))

    if (len(data) == SAMPLES_NUMBER):
        df = pd.DataFrame(data)
        print(df.head())

        room=np.empty(SAMPLES_NUMBER)

        room.fill(FILL_VALUE)
        df["Room"] = room

        try:
            df2 = pd.read_csv(FILE_LOCATION)
            df_new = pd.concat([df2, df]) # Concat is used to add new rows/columns into the dataframe
            df_new.to_csv(FILE_LOCATION , header = True, index = False) # mode = 'a' -> append mode (keeps existing data in .csv file)
        except: # EMPTY CSV OR FILE DOES NOT EXIST ERROR
            print("Empty csv or csv not found!")
            df.to_csv(FILE_LOCATION , index = False)
        
        end_flag = 1
    


cli = mqtt.Client(client_id="Client1", clean_session=True, transport='tcp')
cli.connect(broker_addr, port=port, keepalive=60)

cli.on_connect = on_connect
cli.on_message = on_message # attach callback function


cli.loop_start()

end_flag = 0
while end_flag == 0: # loop_start() is running in its own thread and therefore is not blocking main thread
    continue

cli.disconnect()
cli.loop_stop()

