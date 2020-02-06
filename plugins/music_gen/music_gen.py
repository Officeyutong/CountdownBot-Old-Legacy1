from common.datatypes import PluginMeta
from common.plugin import dataclass_wrapper

from register import command
from global_vars import CONFIG
from pysynth_b import make_wav, mix_files
from cqhttp import CQHttp
from typing import List, Tuple
from pydub import AudioSegment
import base64
import threading
import tempfile
import os
import sox
# import numpy as np
# import wave
config = CONFIG[__name__]
plugin = dataclass_wrapper(lambda: PluginMeta(
    author="officeyutong",
    version=1.0,
    description="生成音乐"
))


# @command(name="gencomp",help="将简谱")

@command(name="gen", help="生成音乐 | 帮助请使用 genhelp 指令查看")
def generate_music(bot: CQHttp, context: dict, args: List[str] = None):
    tracks: List[List[Tuple[str, int]]] = []
    bpm = config.DEFAULT_BPM

    def process_track(string: str):
        notes: List[Tuple[str, int]] = []
        print(f"Processing track '{string}'")
        for note_ in string.split(" "):
            note = note_.strip()
            if not note:
                continue
            if note.startswith("bpm:"):
                nonlocal bpm
                bpm = int(note[note.index(":")+1:])
                continue
            try:
                note_name, duration = note.split(".", 1)
                if abs(float(duration)) < 1:
                    raise ValueError("abs(Duration) >= 1")
                notes.append((
                    note_name, float(duration)
                ))
            except Exception as ex:
                bot.send(context, f"存在非法音符: {note}\n{ex}")
                raise ValueError(f"存在非法音符: {note}\n{ex}")
        return notes
    string = " ".join(args[1:])

    for track_string in string.split("|"):
        track_string = track_string.strip()

        if track_string:
            print("track:"+track_string)
            tracks.append(process_track(track_string))
    print(tracks)

    if sum((len(x) for x in tracks)) > config.MAX_NOTES:
        bot.send(context, "超出音符数上限")
        return

    mp3_output = tempfile.mktemp(".mp3")

    def process():
        track_files: List[str] = []
        combiner = sox.Combiner()
        bot.send(context, f"生成中...共计{len(tracks)}个音轨")
        for i, track in enumerate(tracks):
            track_file = tempfile.mktemp(".wav")
            try:
                make_wav(
                    track, bpm, fn=track_file, silent=True
                )
            except Exception as ex:
                bot.send(context, f"音轨{i+1}出现错误: {ex}")
                raise ex
            track_files.append(track_file)
        print(track_files)
        if len(track_files) == 1:
            wav_output = track_files[0]
        else:
            wav_output = tempfile.mktemp(".wav")
            combiner.build(track_files, wav_output, "merge")
        song = AudioSegment.from_wav(wav_output)
        song.export(mp3_output)
        with open(mp3_output, "rb") as f:
            base64_data = "[CQ:record,file=base64://{}]".format(
                base64.encodebytes(f.read()).decode(
                    "utf-8").replace("\n", ""))
        os.remove(wav_output)
        os.remove(mp3_output)
        for file in track_files:
            if os.path.exists(file):
                os.remove(file)
        bot.send(context, base64_data)
    threading.Thread(target=process).start()


@command(name="genhelp", help="查看音乐生成器帮助")
def genhelp(bot: CQHttp, context: dict, *args):
    bot.send(context, f"""本功能基于PySynth，通过numpy输出wav的方式生成音频流。

    使用方式:
    gen [bpm:BPM(可选,用于指定BPM数,默认为{config.DEFAULT_BPM})] [音轨1:音符1] [音轨1:音符2]....| [音轨2:音符1] [音轨2:音符2...]

    其中以|分割不同音轨
    其中音符的格式如下:
    [音符名(a-g,r表示休止符)][#或b(可选,#为升调,b为降调)][八度(可选,默认为4)][*(可选,表示重音)].[节拍,x表示x分音符,-x表示x分附点]
    例如以下均为合法音符
    c.1   --- 普通的音符C,一拍
    c*.2  --- 普通的音符C,重音,两拍
    g5.3  --- 音符G,高一个八度,三拍
    g5*.1 --- 音符G,高一个八度,重音,一拍
    c#5*.2 --- 音符C,升调,高一个八度,重音,两拍
    c.-2 --- 音符C,二分附点
    以下为部分合法的指令调用:
    gen bpm:130 c.1 d.1 e.1 f.1 g.1 a.1 b.1""")
