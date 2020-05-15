# -*- coding: utf-8 -*-

from telebot import apihelper
import telebot
import requests
import sys
from cs_server import CSServer


print("started")
bot_token = "1227092421:AAHe5fwZy32c5ftOzjaI-1BHY7T4NJAqUKg"
channel_id = '-309095306' # CS chat
channel_id = '-1001129593682' # MP SIEM chat
apihelper.proxy = {"https":"socks5://95513393:h60ofuEq@orbtl.s5.opennetwork.cc:999"}

def send(bot, message):
    bot.send_message(channel_id, message)

def getCSServerStats():
    cs_server = CSServer("api.ds-host.ru", "morpheme", "zaqXSW12!@")
    r = cs_server.getServerStats()
    msg = u"\U0001F4A3\U0001F4A3\U0001F4A3\nServer: {}\nMap: {}\nPlayers: {}\n{}".format(
        r['data']['hostname'],
        r['data']['map'],
        r['data']['currentPlayers'],
        ', '.join(['{} [{}]'.format(x['name'], x['score']) for x in r['data']['players']])
    )
    return msg



def main():

    bot = telebot.TeleBot(bot_token)

    @bot.message_handler(commands=['stat'])
    def send_welcome(message):
        msg = getCSServerStats()
        print(msg)
        bot.reply_to(message, msg)

    bot.polling()

    #msg = getCSServerStats()
    #send(bot, msg)

if __name__=='__main__':
    main()
