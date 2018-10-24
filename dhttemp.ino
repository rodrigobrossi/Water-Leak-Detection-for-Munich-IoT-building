
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

 
void setup()   
{
  Serial.begin(9600);
  
  // Connect to WiFi using WiFiManager
 // wifiManager.resetSettings();       // Reset WiFiManager settings, uncomment if needed
  //wifiManager.setTimeout(AP_TIMEOUT); // Timeout until config portal is turned off
  //if (!wifiManager.autoConnect(AP_NAME, AP_PASS))
  //{
  //  Serial.println("Failed to connect and hit timeout");
   // delay(3000);
    //reset and try again
   // ESP.reset();
    //delay(5000);
  //}

  Blynk.begin(auth, ssid, pass);
  //Blynk.begin(auth, AP_NAME, AP_PASS);
  dht.begin();
  // by default, we'll generate the high voltage from the 3.3v line internally! (neat!)
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  // initialize with the I2C addr 0x3C (for the 64x48)
  display.display();
}
 
 
void loop() 
{
  Blynk.run();
  delay(5000);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  
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
  //temp in f
  
  Blynk.virtualWrite(V5, h);
  Blynk.virtualWrite(V6, f);
  display.setCursor(32,8);
  display.println(f);
  display.setCursor(32,16);
  display.println(h);
     
  display.display();
 
}
