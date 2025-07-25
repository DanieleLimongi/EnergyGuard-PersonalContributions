# consumer_influx.py ( prendiamo i dati da RabbitMQ e li registriamo in InfluxDB)
import json
import pika #libreria per Rabbit
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS #libreria per InfluxDB

class InfluxDBWriter:

    _instance = None
    _client = None
    _write_api = None

    def __new__(cls, url, token, org, bucket):
        if cls._instance is None:
            cls._instance = super(InfluxDBWriter, cls).__new__(cls)
            cls._client = InfluxDBClient(url=url, token=token, org=org)
            cls._write_api = cls._client.write_api(write_options=SYNCHRONOUS)
            cls._org = org
            cls._bucket = bucket
            print(f"[INFLUX] Connessione a InfluxDB stabilita: {url}")
        return cls._instance

    def write_measurement(self, sensor_id, timestamp, value):
        """Scrive una misurazione in InfluxDB"""
        try:
            point = Point("energy") \
                .tag("sensor", sensor_id) \
                .field("value", float(value)) \
                .time(timestamp, WritePrecision.S)
            
            self._write_api.write(
                bucket=self._bucket,
                org=self._org,
                record=point
            )
            return True
        except Exception as e:
            print(f"[INFLUX ERROR] {e}")
            return False

    def close(self):
        if self._client:
            self._client.close()
            print("[INFLUX] Connessione InfluxDB chiusa")

class RabbitMQConsumer:
    def __init__(self, host, port, queue_name, influx_writer):
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.influx_writer = influx_writer

    def callback(self, ch, method, properties, body):
        try:
            msg = json.loads(body) # msg json diventa un dizionario
            sensor_id, timestamp = msg["key"].split(":", 1) # separiamo la key in sensore e timestamp
            value = msg["value"]

            success = self.influx_writer.write_measurement(sensor_id, timestamp, value)
            
            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"[INFLUX] {sensor_id}@{timestamp} → {value}")
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        except Exception as e:
            print(f"[ERROR] Errore nel processare il messaggio: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host, port=self.port)
        )
        channel = connection.channel()
        channel.queue_declare(queue=self.queue_name, durable=True) #declare la coda 

        # limite 1 solo mess per volta
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback,
            auto_ack=False  # gestione manuale dell'ack per evitare perdite di dati
        )

        print(" [*] In attesa di messaggi. Ctrl+C per uscire")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            print("Consumer interrotto dall'utente")
        finally:
            connection.close()

# --- Config InfluxDB --- registra le misurazioni
INFLUX_CONFIG = {
    "url": "http://localhost:8086",
    "token": "xoBOKxZstVQ41pm9eVa3UeutaEx1whmjtMed8UCVnW75z84436xXtt_FscGYnvxPZUbnEDa11mrxf575jLi6nw==",
    "org": "myorg",
    "bucket": "energy"
}

# --- Config RabbitMQ ---
RABBITMQ_CONFIG = {
    "host": "localhost",
    "port": 5672,
    "queue_name": "misurazioni"
}

if __name__ == "__main__":
    # Inizializza writer InfluxDB (Singleton)
    influx_writer = InfluxDBWriter(**INFLUX_CONFIG)
    
    # Inizializza e avvia consumer
    consumer = RabbitMQConsumer(
        **RABBITMQ_CONFIG,
        influx_writer=influx_writer
    )
    
    try:
        consumer.start_consuming()
    finally:
        influx_writer.close()
# avvia il consumer e inizializza con InfluxDB