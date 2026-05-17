#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"
#include "secrets.h"

#define DHTPIN 4
#define DHTTYPE DHT11
#define SOIL_PIN 34

DHT dht(DHTPIN, DHTTYPE);

void conectarWiFi() {

  Serial.println("Conectando ao WiFi...");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void setup() {

  Serial.begin(115200);

  conectarWiFi();

  dht.begin();

  delay(2000);
}

void loop() {

  if (WiFi.status() != WL_CONNECTED) {
    conectarWiFi();
  }

  
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  // testando até o sensor chegar
  int soilPercent = random(30, 90);

  // quando chegar:
  // int soilValue = analogRead(SOIL_PIN);
  // int soilPercent = map(soilValue, 3000, 1200, 0, 100);
  // soilPercent = constrain(soilPercent, 0, 100);

  if (isnan(temp) || isnan(hum)) {
    Serial.println("Erro ao ler DHT11");
    delay(2000);
    return;
  }

  HTTPClient http;

  http.begin(API_URL);

  http.addHeader("Content-Type", "application/json");

  String json = "{";
  json += "\"temp\":";
  json += temp;
  json += ",";
  json += "\"hum\":";
  json += hum;
  json += ",";
  json += "\"soil\":";
  json += soilPercent;
  json += "}";

  Serial.println("JSON enviado:");
  Serial.println(json);

  int response = http.POST(json);

  Serial.print("Código HTTP: ");
  Serial.println(response);

  String resposta = http.getString();

  Serial.println("Resposta servidor:");
  Serial.println(resposta);

  http.end();

  delay(5000);
}