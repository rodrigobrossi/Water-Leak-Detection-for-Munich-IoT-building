# Water Damage Prevention System

Sistema de detecção e prevenção de danos por água para o **Munich IoT Center (IBM)**. Monitora umidade em tempo real via sensores IoT, detecta vazamentos automaticamente e dispara notificações multi-canal com fluxo de resposta a incidentes via web.

<img src="/img/sensor.png" width="200"/> <img src="/img/UI.png" width="400"/>

---

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAMADA DE SENSORES                        │
│                                                                   │
│  Raspberry Pi (humidity.py)          ESP8266 (dhttemp.ino)       │
│  Sensor DHT / AM2302 no GPIO 4       Sensor DHT22 no pino D4     │
│  Publica a cada 60 segundos          Publica a cada 5 segundos   │
│                 │                                │                │
│                 └──────────────┬─────────────────┘                │
└────────────────────────────────┼────────────────────────────────-─┘
                                 │ MQTT (porta 1883)
                                 ▼
                   IBM Watson IoT Platform
                   Tópico: iot-2/evt/status/fmt/json
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                    CLOUD BACKEND (Flask + Gevent)               │
│                                                                  │
│  BDPIncident ──► Detecção de incidentes por nível de umidade    │
│       │          < 50% → OK | 50-75% → MODERADO | >75% → CRÍTICO│
│       ▼                                                          │
│  BDPNotifier ──► Email (Gmail SMTP)                             │
│                ──► Slack (Webhook)                              │
│                ──► Tririga (Service Request FM)                 │
│                                                                  │
│  BDPRespond  ──► Web UI: /respond?nid=<id>                     │
│                    ├── SNOOZE (adiar alarme)                    │
│                    └── FIXED (marcar como resolvido)            │
│                                                                  │
│  REST APIs                                                       │
│  ├── POST /tenant    ──► Cadastrar organização                  │
│  ├── POST /user      ──► Cadastrar usuários                     │
│  └── POST /hardware  ──► Registrar sensores                     │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                         IBM Db2 Database
              BDP_TENANT | BDP_USER | BDP_HARDWARE
              BDP_INCIDENT | BDP_NOTIFICATION | BDP_RAW_EVENTS
```

---

## Estrutura do Repositório

```
.
├── sensors/
│   ├── pi/                   # Implementação para Raspberry Pi
│   │   ├── humidity.py       # Coleta de dados do sensor DHT, publica via MQTT e Blynk
│   │   ├── MarkovModel.py    # Modelo preditivo de transições de estado (seco/molhado)
│   │   └── humidity.service  # Serviço systemd para execução automática
│   └── dhttemp/              # Implementação para ESP8266 (Arduino)
│       └── dhttemp.ino       # Firmware: MQTT + Blynk + display OLED SSD1306
│
└── cloud_app/BuildingDamageProtection/
    ├── Dockerfile
    ├── Procfile              # Deploy no IBM Cloud (Cloud Foundry)
    ├── requirements.txt      # Dependências Python
    ├── runtime.txt           # Python 3.6
    └── src/main/python/
        ├── gateway.py              # Ponto de entrada Flask: define rotas e inicia threads
        ├── bdp_incident.py         # Listener de eventos IoT + lógica de detecção
        ├── bdp_notifier.py         # Orquestração de notificações (email/Slack/Tririga)
        ├── bdp_respond.py          # Handler do fluxo de resposta a incidentes (web UI)
        ├── bdp_hardware.py         # REST API para gerenciamento de sensores
        ├── bdp_tenant.py           # REST API para multi-tenancy
        ├── bdp_user.py             # REST API para usuários
        ├── bdp_auth.py             # Autenticação HTTP Basic Auth
        ├── bdp_property.py         # Singleton de carregamento do config.json
        ├── bdp_dbutil.py           # Queries Db2 + pool de conexões
        ├── bdp_util.py             # Integrações: Gmail, Slack, Tririga
        ├── bdp_sysinit.py          # Inicialização e migração do schema do banco
        ├── bdp_servicecheck.py     # Health check periódico da conexão com DB
        ├── bdp_email.py            # Modelo de dados de email
        ├── bdp_tririga_worktask.py # Integração com sistema FM Tririga
        ├── bdp_unittest.py         # Testes unitários
        ├── templates/              # Templates HTML/texto para emails e UI
        └── static/                 # CSS e imagens da interface web
```

---

## Componentes em Detalhe

### 1. Sensores (`sensors/`)

#### Raspberry Pi — `humidity.py`
- Lê temperatura e umidade do sensor **DHT/AM2302** no pino GPIO 4
- Publica dados a cada **60 segundos** via MQTT para o IBM Watson IoT Platform
- Expõe dados também para o app mobile **Blynk** (pinos virtuais V5=umidade, V6=fahrenheit, V7=celsius)
- Pode ser executado como serviço systemd (arquivo `humidity.service` incluído)

#### ESP8266 — `dhttemp.ino`
- Lê temperatura e umidade do sensor **DHT22** no pino D4
- Exibe dados em display **OLED SSD1306** (I2C)
- Publica via MQTT para o IBM Watson IoT Platform a cada **5 segundos**
- Integração com **Blynk** nos mesmos pinos virtuais

#### Modelo Preditivo — `MarkovModel.py`
- Implementa **Cadeia de Markov** para prever transições de estado (seco → molhado)
- Usa estimação de máxima verossimilhança para parametrização

---

### 2. Backend Cloud (`cloud_app/`)

#### `gateway.py` — Ponto de Entrada
- Inicializa o app Flask com Gevent WSGI para handling assíncrono
- Registra todas as rotas REST
- Inicia thread de background para health checks periódicos
- Conecta ao IBM Watson IoT Platform para escutar eventos dos sensores
- Modos de servidor: `flask` (dev), `cli` (sem servidor HTTP), ou WSGI com SSL

#### `bdp_incident.py` — Detecção de Incidentes
- Escuta eventos MQTT dos device types: `waterLeakDetector` e `waterSensorsDemo`
- Armazena leituras brutas em `BDP_RAW_EVENTS` (retenção de 7 dias)
- **Lógica de detecção:**
  - Umidade < 50% → Sem incidente
  - Umidade 50–75% → Incidente **MODERADO**
  - Umidade > 75% → Incidente **CRÍTICO**
- Evita duplicação de incidentes ativos por tenant + sensor

#### `bdp_notifier.py` — Orquestração de Notificações
- Determina quais usuários notificar conforme **horário** (horário comercial vs. fora de expediente)
- Gerencia ciclo de vida das notificações: **ALARM → SNOOZE → FIXED**
- Renderiza templates Mustache para emails e mensagens Slack
- Cria service requests no **Tririga** (sistema de facilities management)

#### `bdp_respond.py` — Interface de Resposta
- Rota `GET /respond?nid=<notification_id>`: renderiza UI com detalhes do incidente
- Exibe gráfico histórico de umidade, urgência e status atual
- Permite ao usuário:
  - **SNOOZE**: Adiar alarme por N horas (configurável)
  - **FIXED**: Marcar incidente como resolvido

#### `bdp_dbutil.py` — Camada de Dados
Gerencia conexão singleton com **IBM Db2**. Tabelas principais:

| Tabela | Descrição |
|--------|-----------|
| `BDP_TENANT` | Organizações/clientes do sistema |
| `BDP_USER` | Usuários com info de contato e disponibilidade |
| `BDP_HARDWARE` | Sensores com localização física |
| `BDP_INCIDENT` | Incidentes de água detectados |
| `BDP_NOTIFICATION` | Notificações individuais por usuário |
| `BDP_RAW_EVENTS` | Leituras brutas dos sensores (7 dias) |
| `BDP_DBCHANGELOG` | Versionamento do schema |

---

## Pré-requisitos

### Para o Backend Cloud
- Python 3.6
- IBM Db2 (local ou IBM Cloud)
- IBM Watson IoT Platform (conta IBM Cloud)
- Conta Gmail com "Acesso a app menos seguro" habilitado (ou App Password)
- Slack Webhook URL (opcional)
- Tririga API (opcional)

### Para o Sensor Raspberry Pi
- Raspberry Pi (qualquer modelo com GPIO)
- Sensor DHT11, DHT22 ou AM2302
- Python 3.x

### Para o Sensor ESP8266
- Placa ESP8266 (NodeMCU, Wemos D1 Mini, etc.)
- Sensor DHT22
- Display OLED SSD1306 (opcional)
- Arduino IDE 1.8+

---

## Setup Local — Backend

### 1. Configuração

Crie o arquivo de configuração a partir do exemplo:

```bash
cp cloud_app/BuildingDamageProtection/resources/config/config.example.json \
   cloud_app/BuildingDamageProtection/resources/config/config.json
```

Edite `config.json` com suas credenciais (veja detalhes na seção [Configuração](#configuração)).

### 2. Instalação das Dependências

```bash
cd cloud_app/BuildingDamageProtection
pip install -r requirements.txt
```

> **Nota:** A dependência `ibm_db==3.0.1` requer o IBM Db2 Client instalado no sistema.
> Veja: [ibm-db no PyPI](https://pypi.org/project/ibm-db/)

### 3. Executar

```bash
# Modo desenvolvimento (Flask)
cd cloud_app/BuildingDamageProtection/src/main/python
python gateway.py

# Modo produção (Gunicorn)
cd cloud_app/BuildingDamageProtection
gunicorn -w 3 --pythonpath src/main/python --log-level debug gateway:application
```

### 4. Via Docker

```bash
cd cloud_app/BuildingDamageProtection
docker build -t building-damage-protection .
docker run -p 5000:5000 building-damage-protection
```

### 5. Testes

```bash
python src/main/python/bdp_unittest.py
```

---

## Setup Local — Sensor Raspberry Pi

```bash
# 1. Instalar biblioteca do sensor DHT
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
sudo python setup.py install

# 2. Instalar dependências IoT e Blynk
pip install ibmiotf
pip install blynk-library-python

# 3. Configurar credenciais em sensors/pi/humidity.py
# Edite: organization, deviceType, deviceId, authToken, blynkToken

# 4. Executar
cd sensors/pi
python humidity.py

# 5. (Opcional) Instalar como serviço systemd
sudo cp humidity.service /etc/systemd/system/
sudo systemctl enable humidity.service
sudo systemctl daemon-reload
sudo systemctl start humidity.service
```

---

## Setup — Sensor ESP8266

1. Abra `sensors/dhttemp/dhttemp.ino` no **Arduino IDE**
2. Instale as bibliotecas pelo Library Manager:
   - `PubSubClient` (MQTT)
   - `ESP8266WiFi`
   - `Blynk`
   - `Adafruit GFX Library`
   - `Adafruit SSD1306`
   - `DHT sensor library` (Adafruit)
3. Edite as credenciais no sketch:
   ```cpp
   char auth[] = "SEU_BLYNK_TOKEN";
   char ssid[] = "SUA_REDE_WIFI";
   char pass[] = "SUA_SENHA_WIFI";
   #define ORG "SEU_ORG_ID"
   #define TOKEN "SEU_AUTH_TOKEN"
   ```
4. Selecione a placa correta (ex: `NodeMCU 1.0`) e faça o upload

---

## Configuração

O arquivo `config.json` deve estar em:
`cloud_app/BuildingDamageProtection/resources/config/config.json`

```json
{
  "ver": "1.0",
  "server_type": "flask",
  "server_port": "5000",
  "https_key": "",
  "https_cert": "",
  "gateway_user": "admin",
  "gateway_password": "senha_segura",
  "db_dbname": "BLUDB",
  "db_dbhost": "localhost",
  "db_dbport": "50000",
  "db_admin_user": "db2admin",
  "db_admin_password": "senha_db",
  "iotplatform_options": {
    "org": "SEU_ORG_ID",
    "id": "cloud-app",
    "auth-method": "apikey",
    "auth-key": "SUA_API_KEY",
    "auth-token": "SEU_AUTH_TOKEN"
  },
  "gmail_user": "seu@gmail.com",
  "gmail_password": "sua_app_password",
  "slack_auth": "xoxb-seu-token-slack",
  "tririga_api": "https://sua-instancia.tririga.com/api/",
  "tririga_user": "usuario_tririga",
  "tririga_password": "senha_tririga",
  "alarm_interval_hr": "1",
  "snooze_hr": "2",
  "check_status_interval": "24"
}
```

### Parâmetros de Configuração

| Parâmetro | Descrição |
|-----------|-----------|
| `server_type` | `flask` (dev), `cli` (sem HTTP), ou qualquer outro valor (WSGI/SSL) |
| `server_port` | Porta do servidor HTTP |
| `gateway_user/password` | Credenciais para autenticação HTTP Basic nas APIs REST |
| `db_*` | Credenciais do IBM Db2 |
| `iotplatform_options` | Credenciais IBM Watson IoT Platform (Application credentials) |
| `gmail_user/password` | Conta Gmail para envio de alertas |
| `slack_auth` | Token de bot Slack para envio de mensagens |
| `tririga_*` | Credenciais da API do sistema Tririga (FM) |
| `alarm_interval_hr` | Intervalo mínimo entre alarmes repetidos (horas) |
| `snooze_hr` | Duração do snooze de notificações (horas) |
| `check_status_interval` | Frequência do health check de conexão com o DB (horas) |

---

## Fluxo de Funcionamento

```
1. Sensor detecta umidade acima do limite
        ↓
2. Publica leitura via MQTT para IBM Watson IoT Platform
        ↓
3. BDPIncident recebe o evento, verifica nível de urgência
        ↓
4. Cria registro de incidente no banco (BDP_INCIDENT)
        ↓
5. BDPNotifier identifica usuários responsáveis
   (horário comercial vs. fora de expediente)
        ↓
6. Envia notificações: Email + Slack + Tririga (Service Request)
   O email inclui link: /respond?nid=<id>
        ↓
7. Usuário acessa link → vê detalhes + histórico + gráfico
        ↓
8. Usuário escolhe:
   ├── SNOOZE: silencia alarme por N horas
   └── FIXED: marca incidente como resolvido
```

---

## Endpoints REST

Todos os endpoints requerem **HTTP Basic Auth** (credenciais `gateway_user/gateway_password`).

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Health check — retorna versão e status |
| `GET/POST` | `/respond` | UI de resposta a incidentes |
| `POST` | `/tenant` | Cadastrar tenant/organização |
| `POST` | `/user` | Cadastrar usuário com disponibilidade |
| `POST` | `/hardware` | Registrar sensor/detector |

---

## Aviso de Segurança

> **IMPORTANTE:** O código dos sensores contém credenciais hardcoded (tokens IoT, tokens Blynk, credenciais WiFi). Antes de fazer fork ou deploy em produção:
>
> - Gere novos tokens no IBM Watson IoT Platform
> - Gere novo token no Blynk
> - Mova todas as credenciais para variáveis de ambiente ou arquivo de configuração externo
> - **Nunca commite** `config.json` com credenciais reais

---

## Sugestões de Melhorias

- [ ] Substituir credenciais hardcoded nos sensores por variáveis de ambiente ou arquivo `.env`
- [ ] Adicionar arquivo `config.example.json` como template (sem credenciais reais)
- [ ] Criar `docker-compose.yml` com Db2 + App para facilitar setup local completo
- [ ] Atualizar dependências (Flask 1.0.2 → 3.x, Python 3.6 → 3.11+)
- [ ] Adicionar suporte a múltiplos tipos de sensor e protocolos além do IBM Watson IoT
- [ ] Implementar dashboard web para visualização em tempo real dos dados de umidade
- [ ] Adicionar autenticação JWT nos endpoints REST
- [ ] Substituir `ibmiotf` (deprecated) por `ibm-watson-iot` ou MQTT client direto (`paho-mqtt`)

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Sensor (Pi) | Python, Adafruit DHT, ibmiotf, BlynkLib |
| Sensor (ESP) | C++/Arduino, PubSubClient, ESP8266WiFi, Blynk |
| Backend | Python 3.6, Flask 1.0.2, Gevent, Flask-RESTful |
| Banco de Dados | IBM Db2 |
| IoT Platform | IBM Watson IoT Platform (MQTT) |
| Notificações | Gmail SMTP, Slack API, IBM Tririga |
| Deploy | IBM Cloud Foundry, Docker |

---

## Autores

- Rodrigo Brossi — IBM
- Angelo Danducci — IBM
- Hari Hara Prasad Viswanathan — IBM

Desenvolvido para o **Munich Watson IoT Center** — IBM, 2018/2019.
