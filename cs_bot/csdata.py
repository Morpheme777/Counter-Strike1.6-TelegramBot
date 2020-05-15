## -*- coding: utf-8 -*-
import os
from ftplib import FTP
from struct import *

class CSStats(object):
    def __init__(self):
        self.to_file = os.path.dirname(os.path.realpath(__file__)) + "/data/csstats.dat"
        self.from_path = 'addons/amxmodx/data/'
        self.from_file = 'csstats.dat '
        #self.decodeFile(csdata_file)
        pass

    def downloadFile(self, to_file):
        ftp = FTP(host='83.222.115.202')
        ftp.login(user='gs7336', passwd='UoN8pudmG')

        ftp.cwd(self.from_path)

        out = "{}".format(to_file)
        with open(out, 'wb') as f:
            ftp.retrbinary('retr {}'.format(self.from_file), f.write)

    def decodeFile(self, csdata_file):

        f = open(csdata_file, "rb")

        rank_version = unpack('H', f.read(2))[0]
        #print('Rank version: {}'.format(rank_version))

        bytes = unpack('H', f.read(2))[0]
        #print('Bytes: {}'.format(bytes))

        #player = {}
        players = []
        num = 0

        while bytes:
            player = {}
            # player name
            name = unpack('{}cx'.format(str(bytes-1)), f.read(bytes))
            player['name'] = ''.join([x.decode() for x in name])
            # player auth
            bytes = unpack('H', f.read(2))[0]
            auth = unpack('{}cx'.format(str(bytes-1)), f.read(bytes))
            player['auth'] = ''.join([x.decode() for x in auth])
            # player stat
            buf = unpack('11I', f.read(11*4))
            player['tks'] = buf[0]
            player['damage'] = buf[1]
            player['deaths'] = buf[2]
            player['kills'] = buf[3]
            player['shots'] = buf[4]
            player['hits'] = buf[5]
            player['hs'] = buf[6]
            player['defuses'] = buf[7]
            player['defuse_attempts'] = buf[8]
            player['plants'] = buf[9]
            player['explosions'] = buf[10]
            # player hits
            buf = unpack('9I', f.read(9*4))
            player['hits'] = buf
            # next player
            bytes = unpack('H', f.read(2))[0]
            num = num + 1
            players.append(player)

        self.players_stat = players

#import json
#csstats = CSStats("csdata_20200501.dat")
#csstats.downloadFile("csdata_20200501.dat")
#players = csstats.players_stat
#f = open("player_stat", "w")

#for p in players:
#    print(p)
