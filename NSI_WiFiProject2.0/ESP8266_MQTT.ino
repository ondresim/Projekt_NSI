#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// WiFi connection
const char* ssid = "W-Ondrej NG";
const char* password = "OndrWRLN_:?";


// MQTT connection
const char* mqtt_server = "mqtt.eclipseprojects.io";
const int port = 1883;
const char topic[] = "NSI/RSSI";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0; // counting the time when the last msg was sent
#define MSG_BUFFER_SIZE 250
char msg[MSG_BUFFER_SIZE]; // buffer for messages

void setup_wifi() {
  delay(10);
  // Connect to WiFi
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA); // WiFi is an object defined as extern in ESP library source code
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("Client connected!"); // Inform about succesful connection
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup() { 
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, port);
}


void send_data(){
  int n = WiFi.scanNetworks(); // scan for networks and return count of found networks
  Serial.print("Number of networks found: ");
  Serial.println(n);
  
  String str = "{"; // String je objekt a zrejme drzi pointer na heap, kde je pole charu, tvorici text
  char msg2[MSG_BUFFER_SIZE];

  for (int i = 0; i < n; i++){
    Serial.print("Network number ");
    Serial.print(i);
    Serial.print(" is ");
    Serial.print(WiFi.SSID(i));
    Serial.print(" ");
    Serial.println(WiFi.RSSI(i));
    if (i == 0){
      str += "'" + WiFi.SSID(i) + "': '" + String(WiFi.RSSI(i)) + "'"; // BSSID is not the same as MAC!!!
    }else{
      str += ", '" + WiFi.SSID(i) + "': '" + String(WiFi.RSSI(i)) + "'";
    }
    //if(WiFi.SSID(i) == "Berkovi" || WiFi.BSSIDstr(i) == "3C:98:72:3F:38:56")
  }
  str += "}";
  //Serial.println(sizeof(str));
  //Serial.println(str.length()); // Vraci pocet znaku bez '\0'
  Serial.println(str);
  if(str.length()+1 > MSG_BUFFER_SIZE){
    Serial.println("String is too large to fit into the buffer!");
  }else{
    str.toCharArray(msg2, MSG_BUFFER_SIZE);
    snprintf (msg, MSG_BUFFER_SIZE, msg2);
    client.publish(topic, msg);
  }
}


void loop() {

  if (!client.connected()) { // Check if client is connected
    reconnect();
  }
  client.loop(); // loop() should be called regularly to allow the client to process incoming messages and maintain its connection to the server

  unsigned long now = millis();
  if (now - lastMsg > 1300) { //posilame zpravu kazdych 1300+ milisekund
    lastMsg = now;
    send_data();
  }
}
