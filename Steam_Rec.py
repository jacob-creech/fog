import urllib2
import json
import sys
import SteamValues as sv
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
            print 'Resending Query...'
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
                print 'Resending Query...'
                try_count += 1
                continue
            except:
                e = sys.exc_info()[0]
                print 'getOwnedGames:', e
                print "User ID:", steam_64_id
                print 'Resending Query...'
                try_count += 1
                continue
            received_games = True
        return owned_games


# calculate global average values for the queried user
def calc_local_average(games):
    #user_total_hours = 0
    ratings_sum = 0
    local_averages = {}
    #for game in games:
        #user_total_hours += games[game]
    for game in games:
        if games[game] > 0 and game in sv.game_averages:  # if user_total_hours != 0
            local_average = games[game] / (sv.game_hours[game] / float(sv.game_user[game]))  # float(user_total_hours)
            ratings_sum += local_average
            local_averages[game] = local_average
    return (ratings_sum / len(games)), local_averages


def orig_matrix_add_user(user, local_averages):
    if user not in sv.user_mapping:
        sv.orig_matrix += [[]]
        index = len(sv.orig_matrix) - 1
        for game in sorted(sv.game_averages.keys()):
            sv.orig_matrix[index] += [0]
        gameids = local_averages.keys()
        for game in gameids:
            if game in sv.game_mapping:
                sv.orig_matrix[index][sv.game_mapping[game]] = local_averages[game]
        sv.user_mapping[user] = index
    else:
        gameids = local_averages.keys()
        for game in gameids:
            if game in sv.game_mapping:
                sv.orig_matrix[sv.user_mapping[user]][sv.game_mapping[game]] = local_averages[game]


def main(steam_64_id):
    print '*****FoG Recommender Running Query*****'
    alpha = 0
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

    #sv.read_from_files()

    print 'Calculating Results...'

    #store queried user info
    if 'games' in get_hours(steam_64_id)['response']:
        for game_dict in get_hours(steam_64_id)['response']['games']:
            user_games[game_dict['appid']] = game_dict['playtime_forever']

    #calculate global_average values
    overall_user_rating, local_averages = calc_local_average(user_games)
    global_rating = sv.global_rating

    #calculate svd matrix
    orig_matrix_add_user(steam_64_id, local_averages)
    svd_user_scores = sv.svd()

    #finalize svd and global_avg scores
    user_deviation = overall_user_rating - global_rating
    for game in sv.game_averages:
        # map and store svd scores to the appropriate appid
        svd_scores[game] = svd_user_scores[sv.game_mapping[game]]
        # populate unplayed games for the user and record predicted rating
        game_deviation = sv.game_averages[game] - global_rating
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

    # Normalize svd and ga scores
    normalize_svd_nums = {}
    normalize_ga_nums = {}
    for game in sv.game_averages:
        if game not in user_games or user_games[game] == 0:
            normalize_svd_nums[game] = svd_scores[game]
            normalize_ga_nums[game] = global_avg_scores[game]
    # Get min and max scores
    min_score = normalize_ga_nums[min(normalize_ga_nums, key=normalize_ga_nums.get)]
    max_score = normalize_ga_nums[max(normalize_ga_nums, key=normalize_ga_nums.get)]
    min_score_svd = normalize_svd_nums[min(normalize_svd_nums, key=normalize_svd_nums.get)]
    max_score_svd = normalize_svd_nums[max(normalize_svd_nums, key=normalize_svd_nums.get)]
    for game in normalize_ga_nums:
        normalize_ga_nums[game] = (normalize_ga_nums[game] - min_score) / float(max_score - min_score)
        normalize_svd_nums[game] = (normalize_svd_nums[game] - min_score_svd) / float(max_score_svd - min_score_svd)

    # combine svd and global_average scores
    for game in sv.game_averages:
        if game not in user_games or user_games[game] == 0:
            final_scores[game] = normalize_svd_nums[game]*alpha + normalize_ga_nums[game]*beta
            print game, '\t', normalize_svd_nums[game], '\t', normalize_ga_nums[game]
    #for result in sorted(normalize_svd_nums.iteritems(), key=itemgetter(1), reverse=1)[:20]:
     #   print result

    #Record the top 20 results
    output = ''
    image_url_beg = 'cdn.akamai.steamstatic.com/steam/apps/'
    image_url_end = '/header.jpeg'
    for game in sorted(final_scores.iteritems(), key=itemgetter(1), reverse=1)[:20]:
        # game[0] -> appid
        # game[1] -> score
        game_name = '---Title Not Found---'
        if game[0] in game_list_dict:
            game_name = game_list_dict[game[0]]
        output += '<tr><td><abbr title=\"' + image_url_beg + str(game[0]) + image_url_end + '\">' + str(game_name) + \
                  '</abbr></td> <td>' + str(game[1]) + '</td></tr>\n'
        #output += str(game_name) + ' ' + str(game[1]) + '\n'
    print 'Calculations Completed...Sending Results to Client'
    return output

#print main('76561198053212280')