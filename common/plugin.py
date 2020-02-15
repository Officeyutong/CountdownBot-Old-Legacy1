from functools import wraps


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
    def __init__(self):
        pass
    # def register_event(self,)
