from register import command
from global_vars import CONFIG
import base64
import tempfile
import os
from aip import AipSpeech
import threading
config = CONFIG[__name__]


def plugin():
    return {
        "author": "Antares",
        "version": 1.0,
        "description": "文字朗读"
    }


@command(name="read", help="文字转语音")
def read(bot, context, args):

    if len(args) < 2:
        bot.send(context, "请输入文字")
        return
    string = "".join(args[1:])
    if len(string) > config.MAX_STRING_LENGTH:
        bot.send(context, "字符串过长")
        return

    def handle():
        client = AipSpeech(config.APP_ID, config.API_KEY, config.SECRET_KEY)
        voice = client.synthesis(string, 'zh', 1, {
            'vol': 10,
            'per': 4,
            'spd': 4
        })

        tmpdir = tempfile.mkdtemp()
        audiopath = os.path.join(tmpdir, "audio.mp3")

        if not isinstance(voice, dict):
            with open(audiopath, "wb") as file:
                file.write(voice)
        else:
            bot.send(context, "转换语音失败，请检查是否含有非法字符")
            return

        result = ""
        with open(audiopath, "rb") as file:
            result = base64.encodebytes(file.read()).decode().replace("\n", "")
            bot.send(context, "[CQ:record,file=base64://{}]".format(result))
    threading.Thread(target=handle).start()