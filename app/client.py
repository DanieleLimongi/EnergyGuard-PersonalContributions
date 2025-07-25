import json
import os
import requests

class EnergyGuardClient:

    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.check_initialization()

    def check_initialization(self):
        if not self.base_url or not self.headers.get('Authorization'):
            print("Error: Missing base URL or API token.")
            return False
        try:
            response = requests.get(f"{self.base_url}/nodes_status", headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
            exit()
        return True

    def ingest(self, sensor_id, timestamp, value):
        key = f"{sensor_id}:{timestamp}"
        data = {'sensor_id': sensor_id, 'timestamp': timestamp, 'value': value}
        try:
            response = requests.post(f"{self.base_url}/ingest", json=data, headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def get_measurement(self, key):
        try:
            response = requests.get(f"{self.base_url}/measurement/{key}", headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def delete_measurement(self, key):
        try:
            response = requests.delete(f"{self.base_url}/delete/{key}", headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def fail_node(self, node_id):
        try:
            response = requests.post(f"{self.base_url}/fail_node/{node_id}", headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def recover_node(self, node_id):
        try:
            response = requests.post(f"{self.base_url}/recover_node/{node_id}", headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def get_nodes_status(self):
        try:
            response = requests.get(f"{self.base_url}/nodes_status", headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def set_replication_strategy(self, strategy, replication_factor=None):
        data = {'strategy': strategy}
        if replication_factor is not None:
            data['replication_factor'] = replication_factor
        try:
            response = requests.post(f"{self.base_url}/configure_replication", json=data, headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def get_responsible_nodes(self, key):
        try:
            response = requests.get(f"{self.base_url}/replica_nodes/{key}", headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def ingest_bulk(self):
        try:
            response = requests.post(f"{self.base_url}/ingest_bulk", headers=self.headers)
            self.handle_response(response)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def handle_response(self, response):
        try:
            data = response.json()
            if response.status_code == 200:
                print(json.dumps(data, indent=2))
            else:
                print(f"Error {response.status_code}: {data.get('message', 'No details')}")
        except ValueError:
            print(f"Invalid response: {response.text}")


def load_config(path='config/config_client.json'):
    default = {
        "host": "127.0.0.1",
        "port": 5000,
        "API_TOKEN": "your_api_token_here"
    }
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(default, f)
        return default
    with open(path) as f:
        try:
            return {**default, **json.load(f)}
        except Exception:
            return default


if __name__ == '__main__':
    config = load_config()
    base_url = f"http://{config['host']}:{config['port']}"
    token = config['API_TOKEN']

    client = EnergyGuardClient(base_url, token)

    if client.check_initialization():
        print("\nWelcome to EnergyGuard CLI")
        while True:
            print("\nMenu:")
            print("1. Ingest measurement")
            print("2. Get measurement")
            print("3. Delete measurement")
            print("4. Fail node")
            print("5. Recover node")
            print("6. Get nodes status")
            print("7. Set replication strategy")
            print("8. Get responsible nodes")
            print("9. Ingest bulk (15 sensors)")
            print("10. Exit")
            choice = input("Choose an option: ")

            if choice == '1':
                sid = input("Sensor ID: ")
                ts = input("Timestamp: ")
                val = input("Value: ")
                client.ingest(sid, ts, val)
            elif choice == '2':
                k = input("Sensor key (e.g., sensor1:timestamp): ")
                client.get_measurement(k)
            elif choice == '3':
                k = input("Sensor key to delete: ")
                client.delete_measurement(k)
            elif choice == '4':
                nid = input("Node ID to fail: ")
                client.fail_node(nid)
            elif choice == '5':
                nid = input("Node ID to recover: ")
                client.recover_node(nid)
            elif choice == '6':
                client.get_nodes_status()
            elif choice == '7':
                s = input("Strategy (full/consistent): ")
                rf = input("Replication factor (blank if full): ")
                rf = int(rf) if rf.strip().isdigit() else None
                client.set_replication_strategy(s, rf)
            elif choice == '8':
                k = input("Sensor key to inspect: ")
                client.get_responsible_nodes(k)
            elif choice == '9':
                client.ingest_bulk()
            elif choice == '10':
                break
            else:
                print("Invalid choice")
