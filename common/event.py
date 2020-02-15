from abc import abstractmethod
from typing import List, Callable


class ListenerBase:
    @abstractmethod
    def invoke(self):
        pass


class CommandEventListsner(ListenerBase):
    def __init__(self, command_name, callback: Callable[[str, List[str], str, dict], None]):
        self.command_name = command_name
        self.callback = callback

    def invoke(self, command_name: str, args: List[str], raw_string: str, context: dict):
        return self.callback(command_name, args, raw_string, context)


# class MessageEventListener(ListenerBase):
#     def __init__(self,)