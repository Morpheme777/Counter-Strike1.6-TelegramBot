# -*- coding: utf-8 -*-

import os
from telebot import apihelper
import telebot
import requests
import sys
from cs_server import CSServer

bot_token = "1227092421:AAHe5fwZy32c5ftOzjaI-1BHY7T4NJAqUKg"
CSCHAT_channel_id = '-309095306'  # CS chat
MPSIEM_channel_id = '-1001129593682'  # MP SIEM chat
DEV_channel_id = '-461964607'  # Valera dev team
channel_id = DEV_channel_id
apihelper.proxy = {
    "https": "socks5://95513393:h60ofuEq@orbtl.s5.opennetwork.cc:999"
}
bot = telebot.TeleBot(bot_token)


def send(bot, message):
    bot.send_message(channel_id, message, parse_mode='markdown')


files = []
for file in os.listdir("data"):
    if file.endswith(".json"):
        files.append(file)
files.sort()
print(files)
