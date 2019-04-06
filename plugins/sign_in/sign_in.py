#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from register import command
import global_vars
import os
import re
import json
import random
from datetime import datetime, date, timedelta
from json import JSONDecoder, JSONEncoder
web_app = global_vars.VARS["web_app"]
DATA_PATH = os.path.join(os.path.dirname(__file__),"data/")
config = global_vars.CONFIG[__name__]


def plugin():
    return {
        "author": "Antares",
        "version": 2.0,
        "description": "签到支持"
    }


def load():
    # web_app =
    pass


@command(name="签到", help="签到")
def sign_in(bot, context, args):
    bot.send(context, get_reply(context))

def load_data(group_id, user_id):

    # mkdir ./data
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    group_path = os.path.join(DATA_PATH,
                              "group-%s/" % (group_id))

    # mkdir ./data/group-*
    if not os.path.exists(group_path):
        os.makedirs(group_path)

    # open./data/group-*/user-*json
    file_path = os.path.join(group_path,"user-%s.json" % (user_id)) 

    # read or touch json
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        with open(file_path, "w") as file:
            data = {
                "rating": 0,
                "times_all": 0,
                "times_month": 0,
                "date": "0001-01-01",
                "days": 0
            }
            file.write(json.JSONEncoder().encode(data))

    return data

def save_data(data, group_id,user_id):
    from global_vars import config
    import os
    import json

    # open file ./data/group-*/user-*.json
    file_path = os.path.join(DATA_PATH,
                             "group-%s/" % (group_id),
                             "user-%s.json" % (user_id))

    # write json
    with open(file_path, "w") as f:
        json.dump(data, f)

def get_reply(context):
    group_id = str(context['group_id'])

    if group_id in config.BLACK_LIST_GROUPS:
        return "签到功能在本群停用"

    sender = context['sender']
    user_id = str(sender['user_id'])
    nickname = sender['nickname']
    
    user_data = load_data(group_id, user_id)

    today = datetime.strptime(str(date.today()), '%Y-%m-%d')
    yesterday = today - timedelta(days=1)
    last_day = datetime.strptime(user_data['date'], '%Y-%m-%d')

    # 比较上次签到时间，今日已经签到
    if last_day == today:
        return "%s今天已经签过到了！\n连续签到：%d天\n当前积分：%d\n本月签到次数：%d\n累计群签到次数：%d" % (
            nickname, user_data['days'], user_data['rating'], user_data['times_month'], user_data['times_all'])

    # 清零上个月
    if last_day.month != today.month or last_day.year != today.year:
        user_data['times_month'] = 0

    # 连续签到    
    if last_day == yesterday:
        user_data['days'] += 1
    else:
        user_data['days'] = 1
        
    # 签到
    delta_days = (user_data['days']-1)*3
    if delta_days > 30:
        delta_days = 30
    delta = random.randint(10, 50)+delta_days;
    user_data['rating'] += delta
    user_data['times_month'] += 1
    user_data['times_all'] += 1
    user_data['date'] = str(date.today())

    save_data(user_data, group_id, user_id)
    return "给%s签到成功了！\n连续签到：%s天\n积分增加：%d\n连续签到加成：%d\n当前积分：%d\n本月签到次数：%d\n累计群签到次数：%d" % (
        nickname, user_data['days'], delta, delta_days, user_data['rating'], user_data['times_month'], user_data['times_all'])

@web_app.route("/api/credit/get_by_group/<int:group_id>", methods=["POST", "GET"])
def get_credit_by_group(group_id: int):
    if not os.path.exists(os.path.join(DATA_PATH, "group-{}".format(group_id))):
        return JSONEncoder().encode({
            "message": "Group not found.",
            "status": -1
        })
    
    group_path = os.path.join(DATA_PATH,
                              "group-{}/".format(group_id))

    pattern = re.compile(r"user-([0-9]+)\.json")

    data = {}
    for user in os.listdir(group_path):
        user_id = pattern.findall(user)[0]
        data[user_id] = load_data(group_id,user_id)

    result = []
    for key in data:
        data[key]["id"] = key
        result.append(data[key])
    result.sort(key=lambda x: x["rating"], reverse=True)
    return JSONEncoder().encode(result)

@web_app.route("/api/credit/get_groups", methods=["POST", "GET"])
def get_groups():
    result = []
    pattern = re.compile(r"group-([0-9]+)")
    for group in os.listdir(DATA_PATH):
        result.append(pattern.findall(group)[0])
    return JSONEncoder().encode(result)
