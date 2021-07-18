from typing import Any
from multiprocessing.connection import Connection
from enum import Enum


class Message:
    def __init__(self, code: Enum, data: Any = None):
        self.code = code
        self.data = data

    def __str__(self):
        return f'[{self.code}] {self.data}'


# wrapper for DI
class Messenger:
    def send(self, conn: Connection, msg: Message):
        conn.send(msg)

    def recv(self, conn: Connection) -> Message:
        return conn.recv()

    def poll(self, conn: Connection) -> bool:
        return conn.poll()
