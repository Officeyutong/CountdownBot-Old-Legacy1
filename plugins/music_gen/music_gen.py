from common.datatypes import PluginMeta
from common.plugin import dataclass_wrapper

from register import command
from global_vars import CONFIG
from pysynth_b import make_wav
from cqhttp import CQHttp
from typing import List, Tuple
from pydub import AudioSegment
import base64
import threading
config = CONFIG[__name__]
plugin = dataclass_wrapper(lambda: PluginMeta(
    author="officeyutong",
    version=1.0,
    description="生成音乐"
))


@command(name="gen", help="生成音乐 | 帮助请使用 genhelp 指令查看")
def generate_music(bot: CQHttp, context: dict, args: List[str] = None):
    notes: List[Tuple[str, int]] = []
    bpm = config.DEFAULT_BPM
    for note_ in args[1:]:
        note = note_.strip()
        if not note:
            continue
        if note.startswith("bpm:"):
            bpm = int(note[note.index(":")+1:])
            continue
        try:
            note_name, duration = note.split(".", 1)
            notes.append((
                note_name, int(duration)
            ))
        except Exception as ex:
            bot.send(context, f"存在非法音符: {note}\n{ex}")
            return

    if len(notes) > config.MAX_NOTES:
        bot.send(context, "超出音符数上限")
        return
    import tempfile
    import os
    wav_output = tempfile.mktemp(".wav")
    mp3_output = tempfile.mktemp(".mp3")
    print(notes)

    def process():
        bot.send(context, "开始生成...")
        make_wav(notes, bpm, fn=wav_output, silent=True)
        song = AudioSegment.from_wav(wav_output)
        song.export(mp3_output)
        print(wav_output, mp3_output)
        with open(mp3_output, "rb") as f:
            base64_data = "[CQ:record,file=base64://{}]".format(
                base64.encodebytes(f.read()).decode(
                    "utf-8").replace("\n", ""))
        os.remove(wav_output)
        os.remove(mp3_output)
        bot.send(context, base64_data)
    threading.Thread(target=process).start()


@command(name="genhelp", help="查看音乐生成器帮助")
def genhelp(bot: CQHttp, context: dict, *args):
    bot.send(context, f"""本功能基于PySynth，通过numpy输出wav的方式生成音频流。

    使用方式:
    gen [bpm:BPM(可选,用于指定BPM数,默认为{config.DEFAULT_BPM})] [音符1] [音符2]....
    其中音符的格式如下:
    [音符名(a-g,r表示休止符)][#或b(可选)][八度(可选,默认为4)][*(可选,表示重音)].[节拍,x表示x分音符]
    例如以下均为合法音符
    c.1   --- 普通的音符C,一拍
    c*.2  --- 普通的音符C,重音,两拍
    g5.3  --- 音符G,高一个八度,三拍
    g5*.1 --- 音符G,高一个八度,重音,一拍
    c#5*.2 --- 音符C,升调,高一个八度,重音,两拍
    c.-2 --- 音符C,二分附点
    以下为部分合法的指令调用:
    gen bpm:130 c.1 d.1 e.1 f.1 g.1 a.1 b.1""")
