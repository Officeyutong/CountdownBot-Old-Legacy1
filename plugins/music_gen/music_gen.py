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
config = CONFIG.get(__name__, None)
plugin = dataclass_wrapper(lambda: PluginMeta(
    author="officeyutong",
    version=1.0,
    description="生成音乐"
))


def parse_major(major_note: str) -> int:
    """
    解析基准音,返回绝对音高
    [b或#或忽略][音符]
    """
    BASE_MAPPING = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11
    }
    result = 0
    if major_note[0] in {"b", "#"}:
        result += {"b": -1, "#": 1}[major_note[0]]
        major_note = major_note[1:]
    return result+BASE_MAPPING[major_note[0].upper()]


def parse_note(note: str) -> int:
    """
    解析简谱,返回绝对音高
    [b或#或忽略][音符][八度(默认为4)]
    例如#12 #23
    """
    NOTE_LIST = [0, 2, 4, 5, 7, 9, 11]
    result = 0
    if note[0] in {"#", "b"}:
        result += {"b": -1, "#": 1}[note[0]]
        note = note[1:]
    note_chr = note[0]
    octave = 4
    # starred = False
    # left, right = note[1:].split(".", 1)
    if len(note) == 2:
        octave = int(note[1])
    # print("octave =", octave)
    result += NOTE_LIST[ord(note_chr)-ord('1')]
    result += 12*octave
    return result


def transform_single_note(note: str, major_height: int) -> str:
    NOTE_LIST = ["c", "c#", "d", "d#", "e",
                 "f", "f#", "g", "g#", "a", "a#", "b"]

    note, duration = note.split(".", 1)
    starred = note[-1] == '*'
    if starred:
        note = note[:-1]
    height = major_height+parse_note(note)
    return f"{NOTE_LIST[height%12]}{height//12}{'*' if starred else ''}.{duration}"

# 将简谱转换为PySynth谱


def transform_notes(notes: List[str], major: str):
    """
    转换全部音符
    每个音符形如[#或b或空][1...7][八度(可空,默认为4)][*加重符号,可选].[节拍]

    输出形如
    [a...g音符名][#或b,可选][八度,可空,默认为4][*加重符号].[节拍]
    """
    major_height = parse_major(major)
    result = []
    for note in notes:
        if "r" not in note:
            result.append(transform_single_note(note, major_height))
        else:
            result.append(note)
    return result


@command(name="noteconvert", help="转换简谱 | 使用genhelp指令查看帮助")
def noteconvert(bot: CQHttp, context: dict, args: List[str] = None):
    args = args[1:]
    major = "C"
    filtered = []
    try:
        for note in args:
            note = note.strip()
            if note:
                if note.startswith('major:'):
                    major = note[note.index(":")+1:]
                else:
                    filtered.append(note)
        bot.send(context, " ".join(transform_notes(filtered, major)))
    except Exception as ex:
        bot.send(f"发生错误: {ex}")


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
                # if abs(float(duration)) < 1:
                #     raise ValueError("abs(Duration) >= 1")
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
    c.1   --- 普通的音符C,四拍
    c*.2  --- 普通的音符C,重音,两拍
    g5.3  --- 音符G,高一个八度,三分之四个四分音符
    g5*.1 --- 音符G,高一个八度,重音,四拍
    c#5*.2 --- 音符C,升调,高一个八度,重音,两拍
    c.-2 --- 音符C,二分附点
    以下为部分合法的指令调用:
    gen bpm:130 c.1 d.1 e.1 f.1 g.1 a.1 b.1
    
    以下内容来自PySynth文档:
    # Dotted notes can be written in two ways:
    # 1.33 = -2 = dotted half
    # 2.66 = -4 = dotted quarter
    # 5.33 = -8 = dotted eighth

    关于简谱转换:
    可以使用notecover指令从简谱转换谱子到PySynth的格式
    其使用方式为
    noteconvert [major:大调,可选,例如#G,A,C,默认为C] [简谱音符1] [简谱音符2]...
    其中简谱音符的格式为:
    [音符,1...7][#或b或留空(表示升调或降调)][八度(可空,默认为4)][*,重音符号,可空].[节拍]
    其中节拍参考PySynth谱部分
    以下为合法的指令调用:
    noteconvert major:bB 5.4 3.4 2.4 1.4 2.8 1.8 2.4 5.-4 r.8 5.4 3.4 2.4 1.4 2.8 1.8 5.4 3.-4 r.8
    """)
