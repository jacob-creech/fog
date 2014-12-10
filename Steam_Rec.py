import urllib2
import json
import sys
import SteamValues as sv
from operator import itemgetter


'''
    This is the primary recommender file. The helper function first retrieve the queried user's
    games and playtime information which are then sent to the other two functions which
    calculate baseline and cluster values. Our recommender highly favors the cluster results,
    because they are much fewer and seem to optimize our results.

    Note: some returned score values may appear to be equal (i.e. 0.1) which are the result
    of python round results such as 0.0999999999, 0.0999999998, 0.0999999997, etc. but these
    rankings still hold the order of this lost precision.
'''


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


# calculate top cluster values
def cluster_value(user_games):
    cluster_scores = {}
    for index, game in enumerate(sorted(user_games.iteritems(), key=itemgetter(1), reverse=1)):
        if str(game[0]) in sv.cluster_data:
            for related_game in sv.cluster_data[str(game[0])]:
                #print related_game
                if related_game not in cluster_scores:
                    cluster_scores[related_game] = len(user_games) - index
                else:
                    cluster_scores[related_game] += len(user_games) - index
    return cluster_scores


# calculate global average values for the queried user
def calc_local_average(games):
    ratings_sum = 0
    local_averages = {}
    for game in games:
        if games[game] > 0 and game in sv.game_averages:
            local_average = games[game] / (sv.game_hours[game] / float(sv.game_user[game]))
            ratings_sum += local_average
            local_averages[game] = local_average
    return (ratings_sum / len(games)), local_averages


# Run the Recommendation System
# Note: Only run this code after running run_once.py to generate the data files
def main(steam_64_id):
    print '*****FoG Recommender Running Query*****'
    alpha = .9
    beta = 1 - alpha
    # user_games[appid][hours]
    user_games = {}
    # global_avg_scores[appid][global_avg_score]
    global_avg_scores = {}
    # game_list_dict[appid][game_name]
    game_list_dict = {}
    # final_scores[appid][combined_score]
    final_scores = {}
    # user_scores[appid][combined_score]
    user_scores = {}

    print 'Calculating Results...'

    #store queried user info
    if 'games' in get_hours(steam_64_id)['response']:
        for game_dict in get_hours(steam_64_id)['response']['games']:
            user_games[game_dict['appid']] = game_dict['playtime_forever']

    #calculate global_average values
    overall_user_rating, local_averages = calc_local_average(user_games)
    global_rating = sv.global_rating

    #finalize global_avg scores
    user_deviation = overall_user_rating - global_rating
    for game in sv.game_averages:
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

    # Normalize cluster and global_average scores
    normalize_cluster_nums = cluster_value(user_games)
    min_avg = global_avg_scores[min(global_avg_scores, key=global_avg_scores.get)]
    max_avg = global_avg_scores[max(global_avg_scores, key=global_avg_scores.get)]
    min_cluster = normalize_cluster_nums[min(normalize_cluster_nums, key=normalize_cluster_nums.get)]
    max_cluster = normalize_cluster_nums[max(normalize_cluster_nums, key=normalize_cluster_nums.get)]
    for game in global_avg_scores:
        global_avg_scores[game] = (global_avg_scores[game] - min_avg) / float(max_avg - min_avg)
    for game in normalize_cluster_nums:
        normalize_cluster_nums[game] = (normalize_cluster_nums[game] - min_cluster) / float(max_cluster - min_cluster)
        normalize_cluster_nums[game] += .2

    # combine cluster and global_average scores
    for game in sv.game_averages:
        score = normalize_cluster_nums.get(str(game), 0)*alpha + global_avg_scores[game]*beta
        if game not in user_games or user_games[game] == 0:
            # Remove notorious game "Bad Rats"
            if game == 34900:
                final_scores[game] = 0
            else:
                final_scores[game] = score
        elif game in user_games:
            user_scores[game] = score

    # Record the top 20 user owned game score results
    # '1' is a flag for the data's destination on the web page
    owned_ratings = '1'
    for game in sorted(user_scores.iteritems(), key=itemgetter(1), reverse=1):
        game_name = '---Title Not Found---'
        if game[0] in game_list_dict:
            game_name = game_list_dict[game[0]]
        owned_ratings += game_name + '<br>'

    # Record the top 20 recommended results
    # '0' is a flag for the data's destination on the web page
    top_results = '0'
    image_url_beg = 'http://store.steampowered.com/app/'
    for game in sorted(final_scores.iteritems(), key=itemgetter(1), reverse=1)[:20]:
        # game[0] -> appid
        # game[1] -> score
        game_name = '---Title Not Found---'
        if game[0] in game_list_dict:
            game_name = game_list_dict[game[0]]
        top_results += '<tr><td><a href=\"' + image_url_beg + str(game[0]) + '\">' + str(game_name) + \
                       '</a></td> <td>' + str(game[1]) + '</td></tr>\n'

    print 'Calculations Completed...Sending Results to Client'
    return top_results, owned_ratings
