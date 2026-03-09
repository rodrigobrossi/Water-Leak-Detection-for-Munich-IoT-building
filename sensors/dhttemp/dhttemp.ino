//Written by: Rodrigo Brossi, IBM
//Date: 24/10/18
//Water detection Monitor Munich IoT Center

// Credentials are stored in credentials.h (gitignored).
// Copy credentials.h.example to credentials.h and fill in your values.
#include "credentials.h"

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

// #include "definitions.h"
#define OLED_RESET 0  // GPIO0
Adafruit_SSD1306 display(OLED_RESET);

char auth[] = BLYNK_TOKEN;
char ssid[] = WIFI_SSID;
char pass[] = WIFI_PASS;

#define DHTPIN D4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);
#define ORG         IOT_ORG
#define DEVICE_TYPE IOT_DEVICE_TYPE
#define DEVICE_ID   IOT_DEVICE_ID
#define TOKEN       IOT_TOKEN

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
