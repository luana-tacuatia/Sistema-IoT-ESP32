# 🌱 Sistema de Monitoramento Ambiental para Plantas Domésticas utilizando IoT com ESP32

## Descrição
Este projeto apresenta o desenvolvimento de um sistema baseado em Internet das Coisas (IoT) para monitoramento de variáveis ambientais relevantes ao cultivo de plantas domésticas. A solução utiliza o microcontrolador ESP32, aliado a um sensor de temperatura e umidade (DHT11) utilizando C++ (Arduino Framework), para coletar dados do ambiente e enviá-los a um servidor backend desenvolvido em Flask.

A proposta integra conceitos de sistemas embarcados, comunicação em rede e aplicações web, permitindo a construção de uma base para futuras aplicações de automação residencial e agricultura inteligente em pequena escala.

Tal projeto visa:
- Implementar a coleta de dados de temperatura e umidade;
- Estabelecer comunicação via rede WiFi com o ESP32;
- Desenvolver uma API simples para recepção dos dados;

## Arquitetura do Sistema
O sistema é composto por dois módulos principais:

**1. Camada de Aquisição (ESP32 + Sensor);**

**2. Camada de Processamento (Backend Flask);**
```
ESP32 + DHT11 → Envio HTTP (JSON) → Servidor Flask
```
Fluxo de funcionamento:
- O ESP32 realiza a leitura dos sensores;
- Os dados são estruturados em formato JSON;
- Uma requisição HTTP do tipo POST é enviada ao servidor;
- O backend recebe e processa os dados;

Exemplo de dados transmitidos:
```js
{
  "temp": 25,
  "hum": 60
}
```

### Como Executar
#### Backend (Flask)
Instale as dependências:
```
pip install flask
```
Execute o servidor:
```
python app.py
```
O servidor ficará disponível em:
```
http://0.0.0.0:5000/dados
```

#### Firmware (ESP32)
Configure o arquivo secrets.h:
```
#define WIFI_SSID "SEU_WIFI"
#define WIFI_PASSWORD "SUA_SENHA"
#define API_URL "http://SEU_IP:5000/dados"
```
Compile e envie o código para o ESP32.

## Estrutura do Projeto
```
├── backend/
│   └── app.py          # API Flask para recepção de dados
├── firmware/
│   └── src/
│       └── main.cpp    # Código embarcado do ESP32
```

## Considerações Experimentais
Durante o desenvolvimento, está sendo utilizado simulação de dados para validação do fluxo de comunicação:
```
float temp = random(20, 30);
float hum = random(40, 80);
```
Essa abordagem permite testar a integração entre os módulos mesmo na ausência do sensor físico.
