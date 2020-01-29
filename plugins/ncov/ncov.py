from register import command
from cqhttp import CQHttp
from typing import List, Dict


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "丁香园2019nCov疫情播报"
    }


@command(name="ncov", help="查询2019nCov疫情 | ncov (省名)")
def dxy_query(bot: CQHttp, context=None, args: List[str] = None):
    import bs4
    import requests
    import re
    import json
    import time
    import datetime
    with requests.get("https://3g.dxy.cn/newh5/view/pneumonia") as urlf:
        soup = bs4.BeautifulSoup(urlf.content.decode("utf-8"), "lxml")
    script = soup.select_one("#getAreaStat")
    expr = re.compile(r"(\[.*\])")

    data: List[Dict[str, dict]] = json.JSONDecoder().decode(
        expr.search(script.string).groups()[0])
    statistics = json.JSONDecoder().decode(re.compile(
        r"= (\{.*\})\}catch").search(soup.select_one("#getStatisticsService").string).groups()[0])

    # broadcast = soup.select_one(".count___3GCdh)
    total_confirmed = sum((item["confirmedCount"] for item in data))
    total_suspected = sum((item["suspectedCount"] for item in data))
    total_cured = sum((item["curedCount"] for item in data))
    total_dead = sum((item["deadCount"] for item in data))
    update_time: time.struct_time = time.localtime(
        statistics["modifyTime"]//1000)
    broadcast = f"{total_confirmed} 确认 | {total_suspected} 疑似 | {total_cured} 治愈 | {total_dead} 死亡\n更新于{time.strftime('%Y.%m.%d %H:%M:%S', update_time)}"
    from io import StringIO
    buf = StringIO()
    buf.write("数据来源: 丁香医生\n")
    # buf.write(str(soup.select_one(".title___2d1_B").cmd.text)+"\n")
    buf.write(broadcast)
    buf.write("\n\n")

    def generate_line(obj):
        return f"{obj['provinceName'] if 'provinceName' in obj else obj['cityName']} 已确认 {obj['confirmedCount']} 疑似 {obj['suspectedCount']} 治愈 {obj['curedCount']} 死亡 {obj['deadCount']}"

    def handle_province(obj):
        buf.write(generate_line(obj))
        buf.write("\n\n")
        for city in obj["cities"]:
            buf.write(generate_line(city)+"\n")
        bot.send(context, buf.getvalue())

    def handle_global():
        for item in data:
            buf.write(generate_line(item)+"\n")
        bot.send(context, buf.getvalue())

    while args and args[-1].strip() == "":
        args.pop()
    print(args)
    if len(args) == 1:
        handle_global()
    else:
        for item in data:
            if args[1] in item["provinceName"]:
                handle_province(item)
                return
        bot.send(context, "请输入正确的省份名称")


@command(name="ncovnews", help="查询2019nCov最近5条实时播报")
def ncov_news(bot: CQHttp, context=None, args: List[str] = None):
    import bs4
    import requests
    import re
    import json
    import time
    import datetime
    with requests.get("https://3g.dxy.cn/newh5/view/pneumonia") as urlf:
        soup = bs4.BeautifulSoup(urlf.content.decode("utf-8"), "lxml")
    script = soup.select_one("#getTimelineService")
    expr = re.compile(r"(\[.*\])")

    data: List[Dict[str, dict]] = json.JSONDecoder().decode(
        expr.search(script.string).groups()[0])
    statistics = json.JSONDecoder().decode(re.compile(
        r"= (\{.*\})\}catch").search(soup.select_one("#getStatisticsService").string).groups()[0])
    update_time: time.struct_time = time.localtime(
        statistics["modifyTime"]//1000)
    # print(broadcast.text)
    from io import StringIO
    buf = StringIO()
    buf.write(
        f"数据来源: 丁香医生\n更新于{time.strftime('%Y.%m.%d %H:%M:%S', update_time)}")
    # buf.write(str(soup.select_one(".mapTitle___2QtRg").text)+"\n")
    buf.write("\n\n")
    for item in data[:5]:
        buf.write(f"""{item["title"]} - {item["infoSource"]} - {item["pubDateStr"]}
        {item["sourceUrl"]}
        {item["summary"]}

        """)
    bot.send(context, buf.getvalue())
