from dataclasses import dataclass
from typing import List, Optional
import requests
from pypresence import Presence
import time
import logging

logging.basicConfig(level=logging.INFO)  # Adjust logging level as needed

@dataclass
class Toy:
    identifier: str
    nickname: str
    name: str
    version: str
    battery: int
    status: int

    @staticmethod
    def from_dict(data: dict) -> "Toy":
        return Toy(
            identifier=data["id"],
            nickname=data["nickName"],
            name=data["name"].capitalize(),
            battery=data["battery"],
            status=data["status"],
            version=data["version"],
        )

@dataclass
class Connection:
    device_id: str
    domain: str
    http_port: int
    https_port: int
    platform: str
    app_version: str
    toys: List[Toy]

    @staticmethod
    def from_dict(data: dict) -> "Connection":
        return Connection(
            device_id=data["deviceId"],
            domain=data["domain"],
            http_port=data["httpPort"],
            https_port=data["httpsPort"],
            platform=data["platform"],
            app_version=data["appVersion"],
            toys=[Toy.from_dict(t) for t in data["toys"].values()],
        )

    def vibrate_toy(self, power_level: int, toy: Optional[Toy] = None) -> bool:
        toy = toy or self.toys[0]  # Default to the first toy if not specified
        url = f"https://{self.domain}:{self.https_port}/Vibrate?v={power_level}&t={toy.identifier}"
        try:
            r = requests.get(url)
            r.raise_for_status()  # Raise an error for bad status codes
            logging.info(f"Vibration request successful for toy {toy.name}")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to vibrate toy {toy.name}: {e}")
            return False

    def stop_vibration(self, toy: Optional[Toy] = None) -> bool:
        toy = toy or self.toys[0]  # Default to the first toy if not specified
        url = f"https://{self.domain}:{self.https_port}/Vibrate?v=0&t={toy.identifier}"
        try:
            r = requests.get(url)
            r.raise_for_status()  # Raise an error for bad status codes
            logging.info(f"Stopped vibration for toy {toy.name}")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to stop vibration for toy {toy.name}: {e}")
            return False

def fetch_connections() -> Optional[List[Connection]]:
    try:
        result = requests.get("https://api.lovense.com/api/lan/getToys")
        result.raise_for_status()  # Raise an error for bad status codes
        data = result.json()
        return [Connection.from_dict(v) for v in data.values()]
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch connections: {e}")
        return None
    except ValueError as e:
        logging.error(f"Failed to parse JSON: {e}")
        return None

CLIENT_ID = "962344637270458388"

if __name__ == "__main__":
    rpc = Presence(CLIENT_ID)
    rpc.connect()

    start_time = time.time()
    while True:
        connections = fetch_connections()
        if connections:
            if connections[0].toys:  # Check if there are toys in the first connection
                toy = connections[0].toys[0]
                rpc.update(
                    details=f"💤 {toy.name} {toy.version}",
                    state=f"🔋 {toy.battery}%",
                    start=start_time,
                    large_image="lovense-logo",
                    buttons=[
                        {"label": "Vibrate", "url": "https://example.com/vibrate"},
                        {"label": "Stop Vibration", "url": "https://example.com/stop"},
                    ]
                )
            else:
                logging.warning("No toys found in the first connection.")
        else:
            logging.error("Failed to fetch connections or no connections available.")

        time.sleep(5)

