from functools import wraps
from .event import EventBase, Listener, EventManager, EventCallback
from typing import Callable, Set, Tuple, NoReturn, Type
from .datatypes import PluginMeta
from abc import abstractclassmethod
from pathlib import Path


def dataclass_wrapper(func):
    @wraps(func)
    def inner():
        from common.datatypes import PluginMeta
        result: PluginMeta = func()
        return {
            "author": result.author,
            "version": result.version,
            "description": result.description
        }
    return inner


class Plugin:

    def __init__(self, event_manager: EventManager, plugin_base_dir: Path):
        self.__event_listeners: Set[Tuple[EventBase, EventCallback]] = set()
        self.event_manager = event_manager
        self.plugin_base_dir = plugin_base_dir

    @property
    def data_dir(self) -> Path:
        return self.plugin_base_dir/"data"

    @property
    def listeners(self) -> Set[Tuple[EventBase, EventCallback]]:
        return self.__event_listeners

    def get_config(self, config_class):
        pass

    @abstractclassmethod
    def get_plugin_meta(self) -> PluginMeta:
        pass

    def register_event_listener(self, event: EventBase, callback: EventCallback) -> NoReturn:
        self.__event_listeners.add((event, callback))
        self.event_manager.register_event(event, callback)

    def unregister_event_listsner(self, event: EventBase, callback: EventCallback) -> NoReturn:
        self.__event_listeners.remove((event, callback))
        self.event_manager.unregister_event(event, callback)

    def register_all_event_listeners(self, listener_class_instance: Listener) -> NoReturn:
        for func in dir(listener_class_instance):
            item = getattr(listener_class_instance, func)
            if not func.startswith("__") and callable(item):
                annotations = item.__annotations__
                if len(annotations) == 1:
                    event_type = list(annotations.values())[0]
                    if issubclass(event_type, EventBase):
                        self.register_event_listener(event_type, item)

    def on_load(self) -> NoReturn:
        pass

    def on_disable(self) -> NoReturn:
        for event, callback in self.__event_listeners:
            self.unregister_event_listsner(event, callback)
