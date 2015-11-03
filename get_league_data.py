# -*- coding: utf-8 -*-

#import csv, json, requests, time
import csv, json, numpy, xmltodict, time

from datetime import datetime

from yahooapi import YahooAPI

keyfile = 'secrets.txt'
tokenfile = 'tokenfile.txt'

SEED_LEAGUE_KEY = '331.l.1098504' # current Kimball leauge, build list of leagues based on this # 2014
SEED_LEAGUE_KEY = '348.l.1044567' # 2015
OUTPUT_CSV_PATH = 'C:\\Users\\Peter\\Dropbox\\ff\\data\\'
#OUTPUT_CSV_PATH = 'data/'

api = YahooAPI(keyfile, tokenfile)

url = 'http://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nfl/leagues'
users_uri = 'http://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games'

teams_uri = 'http://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/teams'

nfl_games = 'http://fantasysports.yahooapis.com/fantasy/v2/game/nfl'

numpy.set_printoptions(precision=4)


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
            next_league = None
            
            if league['renew']:
                previous_league = league['renew'].split('_')[0] + '.l.' + league['renew'].split('_')[1]

            if league['renewed']:
                next_league = league['renewed'].split('_')[0] + '.l.' + league['renewed'].split('_')[1]


            
            rtn.append({
                'league_key' : league['league_key'],
                'renew' : league['renew'],
                'renewed' : league['renewed'],
                'previous_league' : previous_league,
                'next_league' : next_league,
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


# assemble a list of leagues based on a seed league
all_leagues = get_league_info(SEED_LEAGUE_KEY) # at this point we have all our league IDs!

for item in all_leagues:
    print item
