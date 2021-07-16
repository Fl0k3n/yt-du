# from abc import ABC
# from utils.events import Event
# from utils.commands.command import Command
# from typing import Callable


# class EventEmitter(ABC):
#     def __init__(self):
#         self.commands = {}

#     def add_event_listener(self, event: Event, command: Command):
#         if event not in self.commands:
#             self.commands[event] = [command]
#         else:
#             self.commands[event].append(command)

#     def call_listeners(self, event: Event):
#         commands = self.commands.get(event)

#         if commands is not None:
#             for command in commands:
#                 command.execute()
