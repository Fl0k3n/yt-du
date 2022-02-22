import json
from typing import Any
from enum import Enum
from multiprocessing.connection import Connection


class Message:
    def __init__(self, code: Enum, data: Any = None):
        self.code = code
        self.data = data

    def __str__(self):
        return f'[{self.code}] {self.data}'

    def to_json(self) -> str:
        """Make sure that data can be converted to json"""
        return json.dumps({
            'code': self.code.value,
            'data': self.data
        })

    @staticmethod
    def from_json(enum_type: type, json_data) -> 'Message':
        data = json.loads(json_data)
        return Message(enum_type(data['code']), data['data'])


class DlData:
    def __init__(self, task_id: int, data: Any = None):
        self.task_id = task_id
        self.data = data

    def __str__(self) -> str:
        return f'#{self.task_id}: {self.data}'


# wrapper for DI
class Messenger:
    def send(self, conn: Connection, msg: Message):
        conn.send(msg)

    def recv(self, conn: Connection) -> Message:
        return conn.recv()

    def poll(self, conn: Connection) -> bool:
        return conn.poll()
