from collections import namedtuple
try:
    import config
except ModuleNotFoundError as ex:
    import config_default as config
loaded_plugins = []
registered_commands = {

}

message_listeners = [

]
loop_threads = []
last_message = None
repeat_time = 0
VARS = {
    "bot": None
}
