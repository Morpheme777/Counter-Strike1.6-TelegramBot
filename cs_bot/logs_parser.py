import copy
import re
import os
from collections import Counter, defaultdict

import trueskill
import tqdm
import numpy as np
from scipy.special import softmax

LOG_FILE_PATTERN = 'L.*\.log'

MAP_CHANGED_MATCHER = re.compile('.*-------- Mapchange to (?P<map>.*) --------')
KILL_MATCHER = re.compile('.*\[(?P<team1>.{1,2})\]\|(?P<player1>.*) killed \[(?P<team2>.{1,2})\]\|(?P<player2>.*?) (?P<headshot>.*)using (?P<weapon>.*)\!')
ROUND_START_MATCHER = re.compile('.*round\ start \[(?P<team1>.{1,2})\] score: (?P<score1>\d+) \[(?P<team2>.{1,2})\] score: (?P<score2>\d+)\!')
ROUND_END_MATCHER = re.compile('.*round\ end \[(?P<team1>.{1,2})\] score: (?P<score1>\d+) \[(?P<team2>.{1,2})\] score: (?P<score2>\d+)\!')
PLAYER_TEAM_MATCHER = re.compile('.*\ (?P<player>.*) joined \[(?P<team>.{1,2})\]\!')

MIN_ROUNDS_FOR_PVP_STAT = 20
# INITIAL_RATING = 25.

MU = 110.
SIGMA = 50
BETA = SIGMA / 2
TAU = 0.05

env = trueskill.TrueSkill(mu=MU, sigma=SIGMA, beta=BETA, tau=TAU)
#env = trueskill.TrueSkill(mu=MU, sigma=SIGMA)

MAPS_TO_ACCOUNT = ['de_dust2', 'de_inferno', 'de_aztec']


class Round:
    def __init__(self):
        self._team_players = defaultdict(list)
        self._player_kills = Counter()
        self.winner_team = None
        self._prev_score = None

    def set_prev_score(self, team2score):
        self._prev_score = team2score

    def calc_winner(self, team2score):
        if not self._prev_score:
            return
        for team, score in self._prev_score.items():
            if score < team2score[team]:
                self.winner_team = team
                return

    def add(self, team, player):
        self._team_players[team].append(player)

    def get_winner_looser_teams(self):
        if not len(self._team_players) == 2:
            return [], [], [], []
        if not self.winner_team:
            return [], [], [], []

        loser_team = [t for t in self._team_players if t != self.winner_team][0]

        winner_players = self._team_players[self.winner_team]
        winner_players_kills = [self._player_kills[p] for p in winner_players]

        loser_players = self._team_players[loser_team]
        loser_players_kills = [self._player_kills[p] for p in loser_players]
        return winner_players, winner_players_kills, loser_players, loser_players_kills

    def register_kill(self, team1, player1, team2, player2, is_headshot, weapon1):
        """ player1  kills player2
        """
        self._player_kills[player1] += 1

class StatCollector:
    def __init__(self):
        self._p2r = defaultdict(env.create_rating)
        self._p2r_prev = None
        self._pvp_stat = Counter()
        self._p_stat = Counter()
        self._current_map = None
        self._players = set()

    def new_map(self, new_map):
        self._current_map = new_map

    def update_ratings(self, winner_players, winner_players_kills, loser_players, loser_players_kills):
        if len(winner_players) == 0 or len(loser_players) == 0:
            return

        team_win_ratings = [self._p2r[p] for p in winner_players]
        team_win_weights = softmax(np.array(winner_players_kills))

        team_lose_ratings = [self._p2r[p] for p in loser_players]
        team_lose_weights = softmax(-np.array(loser_players_kills))

        winner_ratings, loser_ratings = trueskill.rate([team_win_ratings, team_lose_ratings], weights=[team_win_weights, team_lose_weights])

        for player, new_rating in zip(winner_players, winner_ratings):
            self._p2r[player] = new_rating
        for player, new_rating in zip(loser_players, loser_ratings):
            self._p2r[player] = new_rating

    def register_kill(self, team1, player1, team2, player2, is_headshot, weapon1):
        """ player1  kills player2
        """
        #self._p2r[player1], self._p2r[player2] = trueskill.rate_1vs1(
        #    self._p2r[player1], self._p2r[player2]
        #)
        
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
        self._round = None

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
            if self._round:
                self._round.register_kill(*kill)
            return

        new_round = LineMatcher.parse_new_round(line)
        if new_round:
            team2score = new_round
            if self._round:
                self._round.set_prev_score(team2score)
            return

        end_round = LineMatcher.parse_end_round(line)
        if end_round and self._round:
            team2score = end_round
            self._round.calc_winner(team2score)
            team_stats = self._round.get_winner_looser_teams()
            self._stat_collector.update_ratings(*team_stats)
            self._round = Round()
            return

        player_join_team = LineMatcher.parse_player_team(line)
        if player_join_team:
            if not self._round:
                self._round = Round()
            self._round.add(*player_join_team)
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

    def parse_new_round(line):
        result = ROUND_START_MATCHER.search(line)
        if not result:
            return None
        return {
            result.group('team1'): int(result.group('score1')),
            result.group('team2'): int(result.group('score2')),
        }

    def parse_end_round(line):
        result = ROUND_END_MATCHER.search(line)
        if not result:
            return None
        return {
            result.group('team1'): int(result.group('score1')),
            result.group('team2'): int(result.group('score2')),
        }

    def parse_player_team(line):
        result = PLAYER_TEAM_MATCHER.search(line)
        if not result:
            return None
        return (
            result.group('team'),
            result.group('player')
        )