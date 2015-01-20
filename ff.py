# -*- coding: utf-8 -*-

#import csv, json, requests, time
import json
from datetime import datetime

import xmltodict

from yahooapi import YahooAPI

keyfile = 'secrets.txt'
tokenfile = 'tokenfile.txt'

SEED_LEAGUE_KEY = '331.l.1098504' # current Kimball leauge, build list of leagues based on this

api = YahooAPI(keyfile, tokenfile)

url = 'http://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nfl/leagues'
users_uri = 'http://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games'

teams_uri = 'http://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/teams'

league_key = '331.l.1098504' # current Kimball leauge
leagues_uri = 'http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=' + league_key

nfl_games = 'http://fantasysports.yahooapis.com/fantasy/v2/game/nfl'


def get_league_info(league_key):
    uri = 'http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=' + league_key

    r = api.request(uri)

    if r.status_code == 200:
        result = xmltodict.parse(r.text)
        # print r.text
        leagues = result['fantasy_content']['leagues']['league']
        if not isinstance(leagues, list): leagues = [leagues]

        rtn = []
        for league in leagues:
            '''
            Need league_key, renew (previous league ID), renewed (next league ID), start_date (use to get year of league)
            '''
            # print league['league_key']
            # print league['renew']
            # print league['renewed']
            # print league['start_date']
            
            previous_league = None
            
            if league['renew']:
                previous_league = league['renew'].split('_')[0] + '.l.' + league['renew'].split('_')[1]
            
            rtn.append({
                'league_key' : league['league_key'],
                'renew' : league['renew'],
                'renewed' : league['renewed'],
                'previous_league' : previous_league,
                'start_date' : league['start_date'],
                'year': datetime.strptime(league['start_date'], '%Y-%m-%d').year
                })

            # now backtrack for previous leagues
            if league['renew']:
                rtn += get_league_info(previous_league)

        return rtn

        # for league in result['fantasy_content']['leagues']['league']:
        #     print league
        #     '''
        #     Need league_key, renew (previous league ID), renewed (next league ID), start_date (use to get year of league)
        #     '''
    else:
        print 'Error: ' + str(r.status_code)
        print r.text
        return []


def get_players(league_key, position = None):
    uri = 'http://fantasysports.yahooapis.com/fantasy/v2/league/' + league_key + '/players;sort=PTS;sort_type=season;count=100'
    uri = 'http://fantasysports.yahooapis.com/fantasy/v2/league/' + league_key + '/players;sort=PTS;sort_type=season;count=25'

    if position:
        uri += ';position=' + position

    r = api.request(uri)

    if r.status_code == 200:
        rtn = []
        result = xmltodict.parse(r.text)
        # print r.text

        players = result['fantasy_content']['league']['players']['player']
        if not isinstance(players, list): players = [players]

        end_week =  int(result['fantasy_content']['league']['end_week'])
        
        x = 1
        for player in players:
            print 'Looking up scores for ' + player['player_key'] + ' ' + player['name']['full']
            pdict = {
                    'player_key': player['player_key'],
                    'player_name': player['name']['full'],    
                    'season_total': get_player_overall_stats(league_key, player['player_key'])
                }
            if x <= 5:
                # print player['player_key']
                # print player['name']['full']
                # # for each player, assemble a score for each week
                scores = []
                for i in range(1, end_week+1):
                    #print 'Looking up week ' + str(i) + ' score for ' + player['player_key'] + ' ' + player['name']['full']
                    scores.append(get_player_stats(league_key, player['player_key'], i))
                
                pdict['scores'] = scores
                pdict['total'] = sum(float(item) for item in scores)
                pdict['average'] = sum(float(item) for item in scores) / float(len(scores))

                rtn.append(pdict)
            x += 1

        print rtn

    else:
        print 'Error: ' + str(r.status_code)
        print r.text
        return []

def get_player_overall_stats(league_key, player_key):
    uri = 'http://fantasysports.yahooapis.com/fantasy/v2/league/' + league_key + '/players;player_keys=' + player_key + '/stats'

    r = api.request(uri)

    if r.status_code == 200:
        result = xmltodict.parse(r.text)
        #print r.text
        weekly_score = result['fantasy_content']['league']['players']['player']['player_points']['total']
        return weekly_score
    else:
        print 'Error: ' + str(r.status_code)
        print r.text
        return None


def get_player_overall_stats2(league_key, player_key):
    uri = 'http://fantasysports.yahooapis.com/fantasy/v2/league/' + league_key + '/players;player_keys=' + player_key + '/stats'

    r = api.request(uri)

    if r.status_code == 200:
        result = xmltodict.parse(r.text)
        print r.text
        weekly_score = result['fantasy_content']['league']['players']['player']['player_points']['total']
        return weekly_score
    else:
        print 'Error: ' + str(r.status_code)
        print r.text
        return None

def get_player_stats(league_key, player_key, week):
    uri = 'http://fantasysports.yahooapis.com/fantasy/v2/league/' + league_key + '/players;player_keys=' + player_key + '/stats;type=week;week=' + str(week)
    
    r = api.request(uri)

    if r.status_code == 200:
        result = xmltodict.parse(r.text)
        #print r.text
        weekly_score = result['fantasy_content']['league']['players']['player']['player_points']['total']
        return weekly_score
    else:
        print 'Error: ' + str(r.status_code)
        print r.text
        return None


# assemble a list of leagues based on a seed league
# all_leagues = get_league_info(SEED_LEAGUE_KEY) # at this point we have all our league IDs!

# for item in all_leagues:
#     print item

'''
For a given year (league ID), go through each position and assemble top players' weekly average scores

'''
test = get_players(SEED_LEAGUE_KEY, 'QB')

# aaron rodgers 331.p.7200
#foo = get_player_overall_stats2('331.l.1098504', '331.p.7200')


# player stats http://fantasysports.yahooapis.com/fantasy/v2/player/223.p.5479/stats
# http://fantasysports.yahooapis.com/fantasy/v2/league/223.l.431/players;player_keys=223.p.5479/stats
# /fantasy/v2/player/{player_key}/stats;type=week;week={week}

