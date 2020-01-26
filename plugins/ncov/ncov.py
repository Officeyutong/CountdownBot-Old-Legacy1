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
    with requests.get("https://3g.dxy.cn/newh5/view/pneumonia") as urlf:
        soup = bs4.BeautifulSoup(urlf.content.decode("utf-8"), "lxml")
    script = soup.select_one("#getAreaStat")
    expr = re.compile(r"(\[.*\])")

    data: List[Dict[str, dict]] = json.JSONDecoder().decode(
        expr.search(script.string).groups()[0])
    broadcast = soup.select_one(".content___2hIPS")
    # print(broadcast.text)
    from io import StringIO
    buf = StringIO()
    buf.write(broadcast.text)
    buf.write("\n\n")

    def generate_line(obj):
        return f"{obj['provinceName'] if 'provinceName' in obj else obj['cityName']} 已确认 {obj['confirmedCount']} 疑似 {obj['suspectedCount']} 治愈 {obj['curedCount']} 死亡 {obj['deadCount']}"

    def handle_province(obj):
        buf.write(generate_line(obj))
        buf.write("\n")
        for city in obj["cities"]:
            buf.write(generate_line(city)+"\n")
        # print(buf.getvalue())
        bot.send(context, buf.getvalue())

    def handle_global():

        for item in data:
            buf.write(generate_line(item)+"\n")
        # print(buf.getvalue())
        bot.send(context, buf.getvalue())

    while args and args[-1].strip() == "":
        args.pop()
    print(args)
    if len(args) == 1:
        handle_global()
    else:
        for item in data:
            if args[1] in item["provinceShortName"]:
                handle_province(item)
                return
        bot.send(context, "请输入正确的省份名称")
