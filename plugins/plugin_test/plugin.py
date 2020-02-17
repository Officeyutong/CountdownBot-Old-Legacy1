from common.plugin import Plugin
from common.datatypes import PluginMeta


class MyPlugin(Plugin):
    def get_plugin_meta(self):
        return PluginMeta(
            "qwqqwwq", 1.0, "测试一下"
        )


def get_plugin_class():
    return MyPlugin
