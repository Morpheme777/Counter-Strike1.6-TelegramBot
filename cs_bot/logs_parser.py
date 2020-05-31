import copy
import re
import os
from collections import Counter, defaultdict

import trueskill
import tqdm
import numpy as np

LOG_FILE_PATTERN = 'L.*\.log'

MAP_CHANGED_MATCHER = re.compile('.*-------- Mapchange to (?P<map>.*) --------')
KILL_MATCHER = re.compile('.*\[(?P<team1>.{1,2})\]\|(?P<player1>.*) killed \[(?P<team2>.{1,2})\]\|(?P<player2>.*?) (?P<headshot>.*)using (?P<weapon>.*)\!')
MIN_ROUNDS_FOR_PVP_STAT = 20
INITIAL_RATING = 100.

MAPS_TO_ACCOUNT = ['de_dust2', 'de_inferno', 'de_aztec']


class StatCollector:
    def __init__(self):
        self._p2r = defaultdict(lambda: trueskill.Rating(INITIAL_RATING))
        self._p2r_prev = None
        self._pvp_stat = Counter()
        self._p_stat = Counter()
        self._current_map = None
        self._players = set()

    def new_map(self, new_map):
        self._current_map = new_map

    def register_kill(self, team1, player1, team2, player2, is_headshot, weapon1):
        """ player1  kills player2
        """
        self._p2r[player1], self._p2r[player2] = trueskill.rate_1vs1(
            self._p2r[player1], self._p2r[player2]
        )
        
        self._pvp_stat[player1, player2] += 1

        self._p_stat[(self._current_map, player1, team1, 'win')] += 1
        self._p_stat[(self._current_map, player2, team2, 'lose')] += 1

        self._players.update([player1, player2])

    def get_ratings(self):
        return {p: (r.mu,
                    r.mu - self._p2r_prev.get(p).mu if p in self._p2r_prev else None
                    ) for p, r in self._p2r.items()}

    def new_file(self):
        self._p2r_prev = copy.deepcopy(self._p2r)

    def get_pvp_stats(self):
        players, _ = zip(*sorted(self.get_ratings().items(), key=lambda x: x[1], reverse=True))

        data = np.empty((len(players), len(players)))
        for i, player1 in enumerate(players):
            for j, player2 in enumerate(players):
                kills = self._pvp_stat[player1, player2]
                loss = self._pvp_stat[player2, player1]
                rate = None
                if kills + loss >= MIN_ROUNDS_FOR_PVP_STAT:
                    rate = kills / (kills + loss)
                data[i, j] = rate
        return players, data

    def get_player_stats(self):
        res = defaultdict(list)
        for player in self._players:
            for _map in MAPS_TO_ACCOUNT:
                for team in ['CT', 'T']:
                    wins = self._p_stat[(_map, player, team, 'win')]
                    loss = self._p_stat[(_map, player, team, 'lose')]
                    res[player].append((_map, team, wins/(wins+loss)))
        return res


class LogsParser:
    def __init__(self, path):
        self._path = path
        self._files = sorted(os.listdir(path))
        self._files = [f for f in self._files if re.match(LOG_FILE_PATTERN, f)]
        self._stat_collector = StatCollector()

    def parse(self):
        for _file in tqdm.tqdm(self._files):
            self._stat_collector.new_file()
            with open(os.path.join(self._path, _file), 'r') as f:
                for line in f.readlines():
                    self._parse_line(line)
        return self._stat_collector

    def _parse_line(self, line):
        _map = LineMatcher.parse_mapchange(line)
        if _map:
            self._stat_collector.new_map(_map)
            return

        kill = LineMatcher.parse_kill(line)
        if kill:
            self._stat_collector.register_kill(*kill)
            return



class LineMatcher:
    def parse_mapchange(line):
        result = MAP_CHANGED_MATCHER.search(line)
        if not result:
            return None
        return result.group('map')

    def parse_kill(line):
        result = KILL_MATCHER.search(line)
        if not result:
            return None
        return (
            result.group('team1'),
            result.group('player1'),
            result.group('team2'),
            result.group('player2'),
            result.group('headshot') != '',
            result.group('weapon'),
        )