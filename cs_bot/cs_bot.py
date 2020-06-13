# -*- coding: utf-8 -*-

from telebot import apihelper
import telebot
import requests
import sys
from cs_server import CSServer
from csdata import CSStats
import re
import os

bot_token = "1227092421:AAHe5fwZy32c5ftOzjaI-1BHY7T4NJAqUKg"
channel_id = '-309095306' # CS chat
channel_id = '-1001129593682' # MP SIEM chat
#apihelper.proxy = {"https":"socks5://95513393:h60ofuEq@orbtl.s5.opennetwork.cc:999"}
#apihelper.proxy = {"https":"socks5://95513393:h60ofuEq@grsst.s5.opennetwork.cc:999"}
#apihelper.proxy = {"https":"socks5://igor:1qaz!QAZ@timur.no-ip.biz:2831"}
WORK_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FOLDER = WORK_DIR + "/data"
IMG_FOLDER = WORK_DIR + '/img'

def send(bot, message):
    bot.send_message(channel_id, message)

def getCSServerStats():
    cs_server = CSServer("api.ds-host.ru", "morpheme", "zaqXSW12!@")
    r = cs_server.getServerStats()
    msg = u"Map: {}\nPlayers: {}\n{}".format(
        r['data']['map'],
        r['data']['currentPlayers'],
        ', '.join(['{} [{}]'.format(x['name'], x['score']) for x in r['data']['players']])
    )
    return msg



def main():

    bot = telebot.TeleBot(bot_token)

    def help(command, error = ""):
        if command == 'stat':
            msg = "Usage: /stat nickname\n{}".format(error)
            return msg
        if command == 'srv':
            msg = "Usage: /srv\n{}".format(error)
            return msg
        if command == 'rank':
            msg = "Usage: /rank\n{}".format(error)
            return msg
        if command == 'pvp':
            msg = "Usage: /pvp\n{}".format(error)
            return msg
        if command == 'dev':
            msg = "Usage: /dev\n{}".format(error)
            return msg
        else:
            msg = "something wrong"

    @bot.message_handler(commands=['help'])
    def user_stat(message):
        msg = "\n".join([
            help('stat', 'Статистика игрока. Пунктир - статистика за сутки, сплошная линия - усредненное значение.\n'),
            help('srv', 'Статус сервера: карта, кол-во игроков, список игроков.\n'),
            help('rank', "Рейтинг игроков. Обновляется раз в час.\n"),
            help('pvp', "Отношение kills/deaths в PvP. Зеленое - хорошо, красное - плохо. Обновляется раз в час.\n")
        ])
        bot.reply_to(message, msg)

    @bot.message_handler(commands=['srv'])
    def user_srv(message):
        msg = getCSServerStats()
        msg = "\U0001F4A3\U0001F4A3\U0001F4A3\n{}".format(msg)
        bot.reply_to(message, msg)

    @bot.message_handler(commands=['stat'])
    def user_stat(message):
        msg = message.text
        chat_id = message.chat.id
        msg_arg = re.findall('/stat\s(.*)', msg)
        if not msg_arg:
            bot.send_message(chat_id, help('stat', "Nickname is required"))
            return 0
        msg_arg = msg_arg[0]
        csstats = CSStats()
        csdata_file = '{}/csdata.dat'.format(DATA_FOLDER)
        csstats.downloadFile(csdata_file)
        csstats.decodeFile(csdata_file)
        players = csstats.players_stat
        player = {}
        for p in players:
            if p['name'] == msg_arg:
                if p['auth'] == 'STEAM_0:0:1091943949':
                    continue
                player = p
        if not player:
            bot.send_message(chat_id, help('stat', "Cannot find stats for {}".format(msg_arg)))
            return 0
        chat_id = message.chat.id
        msg_stat = """{}\n\U0001F396 Kills: {}\n\U0001F480 Deaths: {}\n\U0001F3AF Accuracy: {}\n\U0001F4AA Efficiency: {}""".format(
            player['name'],
            player['kills'],
            player['deaths'],
            str(round(sum(player['hits'])/player['shots']*100, 1))+"%",
            str(round(int(player['kills'])/(player['kills']+player['deaths'])*100, 2))+"%"
        )
        #bot.reply_to(message, msg_stat)
        try:
            pic = open('{}/{}.png'.format(IMG_FOLDER,msg_arg), 'rb')
            bot.send_photo(chat_id, photo = pic, caption = msg_stat)
        except Exception as e:
            bot.send_message(chat_id, "{}\n{}".format(msg_stat,help('dev', "Cannot find trend stats for {}".format(msg_arg))))

    @bot.message_handler(commands=['rank'])
    def user_rank(message):
        chat_id = message.chat.id
        try:
           pic = open('{}/{}.png'.format(WORK_DIR,'ranking'), 'rb')
           bot.send_photo(chat_id, photo = pic, caption = "")
        except Exception as e:
           bot.send_message(chat_id, help('rank', "Cannot find rank file.. sorry"))


    @bot.message_handler(commands=['pvp'])
    def user_rank(message):
        chat_id = message.chat.id
        try:
           pic = open('{}/{}.png'.format(WORK_DIR,'pvp'), 'rb')
           bot.send_photo(chat_id, photo = pic, caption = "")
        except Exception as e:
           bot.send_message(chat_id, help('rank', "Cannot find rank file.. sorry"))

    @bot.message_handler(commands=['rank_history'])
    def user_stat(message):
        msg = message.text
        chat_id = message.chat.id
        msg_arg = re.findall('/rank_history\s(.*)', msg)
        if not msg_arg:
            bot.send_message(chat_id, "Nickname is required")
            return 0
        msg_arg = msg_arg[0]
        chat_id = message.chat.id
        try:
            history = open('{}/{}_info.csv'.format(IMG_FOLDER,msg_arg), 'rb')
            bot.send_document(chat_id, history, caption = "*confidential")
        except Exception as e:
            bot.send_message(chat_id, "{}\n{}".format(msg_stat,help('dev', "Cannot find history file for {}".format(msg_arg))))


    @bot.message_handler(commands=['dev'])
    def dev_dev(message):
        msg = message.text
        chat_id = message.chat.id
        msg_arg = re.findall('/dev\s(.*)', msg)
        if not msg_arg:
            bot.send_message(chat_id, help('dev', "msg is empty"))
            return 0
        msg_arg = msg_arg[0]
        try:
           pic = open('{}/{}.png'.format(IMG_FOLDER,msg_arg), 'rb')
           bot.send_photo(chat_id, photo = pic, caption = "test caption")
        except Exception as e:
           bot.send_message(chat_id, help('dev', "Cannot find trend stats for {}".format(msg_arg)))

    bot.polling()

    #msg = getCSServerStats()
    #send(bot, msg)

if __name__=='__main__':
    main()
