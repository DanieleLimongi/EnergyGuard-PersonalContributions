# EnergyGuard – Project Contributions

## Project Overview
**EnergyGuard** is a distributed energy monitoring system developed by the team.  
The system combines distributed data replication, messaging through **RabbitMQ**, time-series storage using **InfluxDB**, and visualization via **Grafana**.  

My main focus was on the **frontend, dashboard, and infrastructure**, building a bridge between the existing distributed system and a complete energy monitoring platform.

---

## My Main Contributions

### 🚀 Frontend and Dashboard
I primarily worked on the **frontend and dashboard** of the system, implementing the following key features:

### 1. **Ingest Bulk – Multi-Sensor Simulation**

#### **Backend Implementation (routes.py)**
I developed the `/ingest_bulk` endpoint, simulating the behavior of 15 energy sensors:

```python
@app.route('/ingest_bulk', methods=['POST'])
@require_api_token
def ingest_bulk_measurements():
    """Simulate 15 sensors sending data to RabbitMQ."""
    sensor_count = 15  
    iterations = 3    
    delay = 2          

    for _ in range(iterations):
        for sensor_id in range(1, sensor_count + 1):
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            value = round(random.uniform(40, 70), 2)
            key = f"sensor{sensor_id}:{timestamp}"

            # Save in the distributed system
            replication_manager.store_measurement(key, value)

            # Send the message to the RabbitMQ broker
            send_to_broker({'key': key, 'value': value},
                           host=BROKER_URL,
                           port=BROKER_PORT)
        
        time.sleep(delay)
