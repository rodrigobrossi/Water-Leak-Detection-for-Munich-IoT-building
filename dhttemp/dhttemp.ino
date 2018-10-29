//Written by: John D Vasquez, IBM
//Date: 24/10/18
//Water detection Monitor Munich IoT Center
// WiFi manager code in place 

#define BLYNK_PRINT Serial

#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "DHT.h"

#include <PubSubClient.h>

//Includes for blynk connection
#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>


// WiFi-Manager
//#include <DNSServer.h>        // Local DNS Server used for redirecting all requests to the configuration portal
//#include <ESP8266WebServer.h> // Local WebServer used to serve the configuration portal
//#include <WiFiManager.h>      // https://github.com/tzapu/WiFiManager WiFi Configuration Magic

// #include "definitions.h"
#define OLED_RESET 0  // GPIO0
Adafruit_SSD1306 display(OLED_RESET);

// You should get Auth Token in the Blynk App.
// Go to the Project Settings (nut icon).
char auth[] = "bb1475ed813446248525d5e9374d32c8";

// Your WiFi credentials.
// Set password to "" for open networks.

char ssid[] = "IOTDEMOS";
char pass[] = "dem04IoT";
 
#define DHTPIN D4
#define DHTTYPE DHT22  
DHT dht(DHTPIN, DHTTYPE);
#define ORG "h9eyui"
#define DEVICE_TYPE "waterLeakDetector"
#define DEVICE_ID "20WestSensor1"
#define TOKEN "watsoniot"

char server[] = ORG ".messaging.internetofthings.ibmcloud.com";
char topic[] = "iot-2/evt/status/fmt/json";
char authMethod[] = "use-token-auth";
char token[] = TOKEN;
char clientId[] = "d:" ORG ":" DEVICE_TYPE ":" DEVICE_ID;

WiFiClient wifiClient;
PubSubClient client(server, 1883, NULL, wifiClient);



 
void setup()   
{
  Serial.begin(9600);
  
  Blynk.begin(auth, ssid, pass);
  dht.begin();
  // by default, we'll generate the high voltage from the 3.3v line internally! (neat!)
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  // initialize with the I2C addr 0x3C (for the 64x48)
  display.display();

  
}
 
int counter = 0;
void loop() 
{
  Blynk.run();
  delay(5000);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);

  if (!!!client.connected()) {
   Serial.print("Reconnecting client to ");
   Serial.println(server);
   while (!!!client.connect(clientId, authMethod, token)) {
      Serial.print(".");
      delay(500);
   }
   Serial.println();
 }

  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  float f = dht.readTemperature(true);
  // Check if any reads failed and exit early (to try again).
  if (isnan(h) || isnan(t) || isnan(f)) 
  {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  
  float c  = ((f -32) /1.800);

 String payload = "{";
  payload += "\"temperature\":"; payload += t; payload += ",";
  payload += "\"humidity\":"; payload += h;payload += ",";
  payload += "\"celsius\":"; payload += c;
  payload += "}";
 
 Serial.print("Sending payload: ");
 Serial.println(payload);
 
 if (client.publish(topic, (char*) payload.c_str())) {
   Serial.println("Publish ok");
 } else {
   Serial.println("Publish failed");
 }

 
  Blynk.virtualWrite(V5, h);
  Blynk.virtualWrite(V6, f);
  Blynk.virtualWrite(V7, c);
  display.setCursor(32,8);
  display.println(String(h)+" %");
  display.setCursor(32,16);
  display.println(String(f)+" 'F");
  display.setCursor(32,24);
  display.println(String(c)+" 'C");
  
     
  display.display();
 
}
