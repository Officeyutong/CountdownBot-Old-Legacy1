from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase


class MyPlugin(Plugin):
    def get_plugin_meta(self):
        return PluginMeta(
            "qwqqwwq", 1.0, "测试一下"
        )


class MyPluginConfig(ConfigBase):
    TEST_URL: str = ""
    

def get_plugin_class():
    return MyPlugin


def get_config_class():
    return MyPluginConfig
