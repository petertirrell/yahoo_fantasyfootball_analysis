# -*- coding: utf-8 -*-

#import csv, json, requests, time
import csv, json, numpy, xmltodict, time

from datetime import datetime
from operator import itemgetter

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


def write_csv_file(filename, year, list_of_players):
    print str(datetime.now()) + ' Writing file {0}'.format(OUTPUT_CSV_PATH + filename + '.csv')
    #print list_of_players
    with open(OUTPUT_CSV_PATH + year + '-' + filename + '.csv', 'w+') as f:
        writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
        
        writer.writerow([
            'YEAR', 
            'FILENAME', 
            'PLAYER_KEY', 
            'PLAYER_NAME', 
            'SEASON_TOTAL', 
            'CALCULATED_SEASON_TOTAL', 
            'MEAN', 
            'MEDIAN', 
            'STD_DEVIATION', 
            'CV',
            'MEAN_RANK', 
            'CV_RANK', 
            'PERFORMANCE_SCORE',
            'PERFORMANCE_RANK'
        ] + ['WK{0}'.format(i) for i in range(1, len(list_of_players[0]['scores'])+1)])
            #'WK1', 'WK2', 'WK3', 'WK4', 'WK5', 'WK6', 'WK7', 'WK8', 'WK9', 'WK10', 'WK11', 'WK12', 'WK13', 'WK14', 'WK15', 'WK16'])
        # writer.writerows([year, filename, item['player_key'], item['player_name'], item['season_total'],
        #     item['calculated_season_total'], item['average'], item['median'], item['std_deviation'], ','.join(item['scores'])] for item in list_of_players)
        for player in list_of_players:
            writer.writerow([
                year, 
                filename, 
                player['player_key'], 
                player['player_name'], 
                player['season_total'],
                player['calculated_season_total'], 
                player['mean'], 
                player['median'], 
                player['std_deviation'], 
                player['coefficient_of_variation'],
                player['mean_rank'], 
                player['cv_rank'], 
                player['performance_score'],
                player['performance_rank'],
            ] + player['scores'])
                # player['scores'][0] if len(player['scores'])>0 else '',
                # player['scores'][1] if len(player['scores'])>1 else '',
                # player['scores'][2] if len(player['scores'])>2 else '',
                # player['scores'][3] if len(player['scores'])>3 else '',
                # player['scores'][4] if len(player['scores'])>4 else '',
                # player['scores'][5] if len(player['scores'])>5 else '',
                # player['scores'][6] if len(player['scores'])>6 else '',
                # player['scores'][7] if len(player['scores'])>7 else '',
                # player['scores'][8] if len(player['scores'])>8 else '',
                # player['scores'][9] if len(player['scores'])>9 else '',
                # player['scores'][10] if len(player['scores'])>10 else '',
                # player['scores'][11] if len(player['scores'])>11 else '',
                # player['scores'][12] if len(player['scores'])>12 else '',
                # player['scores'][13] if len(player['scores'])>13 else '',
                # player['scores'][14] if len(player['scores'])>14 else '',
                # player['scores'][15] if len(player['scores'])>15 else '',
                # ])


def get_players(league_key, position = None):
    uri = 'http://fantasysports.yahooapis.com/fantasy/v2/league/' + league_key + '/players;sort=PTS;sort_type=season'
    # uri = 'http://fantasysports.yahooapis.com/fantasy/v2/league/' + league_key + '/players;sort=PTS;sort_type=season;count=5'
    # ;start=26 would get the next set
    # so we need to loop through 4 times to get the top 100 of anything

    startPos = ['0', '25', '50', '75']
    #startPos = ['75']

    if position:
        uri += ';position=' + position

    
    rtn = []

    for pos in startPos:

        r = api.request(uri + ';start=' + pos)
        print str(datetime.now()) + ' ' + uri + ';start=' + pos
        
        if r.status_code == 200:
            
            result = xmltodict.parse(r.text)
            # print r.text

            players = []
            if result['fantasy_content']['league']['players']:
                players = result['fantasy_content']['league']['players']['player']
            
            if not isinstance(players, list): players = [players]

            end_week =  int(result['fantasy_content']['league']['current_week'])
            
            limit_debug = True

            x = 1
            for player in players:
                
                if (x <= 1 and limit_debug == True) or limit_debug == False:
                    print str(datetime.now()) + ' Looking up scores for ' + player['player_key'] + ' ' + player['name']['full']
                    pdict = {
                            'player_key': player['player_key'],
                            'player_name': player['name']['full'],    
                            'season_total': get_player_overall_stats(league_key, player['player_key'])
                        }
                        # print player['player_key']
                        # print player['name']['full']
                        # # for each player, assemble a score for each week
                    scores = []
                    for i in range(1, end_week+1):
                        #print 'Looking up week ' + str(i) + ' score for ' + player['player_key'] + ' ' + player['name']['full']
                        player_stats = get_player_stats(league_key, player['player_key'], i)
                        if player_stats:
                            scores.append(player_stats)
                        else:
                            scores.append(None)
                    
                    scores_list = [float(item) for item in scores]
                    a = numpy.array(scores_list)

                    pdict['scores'] = scores
                    pdict['calculated_season_total'] = sum(float(item) for item in scores)
                    #pdict['averageold'] = sum(float(item) for item in scores) / len(scores)
                    pdict['mean'] = numpy.around(numpy.mean(a), decimals=4)
                    pdict['median'] = numpy.median(a)
                    pdict['std_deviation'] = numpy.std(a)
                    pdict['coefficient_of_variation'] = pdict['std_deviation'] / pdict['mean'] # sd / mean # lower is better, less risk/volatility
                    #pdict['performance_score'] = pdict['coefficient_of_variation'] * pdict['mean']

                    rtn.append(pdict)
                x += 1        

        else:
            print 'Error: ' + str(r.status_code)
            print r.text
    
    return rtn            

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
    
    retries = 5

    while(retries >=0):        
        r = api.request(uri)

        if r.status_code == 200:
            result = xmltodict.parse(r.text)
            #print r.text
            weekly_score = result['fantasy_content']['league']['players']['player']['player_points']['total']
            return weekly_score
        else:
            print 'Error: ' + str(r.status_code)
            print r.text
            print 'Retrying...'
            retries = retries - 1
            time.sleep(2)

    return -99


'''
For a given year (league ID), go through each position and assemble top players' weekly average scores

'''

positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']
positions = ['WR']

for position in positions:
    players = get_players(SEED_LEAGUE_KEY, position)

    # sort list by mean, then add rank value (highest is better)
    players = sorted(players, key=itemgetter('mean'), reverse=True)

    i = 1
    for player in players:
        player['mean_rank'] = i
        i += 1

    # sort list by cv, then add rank value (lowest value is better)
    players = sorted(players, key=itemgetter('coefficient_of_variation'))

    i = 1
    for player in players:
        player['cv_rank'] = i if player['coefficient_of_variation'] > 0 else 100
        i +=1

    # calculate average rank, place in performance value
    for player in players:
        player['performance_score'] = ((4 *player['mean_rank']) + player['cv_rank']) / 2

    # sort by overall performance
    players = sorted(players, key=itemgetter('performance_score'))

    i = 1
    for player in players:
        player['performance_rank'] = i
        i +=1
    
    for player in players:
        print player

    # write csv
    # print '{1} Writing CSV file to {0}'.format(OUTPUT_CSV_NAME, str(datetime.now()))
    write_csv_file(position, '2015', players)

# aaron rodgers 331.p.7200
#foo = get_player_overall_stats2('331.l.1098504', '331.p.7200')


# player stats http://fantasysports.yahooapis.com/fantasy/v2/player/223.p.5479/stats
# http://fantasysports.yahooapis.com/fantasy/v2/league/223.l.431/players;player_keys=223.p.5479/stats
# /fantasy/v2/player/{player_key}/stats;type=week;week={week}

