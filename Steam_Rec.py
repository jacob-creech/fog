import urllib2
import json
import sys
import SteamValues as steam_val
from operator import itemgetter


def get_hours(steam_64_id):
    api_key = open('api_key.txt')
    key = api_key.read()
    api_key.close()
    getSummaries = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='
    getOwnedGames = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='

    received_summaries = False
    try_count = 0
    summaries = {}
    while not received_summaries:
        if try_count >= 10:
            print 'Error(getSummaries): Steam Server Not Responding...Quiting'
            break
        try:
            summaries = json.loads(urllib2.urlopen(getSummaries + key + '&steamids=' + steam_64_id + '&format=json', timeout=10).read())
        except urllib2.URLError, e:
            print "URLError(getSummaries): ", e.reason
            print "User ID:", steam_64_id
            print 'Resending Query...'
            try_count += 1
            continue
        except:
            e = sys.exc_info()[0]
            print 'getSummaries:', e
            print "User ID:", steam_64_id
            try_count += 1
            continue
        received_summaries = True

    if summaries != {}:
        received_games = False
        try_count = 0
        owned_games = {}
        while not received_games:
            if try_count >= 10:
                print 'Error(getOwnedGames): Steam Server Not Responding...Quiting'
                break
            try:
                owned_games = json.loads(urllib2.urlopen(getOwnedGames + key + '&steamid=' + steam_64_id + '&include_played_free_games=1&format=json', timeout=10).read())
            except urllib2.URLError, e:
                print "URLError(getOwnedGames): ", e.reason
                print "User ID:", steam_64_id
                try_count += 1
                continue
            except:
                e = sys.exc_info()[0]
                print 'getOwnedGames:', e
                print "User ID:", steam_64_id
                try_count += 1
                continue
            received_games = True
        return owned_games


def main():
    steam_64_id = raw_input('Enter a Steam 64 ID: ')
    games = get_hours(steam_64_id)['response']['games']

    steam_val.read()
    overall_user_rating = steam_val.calc_local_average(steam_64_id, games)
    overall_rating = steam_val.global_average()
    steam_val.map_users()
    steam_val.map_games()
    steam_val.build_matrix()
    #print steam_val.svd()

    user_deviation = overall_user_rating - overall_rating
    for game in steam_val.game_averages:
        game_deviation = steam_val.game_averages[game] - overall_rating
        if game in steam_val.user_averages[steam_64_id] and steam_val.user_averages[steam_64_id][game] == 0:
            steam_val.user_averages[steam_64_id][game] = overall_rating + game_deviation + user_deviation

    for game in sorted(steam_val.user_averages[steam_64_id].iteritems(), key=itemgetter(1), reverse=1)[:20]:
        print game[0], game[1]

main()
