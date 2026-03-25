from aiokafka import AIOKafkaProducer
import json
from pydantic import BaseModel

class KafkaProducerClient:
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._connected = False

    async def start(self):
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            self._connected = True
        except Exception as e:
            print(f"Warning: Failed to connect to Kafka. Mocking producer. {e}")
            self._connected = False

    async def stop(self):
        if self._connected and self.producer:
            await self.producer.stop()

    async def send_event(self, topic: str, value: BaseModel):
        if self._connected and self.producer:
            await self.producer.send_and_wait(topic, value.dict())
        else:
            print(f"[Mock Kafka] Emitting to {topic}: {value.json()}")

kafka_producer = KafkaProducerClient()
