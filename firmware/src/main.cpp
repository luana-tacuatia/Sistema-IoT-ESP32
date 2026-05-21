#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"
#include "secrets.h"

// Configurações de Pinos
#define DHTPIN 4
#define DHTTYPE DHT11
#define SOIL_PIN 34 

DHT dht(DHTPIN, DHTTYPE);

// Variáveis de Calibração - AJUSTE ESTES VALORES APÓS TESTAR
int valorNoAr = 3200;   // Valor lido com o sensor na terra seca
int valorNaAgua = 1500; // Valor lido com o sensor na terra úmida

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  
  Serial.println("\nConectando ao WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFalha ao conectar no WiFi.");
  }
}

void setup() {
  Serial.begin(115200);
  
  // Configura leitura de até 3.3V
  analogSetAttenuation(ADC_11db); 
  
  conectarWiFi();
  dht.begin();

  // Para pinos analógicos no ESP32, não usamos pinMode(INPUT)
  
  Serial.println("Sistema Iniciado!");
  delay(2000);
}

void loop() {
  // Garante conexão WiFi antes de tentar o HTTP
  conectarWiFi();

  // --- LEITURA DHT11 ---
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  // --- LEITURA SENSOR DE SOLO ---
  // Fazemos a média de 10 leituras para evitar ruído
  long soma = 0;
  for(int i = 0; i < 10; i++) {
    soma += analogRead(SOIL_PIN);
    delay(10);
  }
  int soilValue = soma / 10;

  // Conversão para porcentagem
  // O map inverte os valores: valorNoAr = 0%, valorNaAgua = 100%
  int soilPercent = map(soilValue, valorNoAr, valorNaAgua, 0, 100);
  soilPercent = constrain(soilPercent, 0, 100);

  // --- DEBUG SERIAL ---
  Serial.println("\n--- LEITURAS ATUAIS ---");
  Serial.printf("Temperatura: %.1f °C | Umidade Ar: %.1f %%\012", temp, hum);
  Serial.printf("Solo Bruto: %d | Solo: %d %%\012", soilValue, soilPercent);

  // Validação dos dados do DHT
  if (isnan(temp) || isnan(hum)) {
    Serial.println("Erro crítico: Falha na leitura do DHT11!");
    delay(2000);
    return; 
  }

  // --- ENVIO HTTP ---
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");

    // Montagem do JSON
    String json = "{";
    json += "\"temp\":" + String(temp, 1) + ",";
    json += "\"hum\":" + String(hum, 1) + ",";
    json += "\"soil\":" + String(soilPercent);
    json += "}";

    Serial.println("Enviando JSON: " + json);

    int response = http.POST(json);

    if (response > 0) {
      Serial.printf("Sucesso! Código HTTP: %d\012", response);
      Serial.println("Resposta: " + http.getString());
    } else {
      Serial.printf("Erro no POST: %s\012", http.errorToString(response).c_str());
    }
    http.end();
  }

  delay(5000); // Aguarda 5 segundos para a próxima leitura
}
