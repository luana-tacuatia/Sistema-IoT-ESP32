#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"
#include "secrets.h"

#define DHTPIN 4
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);

  Serial.println("Conectando ao WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  dht.begin();
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // float temp = dht.readTemperature();
    // float hum = dht.readHumidity();
    float temp = random(20, 30);
    float hum = random(40, 80);

    if (isnan(temp) || isnan(hum)) {
      Serial.println("Erro ao ler DHT11");
      delay(2000);
      return;
    }

    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");

    String json = "{\"temp\":" + String(temp) + ",\"hum\":" + String(hum) + "}";

    int response = http.POST(json);

    Serial.print("Enviado! Código HTTP: ");
    Serial.println(response);
    Serial.println("Enviando dados...");

    http.end();
  }

  delay(5000);
}
