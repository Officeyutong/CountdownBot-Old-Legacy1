from io import StringIO
from util import print_log
from register import command
from global_vars import CONFIG
import threading
config = CONFIG[__name__]


def plugin():
    return {
        "author": "Antares",
        "version": 1.0,
        "description": "历史上的今天"
    }


def get_histroy(date: str, key: str) -> list:
    url = f"http://v.juhe.cn/todayOnhistory/queryEvent.php?key={key}&date={date}"
    import json
    import urllib.request
    try:
        with urllib.request.urlopen(url) as urlf:
            data = json.JSONDecoder().decode(urlf.read().decode("utf-8"))
        return data['result']
    except Exception as err:
        print_log(err)
        return []


@command(name="histroy", help="历史上的今天，参数为月和日")
def history(bot, context, args):
    while args[-1] == "":
        del args[-1]

    def handle():
        import datetime
        today = datetime.date.today()
        date = f"{today.month}/{today.day}"
        if len(args) == 3:
            try:
                month = int(args[1])
                day = int(args[2])
            except ValueError as err:
                print_log(err)
                bot.send(context, "请输入合法的日期")
                return

            if month < 1 or month > 12:
                bot.send(context, "月份不合法")
                return

            if day < 1 or day > 31:
                bot.send(context, "日期不合法")
                return

            date = f"{month}/{day}"

        result = get_histroy(date, config.APP_KEY)[::-1]
        if len(result) == 0:
            bot.send(context, "无结果")
            return

        buf = StringIO()
        buf.write(f"查询日期: {date}\n\n")
        count = 0
        for item in result:
            buf.write(f"{item['date']} {item['title']}\n")
        
        bot.send(context,buf.getvalue())

    threading.Thread(target=headle).start()
