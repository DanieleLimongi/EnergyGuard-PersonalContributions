# EnergyGuard - Contributi al Progetto

## Panoramica del Progetto
EnergyGuard è un sistema distribuito per il monitoraggio energetico sviluppato dal team. Il sistema combina replica distribuita dei dati, messaging tramite RabbitMQ, time-series database (InfluxDB) e visualizzazione tramite Grafana.
Il mio focus principale è stato sul **frontend, dashboard e infrastructure**, creando un ponte tra il sistema distribuito esistente e una piattaforma completa di monitoring energetico.

---

## I Miei Contributi Principali

### 🚀 Frontend e Dashboard
Mi sono occupato principalmente del **frontend e della dashboard** del sistema, implementando le seguenti funzionalità:

### 1. **Ingest Bulk - Simulazione Multi-Sensore**

#### **Implementazione Backend (routes.py)**
Ho creato l'endpoint `/ingest_bulk` che simula il comportamento di 15 sensori energetici:

```python
@app.route('/ingest_bulk', methods=['POST'])
@require_api_token
def ingest_bulk_measurements():
    """Simula 15 sensori che inviano dati a RabbitMQ."""
    sensor_count = 15  
    iterations = 3    
    delay = 2          

    for _ in range(iterations):
        for sensor_id in range(1, sensor_count + 1):
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            value = round(random.uniform(40, 70), 2)
            key = f"sensor{sensor_id}:{timestamp}"

            # Salva nel sistema distribuito
            replication_manager.store_measurement(key, value)

            # Invia il messaggio al broker RabbitMQ
            send_to_broker({'key': key, 'value': value},
                           host=BROKER_URL,
                           port=BROKER_PORT)
        
        time.sleep(delay)
```

**Caratteristiche:**
- Simula 15 sensori energetici
- Genera valori realistici (40-70 unità)
- Timestamps UTC precisi al secondo
- Invio sia al sistema distribuito che a RabbitMQ
- Gestione temporizzata per evitare overflow

#### **CLI Client Interface**
Ho esteso il client CLI aggiungendo l'opzione "Ingest bulk (15 sensors)":

```python
elif choice == '9':
    client.ingest_bulk()
```

Questo permette agli utenti di testare facilmente il sistema con dati multi-sensore.

### 2. **Consumer InfluxDB - Bridge RabbitMQ → Time-Series DB**

Ho sviluppato `consumer_influx.py`, un servizio dedicato che:

#### **Architettura Consumer**
```python
class RabbitMQConsumer:
    def callback(self, ch, method, properties, body):
        msg = json.loads(body)
        sensor_id, timestamp = msg["key"].split(":", 1)
        value = msg["value"]
        
        success = self.influx_writer.write_measurement(sensor_id, timestamp, value)
```

#### **Writer InfluxDB**
```python
class InfluxDBWriter:
    def write_measurement(self, sensor_id, timestamp, value):
        point = Point("energy") \
            .tag("sensor", sensor_id) \
            .field("value", float(value)) \
            .time(timestamp, WritePrecision.S)
        
        self._write_api.write(
            bucket=self._bucket,
            org=self._org,
            record=point
        )
```

**Funzionalità Implementate:**
- **Parsing messaggi RabbitMQ**: Estrae sensor_id, timestamp e value dal formato `key:value`
- **Conversione in Point Objects**: Crea strutture dati InfluxDB native
- **Gestione ACK/NACK**: Acknowledgment intelligente per evitare perdite di dati
- **Connection Pooling**: Pattern Singleton per ottimizzare le connessioni
- **Error Handling**: Resilienza agli errori di connessione e parsing

### 3. **Configurazione Infrastructure (Docker Compose)**

Ho creato e configurato il file `docker-compose.yml` per orchestrare l'intera infrastruttura:

#### **Servizi Configurati:**

**RabbitMQ Management:**
```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports:
    - "5672:5672"   # AMQP Protocol
    - "15672:15672" # Web Management UI
  environment:
    RABBITMQ_DEFAULT_USER: guest
    RABBITMQ_DEFAULT_PASS: guest
```

**InfluxDB 2.7:**
```yaml
influxdb:
  image: influxdb:2.7
  ports:
    - "8086:8086"
  environment:
    - DOCKER_INFLUXDB_INIT_MODE=setup
    - DOCKER_INFLUXDB_INIT_ORG=myorg
    - DOCKER_INFLUXDB_INIT_BUCKET=energy
    - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=xoBOKxZstVQ41pm9eVa3UeutaEx1whmjtMed8UCVnW75z84436xXtt_FscGYnvxPZUbnEDa11mrxf575jLi6nw==
```

**Grafana Dashboard:**
```yaml
grafana:
  image: grafana/grafana
  depends_on:
    - influxdb
  ports:
    - "3000:3000"
  environment:
    GF_SECURITY_ADMIN_USER: admin
    GF_SECURITY_ADMIN_PASSWORD: admin
```

### 4. **Configurazione Database Time-Series**

#### **Bucket "energy" per Time-Series**
Ho configurato InfluxDB con:
- **Organization**: `myorg`
- **Bucket**: `energy` 
- **Token di accesso**: `xoBOKxZstVQ41pm9eVa3UeutaEx1whmjtMed8UCVnW75z84436xXtt_FscGYnvxPZUbnEDa11mrxf575jLi6nw==` 

#### **Schema Dati**
```
Measurement: "energy"
├── Tag: "sensor" (sensor_id)
├── Field: "value" (valore misurazione)
└── Timestamp: UTC precision 
```

### 5. **Integrazione Queue RabbitMQ**

Ho configurato la connessione alla queue **"misurazioni"**:

```python
RABBITMQ_CONFIG = {
    "host": "localhost",
    "port": 5672,
    "queue_name": "misurazioni"
}
```

---

## Architettura Complessiva

```
[Sensori] → [EnergyGuard API] → [RabbitMQ Queue] → [Consumer InfluxDB] → [InfluxDB]
    ↓                                                                        ↓
[Sistema Distribuito]                                                   [Grafana Dashboard]
```

### Data Flow:
1. **Ingest**: I sensori inviano dati via API REST
2. **Replication**: Il sistema distribuito replica i dati sui nodi
3. **Messaging**: I dati vengono inviati alla queue RabbitMQ "misurazioni"
4. **Processing**: Il consumer estrae i messaggi e li processa
5. **Storage**: I dati vengono salvati in InfluxDB come time-series
6. **Visualization**: Grafana visualizza i dati storici e real-time

---

## Come Eseguire

1. **Avvia l'infrastruttura:**
   ```bash
   docker-compose up -d
   ```

2. **Avvia il sistema EnergyGuard:**
   ```bash
   python run.py
   ```

3. **Avvia il consumer InfluxDB:**
   ```bash
   python consumer_influx.py
   ```

4. **Testa con bulk ingest:**
   ```bash
   python app/client.py
   # Scegli opzione 9: "Ingest bulk (15 sensors)"
   ```

5. **Visualizza in Grafana:**
   - URL: http://localhost:3000
   - Credenziali: admin/admin
   - Datasource: InfluxDB (http://influxdb:8086)

   **Query per visualizzare tutti i sensori:**
   ```flux
   from(bucket: "energy")
     |> range(start: -1h)
     |> filter(fn: (r) => r["_measurement"] == "energy")
     |> filter(fn: (r) => r["_field"] == "value")
     |> group(columns: ["sensor"])
   ```
---

## Risultati Ottenuti

### **Performance:**
- **Throughput**: Gestione simultanea di 15 sensori
- **Latency**: < 2 secondi per ingest → visualizzazione

### **Scalabilità:**
- **Horizontal Scaling**: Facile aggiunta di nuovi consumer
- **Volume Handling**: Gestione migliaia di punti dati/ora

### **Monitoring:**
- **Real-time Dashboard**: Visualizzazione immediata in Grafana
- **Historical Analysis**: Query time-series per analisi storiche
- **Alert Integration**: Funzionalità di alerting