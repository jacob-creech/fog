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
        if try_count >= 3:
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
            if try_count >= 3:
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


def main(steam_64_id):
    print '*****FoG Recommender Running Query*****'
    alpha = .2
    beta = 1 - alpha
    # user_games[appid][hours]
    user_games = {}
    # svd_scores[appid][svd_score]
    svd_scores = {}
    # global_avg_scores[appid][global_avg_score]
    global_avg_scores = {}
    # game_list_dict[appid][game_name]
    game_list_dict = {}
    # final_scores[appid][combined_score]
    final_scores = {}

    steam_val.read_from_files()

    print 'Calculating Results...'

    #store queried user info
    for game_dict in get_hours(steam_64_id)['response']['games']:
        user_games[game_dict['appid']] = game_dict['playtime_forever']

    #calculate global_average values
    overall_user_rating = steam_val.calc_local_average(steam_64_id, user_games)
    global_rating = steam_val.global_rating

    #calculate svd matrix
    steam_val.orig_matrix_add_user(steam_64_id)
    svd_user_scores = steam_val.svd(steam_64_id)

    #finalize svd and global_avg scores
    user_deviation = overall_user_rating - global_rating
    for game in steam_val.game_averages:
        # map and store svd scores to the appropriate appid
        svd_scores[game] = svd_user_scores[steam_val.game_mapping[game]]
        # populate unplayed games for the user and record predicted rating
        game_deviation = steam_val.game_averages[game] - global_rating
        global_avg_scores[game] = global_rating + game_deviation + user_deviation

    # map each appid with its game_name
    game_list_file = open('SteamGameList', 'r')
    game_list_str = ''
    for line in game_list_file:
        game_list_str += line
    game_list_obj = json.loads(game_list_str.decode('utf-8').encode('ascii', 'ignore'))
    for game in game_list_obj['applist']['apps']['app']:
        game_list_dict[game['appid']] = game['name']
    game_list_file.close()

    # combine svd and global_average; record the recommendations
    for game in steam_val.game_averages:
        if game not in user_games or user_games[game] == 0:
            final_scores[game] = svd_scores[game]*alpha + global_avg_scores[game]*beta
    output = ''
    for game in sorted(final_scores.iteritems(), key=itemgetter(1), reverse=1)[:20]:
        # game[0] -> appid
        # game[1] -> score
        game_name = '---Title Not Found---'
        if game[0] in game_list_dict:
            game_name = game_list_dict[game[0]]
        output += '<tr>\n\t<td>', game_name, '</td>\n\t<td> GENRE </td>\n\t<td> PRICE </td>\n</tr>'
    return output

# print main('76561198057195965')