import json
import os
from threading import Thread

from confluent_kafka import Producer, Consumer, KafkaError
import sys
import logging

logger = logging.getLogger(__name__)


class KafkaCli(object):
    def __init__(self, *, bootstrap_servers: str, group_id: str, auto_offset_reset: str = 'earliest'):
        self._kafka_producer = None
        self._kafka_consumer = None
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset

    def init_kafka_producer(self):
        try:
            self._kafka_producer = Producer({'bootstrap.servers': self.bootstrap_servers})
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            sys.exit()

    def init_kafka_consumer(self, topics: list):
        try:
            self._kafka_consumer = Consumer({
                'bootstrap.servers': self.bootstrap_servers,
                'group.id': self.group_id,
                'auto.offset.reset': self.auto_offset_reset,
                'enable.auto.commit': False,  # 是否自动提交偏移量
                'default.topic.config': {'auto.offset.reset': 'latest'}  # 默认设置topic的消费的方式
            # ‘smallest’ 每次从最小的offset位置消费，‘latest’ 从最新的offset位置消费数据

            })
            self._kafka_consumer.subscribe(topics)
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            sys.exit()

    def send_message(self, topic, message):
        try:
            self._kafka_producer.produce(topic, message)
            # self._kafka_producer.poll(kafka_producer_timeout)  # kafka_producer_timeout 为超时时间.encode('utf-8')
            self._kafka_producer.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            print(str(e))
            return False

    def consume_messages(self):
        # i = 0
        while True:
            # i = i + 1
            msg = self._kafka_consumer.poll(1.0)#
            print('msg')
            print(msg)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    break
            else:
                message = msg.value().decode('utf-8')
                print('message')
                print(message)
                # yield json.loads(msg.value().decode('utf-8'))
        #     result = json.loads(msg.value().decode('utf-8'))
        #     print('i:' + str(i))
        #     print('msg')
        #     print(msg)
        #     print('result')
        #     print(result)
        #
        #     # return result

    def shutdown(self):
        self._kafka_producer.flush()
        self._kafka_consumer.close()


print('KafkaCli:',os.getenv('KAFKA_BROKER'))

kafka_client = KafkaCli(
    bootstrap_servers=os.getenv('KAFKA_BROKER'),
    # bootstrap_servers='localhost:9092',
    group_id=os.getenv('KAFKA_GROUP_ID')
    # group_id='test'
)

__all__ = ["kafka_client"]
