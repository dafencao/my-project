from typing import Any

from kafka import KafkaProducer

from common.session import BaseModel
from peewee import CharField, IntegerField, DateTimeField, JOIN, Model, fn

class KafkaModel(BaseModel):

    message = CharField()

    @classmethod
    async def producer_send(cls,
                            msg: str,
                            value: Any = None
                            ):
        producer = KafkaProducer(bootstrap_servers='localhost:9092')
        # msg = str('%' + msg + '%')
        producer.send(msg)
