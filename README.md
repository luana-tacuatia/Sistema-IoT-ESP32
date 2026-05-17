# 🌱 Sistema Inteligente de Monitoramento Ambiental para Plantas Domésticas utilizando IoT com ESP32

## Descrição

Este projeto apresenta o desenvolvimento de um sistema baseado em Internet das Coisas (IoT) para monitoramento ambiental aplicado ao cultivo de plantas domésticas.

A solução utiliza o microcontrolador ESP32 integrado a sensores ambientais para coleta de:

- Temperatura ambiente;
- Umidade relativa do ar;
- Umidade do solo.

Os dados são enviados via rede Wi-Fi para um servidor backend desenvolvido em Flask, responsável pelo processamento, armazenamento e disponibilização das informações para um dashboard web interativo.

O sistema foi concebido como uma base para futuras aplicações de:

- automação residencial;
- agricultura inteligente em pequena escala;
- monitoramento remoto de ambientes;
- análise histórica de variáveis ambientais.

---

# Objetivos

O projeto visa:

- Implementar coleta automática de dados ambientais;
- Estabelecer comunicação sem fio utilizando Wi-Fi;
- Desenvolver uma API REST para recepção e consulta de dados;
- Armazenar medições em banco de dados SQLite;
- Disponibilizar visualização gráfica em dashboard web;
- Emitir alertas automáticos via Telegram quando condições inadequadas forem detectadas;
- Permitir análises históricas e tendências ambientais por período.

---

# Arquitetura do Sistema

O sistema é composto por três camadas principais.

## 1. Camada de Aquisição

Responsável pela leitura dos sensores através do ESP32.

### Sensores utilizados

- DHT11 → temperatura e umidade do ar;
- Sensor capacitivo de umidade do solo v1.2 (integração em andamento — dados simulados durante o desenvolvimento).

---

## 2. Camada de Processamento

Backend desenvolvido em Flask responsável por:

- Receber e validar dados via HTTP POST;
- Armazenar leituras no banco SQLite;
- Disponibilizar endpoints REST para consulta de dados e disponibilidade de períodos;
- Monitorar leituras em background e disparar alertas via Telegram quando necessário.

### Endpoints da API

| Método | Rota                        | Descrição                                    |
| ------ | --------------------------- | -------------------------------------------- |
| `POST` | `/dados`                    | Recebe leituras do ESP32                     |
| `GET`  | `/api/dados?periodo=<p>`    | Retorna leituras do período informado        |
| `GET`  | `/api/periodos-disponiveis` | Retorna quais períodos têm dados suficientes |
| `GET`  | `/`                         | Serve o dashboard web                        |

### Períodos suportados

`30min` · `1h` · `24h` · `1mes` · `6m` · `12m`

---

## 3. Camada de Visualização

Dashboard web desenvolvido com HTML, CSS, JavaScript e Chart.js, responsável por:

- Exibir medições em tempo real (atualização a cada 5 minutos);
- Exibir gráficos históricos por período;
- Exibir banner de alerta visual quando alguma leitura estiver fora dos limites;
- Habilitar automaticamente os filtros de período conforme o histórico de dados cresce.

---

# Fluxo de Funcionamento

```text
ESP32 + Sensores
        ↓
Envio HTTP POST (JSON)
        ↓
Servidor Flask  →  Validação e armazenamento
        ↓
Banco SQLite
        ↓                        ↓
Dashboard Web              Monitor de Alertas (background)
(consulta periódica)       (verifica a cada 5 min)
                                 ↓
                         Telegram Bot (alerta / resolução)
```

---

# Exemplo de Payload Transmitido

```json
{
  "temp": 25.4,
  "hum": 61.2,
  "soil": 72.8
}
```

---

# Estrutura do Projeto

```text
SISTEMA-IOT-ESP32/
│
├── firmware/
│   ├── include/
│   │   ├── secrets.h
│   │   └── secrets_example.h
│   │
│   ├── src/
│   │   └── main.cpp
│   │
│   └── platformio.ini
│
├── webapp/
│   ├── app.py
│   ├── alertas.py
│   ├── database.db
│   │
│   ├── static/
│   │   ├── style.css
│   │   └── app.js
│   │
│   └── templates/
│       └── dashboard.html
│
├── .env                  ← credenciais locais (não versionado)
├── .env.example          ← template de configuração
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Tecnologias Utilizadas

## Firmware

- ESP32;
- Arduino Framework;
- PlatformIO.

## Backend

- Python 3;
- Flask;
- SQLite3;
- Requests (integração Telegram);
- Python-dotenv (variáveis de ambiente).

## Frontend

- HTML5;
- CSS3;
- JavaScript (ES6+);
- Chart.js.

---

# Como Executar

## Backend (Flask)

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o arquivo `.env` a partir do template (veja a seção [Configuração de Alertas](#configuração-de-alertas)):

```bash
cp .env.example .env
```

Configure a variável de ambiente para modo de desenvolvimento (opcional):

```bash
export FLASK_DEBUG=true   # Linux/macOS
set FLASK_DEBUG=true      # Windows
```

Execute o servidor a partir da pasta `webapp/`:

```bash
cd webapp
python app.py
```

O servidor ficará disponível em:

```
http://localhost:5000
```

---

## Firmware (ESP32)

Configure o arquivo `secrets.h` a partir do exemplo fornecido:

```cpp
#define WIFI_SSID     "SEU_WIFI"
#define WIFI_PASSWORD "SUA_SENHA"
#define API_URL       "http://SEU_IP:5000/dados"
```

Compile e envie o código para o ESP32:

```bash
pio run
pio run --target upload
```

---

# Configuração de Alertas

O sistema monitora as leituras a cada 5 minutos e envia notificações via Telegram quando algum valor sair da faixa ideal. Quando os valores se normalizam, uma mensagem de resolução é enviada automaticamente.

## Limites configurados

| Métrica         | Mínimo | Máximo |
| --------------- | ------ | ------ |
| Temperatura     | 15 °C  | 35 °C  |
| Umidade do Ar   | 30 %   | 90 %   |
| Umidade do Solo | 20 %   | 80 %   |

Para ajustar os limites, edite o dicionário `LIMITES` em `webapp/alertas.py` e o objeto `LIMITES` em `webapp/static/app.js` (usado para o banner no dashboard).

## Configurando o bot do Telegram

### 1. Criar o bot

No Telegram, pesquise por `@BotFather` e inicie uma conversa. Envie o comando `/newbot` e siga as instruções para escolher nome e username. Ao final, o BotFather entregará o **token** do bot:

```
123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Iniciar a conversa com o bot

Pesquise pelo username do bot criado e clique em **Start** (ou envie qualquer mensagem). Esse passo é obrigatório — o Telegram não permite que um bot envie mensagens para quem nunca interagiu com ele.

### 3. Obter o chat_id

Após enviar uma mensagem para o bot, acesse a URL abaixo no navegador substituindo pelo seu token:

```
https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
```

No JSON retornado, o `chat_id` está em:

```json
{
  "message": {
    "chat": {
      "id": 123456789
    }
  }
}
```

> Se o resultado vier vazio (`"result": []`), volte ao passo 2 e envie uma mensagem para o bot antes de tentar novamente.

### 4. Preencher o `.env`

Crie o arquivo `.env` dentro da pasta `webapp/` com as credenciais obtidas:

```env
TELEGRAM_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
```

## Testando o bot

**Teste 1 — verificar conectividade** (sem precisar reiniciar o servidor):

```bash
curl -s -X POST "https://api.telegram.org/bot<SEU_TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "<SEU_CHAT_ID>", "text": "Teste de conexao"}'
```

Se a mensagem chegar no Telegram, o token e o chat_id estão corretos.

**Teste 2 — validar o fluxo completo** (opcional):

Edite temporariamente `webapp/alertas.py` para forçar uma violação e reduzir o intervalo:

```python
INTERVALO_SEGUNDOS = 10  # temporário

LIMITES = {
    'temperatura': { 'min': 100.0, 'max': 101.0, ... },
    ...
}
```

Reinicie o Flask e aguarde ~10 segundos. O alerta deve chegar no Telegram. Reverta os valores após o teste.

---

# Dashboard

O dashboard exibe em tempo real temperatura, umidade do ar e umidade do solo, e permite consulta histórica por período. Um banner de alerta aparece automaticamente no topo quando alguma leitura estiver fora dos limites, com o ícone piscando para chamar atenção. Os botões de filtro são habilitados automaticamente conforme o banco acumula histórico suficiente.

| Período  | Habilita após (aprox.) |
| -------- | ---------------------- |
| 30 min   | ~15 min de dados       |
| 1 hora   | ~30 min de dados       |
| 24 horas | ~12 h de dados         |
| 1 mês    | ~15 dias de dados      |
| 6 meses  | ~3 meses de dados      |
| 12 meses | ~6 meses de dados      |

---

# Considerações Experimentais

Durante parte do desenvolvimento, o sensor capacitivo de umidade do solo ainda não havia sido integrado fisicamente. Para validação do fluxo completo de comunicação, foram utilizados dados simulados gerados no firmware:

```cpp
float temp = random(20, 30);
float hum  = random(40, 80);
float soil = random(40, 90);
```

Essa abordagem permitiu validar:

- comunicação entre ESP32 e servidor;
- armazenamento e consulta no banco de dados;
- funcionamento do dashboard e dos filtros de período;
- visualização gráfica e persistência histórica dos dados;
- disparo e resolução de alertas via Telegram.

---

# Projeto Acadêmico

Projeto desenvolvido para a disciplina **Projeto Integrador V** do curso de **Engenharia de Computação** da **UNIVESP**.
