import sys

from PySide6 import QtGui, QtCore
from PySide6.QtCore import Slot, QTimer, QObject, QSize
from PySide6.QtGui import QAction, QKeySequence, QPaintEvent, QPainter, QBrush, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QGraphicsScene, QGraphicsView, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QMenuBar, QMenu

import paho.mqtt.client as mqtt
import time
import ast
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


### Program se sam nepripoji, je nutne po spusteni kliknout na Connect/Disconnect


# Trida hlavniho okna
class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('RT Location System')
        self.resize(1100,640)
        self.setWindowFlags(QtGui.Qt.MSWindowsFixedSizeDialogHint)

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)


        self.menu1 = self.menuBar().addMenu("Options")
        self.menu1.addMenu("Choose model")

        self.action = QAction(self)
        self.action.setText("Connect/Disconnect")
        self.menu1.addAction(self.action)
        self.action.triggered.connect(self.function)

        self.vbox = QVBoxLayout()
        self.hbox = QHBoxLayout()

        self.label = QLabel("Position: Pokoj0")
        self.label.setIndent(460)
        self.label.setFont(QtGui.QFont('Arial', 14))
        self.hbox.addWidget(self.label)
        self.vbox.addLayout(self.hbox)
        self.main_widget.setLayout(self.vbox)

        self.MainLabel = PositionLabel()
        self.vbox.addWidget(self.MainLabel)
        self.MainLabel.repaint()

        self.messages = RTPredictor("Client3") ### nefunguje uvnitr QLabel z neznameho duvodu

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.setLoc)
        self.timer.start()
    
    def setLoc(self):
        if(self.messages.data[0] == 0):
            self.MainLabel.x = 1020
            self.MainLabel.y = 650
            self.label.setText("Position: Pokoj0")
        elif(self.messages.data[0] == 1):
            self.MainLabel.x = 830
            self.MainLabel.y = 310
            self.label.setText("Position: Chodba")
        elif(self.messages.data[0] == 2):
            self.MainLabel.x = 620
            self.MainLabel.y = 650
            self.label.setText("Position: Pokoj2")
        elif(self.messages.data[0] == 3):
            self.MainLabel.x = 380
            self.MainLabel.y = 620
            self.label.setText("Position: Obývák")
        else:
            self.MainLabel.x = 280
            self.MainLabel.y = 160
            self.label.setText("Position: Kuchyň")


    def function(self):
        if(self.messages.cli.is_connected()):
            self.messages.cli.loop_stop()
            self.messages.cli.disconnect()
        else:
            self.messages.connect_to_host()


# Trida zobrazujici QLabel s pudorysem domu
class PositionLabel(QLabel):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.x = 1020
        self.y = 650
        self.setGeometry(0,0,400,400)
        
        self.active_pixmap = QPixmap("NSI_WiFiProject2.0/půdorys_small")
        self.setPixmap(self.active_pixmap.scaled(1100,640, mode=QtCore.Qt.SmoothTransformation)) # metoda scaled VRACI scalovanou pixmap


    def paintEvent(self, arg__1: QPaintEvent) -> None:
        picture = QPixmap("NSI_WiFiProject2.0/půdorys_small")
        painter = QPainter(picture)
        painter.setBrush(QBrush(QtGui.QColor(0,0,170)))
        painter.drawEllipse(self.x, self.y, 40,50)
        self.setPixmap(picture.scaled(1100,640, mode=QtCore.Qt.SmoothTransformation))
        painter.end()
        return super().paintEvent(arg__1)




# prida pro pripojovani/odpojovani k MQTT broker + trida slouzici k RT predikci z natrenovanych dat
class RTPredictor():
    def __init__(self, client_id, broker_addr = "mqtt.eclipseprojects.io", port = 1883, topic = "NSI/RSSI"):
        super().__init__()
        self.cli = mqtt.Client(client_id=client_id, clean_session=True, transport='tcp')
        self.broker_addr = broker_addr
        self.port = port
        self.topic = topic

        self.data = [0,0,0]

        self.cli.on_connect = self.on_connect
        self.cli.on_disconnect = self.on_disconnect
        self.cli.on_message = self.on_message # attach callback function

        self.model = None
        with open('NSI_WiFiProject2.0/Model_library/rf_model.pkl','rb') as file:
            self.model = pickle.load(file)

        self.df = pd.read_csv("NSI_WiFiProject2.0/signal_data2.csv")


    def connect_to_host(self):
        self.cli.connect(self.broker_addr, self.port, keepalive=60)
        self.cli.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if (rc == 0):
            self.cli.connected_flag = True
            print("connection OK Returned code =",rc)
            self.cli.subscribe(self.topic, qos = 0) # Pri uspesnem pripojeni se subscribujeme na dany topic
        else:
            print("Bad connection Returned code = ",rc)

    def on_disconnect(self, client, userdata, rc):
        print("Client disconnected with rc =", rc)

    def on_message(self, client, userdata, message):
        msg = message.payload.decode('UTF-8')
        msg_as_dict = ast.literal_eval(msg) # prevod ze stringu na slovnik
        print(msg_as_dict)

        df_from_dict = pd.DataFrame(msg_as_dict, index = [0]) # DF vytvoreny z prichozi zpravy
        new_df = pd.DataFrame().reindex(columns=self.df.columns) # DF bez hodnot, pouze obsahuje jmena sloupcu, ktere byly natrenovany
        df_from_dict = pd.concat([new_df, df_from_dict], ignore_index=True) # Slouceni 2 DF, obsahuje vsechny sloupce, ktere byly zachyceny pri trenovani

        for column in df_from_dict:
            df_from_dict[column].fillna(-100, inplace = True) # Nahrazujeme chybejici hodnoty hodnotou -100

        if(df_from_dict.shape[1] == 31): # Neprida-li se nova sit do Dataframu, tak predikujeme
            y_pred = self.model.predict(df_from_dict.drop(['Room'], axis = 1)) # Pokud program nalezne site, ktere dosud nebyly v csv souboru, tak program spadne z duvodu neznamych features
            print("Predikce:",y_pred)
            self.data[0] = y_pred[0]




if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = MainWin()
    main.show()

    sys.exit(app.exec())