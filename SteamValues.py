import json
import re
import numpy

user_game_dict = {}
# user_averages[userid][appid][local_average]
user_averages = {}
# game_averages[appid][global_average]
game_averages = {}
# user_mapping[userid][index]
user_mapping = {}
# game_mapping[appid][index]
game_mapping = {}
orig_matrix = []


def read():
    global user_game_dict
    dict_file = open("dictionary_first_crawl.txt", "r")
    for line in dict_file:
        line = re.sub('u', '', line)
        line = re.sub('\'', '\"', line)
        dataset = json.loads(line[18:])
        user_game_dict[line[:17]] = dataset


def map_users():
    global user_mapping
    for i, user in enumerate(sorted(user_averages.keys())):
        user_mapping[user] = i


def map_games():
    global game_mapping
    for i, game in enumerate(sorted(game_averages.keys())):
        game_mapping[game] = i


def build_matrix():
    global user_game_dict
    global user_averages
    global game_averages
    global orig_matrix
    user_avg_keys = sorted(user_averages.keys())
    game_avg_keys = sorted(game_averages.keys())

    # Default all values to Zero
    for i, user in enumerate(user_avg_keys):
        orig_matrix += [[]]
        for game in game_avg_keys:
            orig_matrix[i] += [0]
    # Maps previous ratings to matrix
    for i, user in enumerate(user_avg_keys):
        gameids = user_averages[user].keys()
        for game in gameids:
            if game in game_mapping:
                orig_matrix[i][game_mapping[game]] = user_averages[user][game]


def svd():
    global orig_matrix
    print orig_matrix
    print
    print
    u, s, v = numpy.linalg.svd(orig_matrix, full_matrices=False)
    composite = numpy.dot(numpy.dot(u, numpy.diag(s)), v)
    return composite[len(composite) - 1]


def calc_local_average(user, games):
    global user_averages
    user_total_hours = 0
    ratings_sum = 0
    user_averages[user] = {}
    for game in games:
        user_total_hours += game['playtime_forever']
    for game in games:
        if user_total_hours != 0:
            local_average = game['playtime_forever']/float(user_total_hours)
            ratings_sum += local_average
            user_averages[user][game['appid']] = local_average
    return ratings_sum / len(games)


def global_average():
    global user_game_dict
    global user_averages
    global game_averages
    # game_user[appid][num_of_users]
    game_user = {}

    for user in user_game_dict:
        user_averages[user] = {}
    for user in user_game_dict:
        user_total_hours = 0
        # for each game in the user's gamelist
        if 'games' in user_game_dict[user]['response']:
            # add up total hours of playtime that a user has first
            for game in user_game_dict[user]['response']['games']:
                # add up number of users per game
                game_user[game['appid']] = game_user.get(game['appid'], 0) + 1
                user_total_hours += game['playtime_forever']
            # Then get the local averages per game, per user
            for game in user_game_dict[user]['response']['games']:
                # Calculate local average
                if user_total_hours != 0:
                    local_average = game['playtime_forever']/float(user_total_hours)
                    user_averages[user][game['appid']] = local_average
                    # Add each local average to global total
                    game_averages[game['appid']] = game_averages.get(game['appid'], 0) + local_average
    for appid in game_averages:

        game_averages[appid] /= game_user[appid]

    game_sum = 0
    for game in game_averages:
        game_sum += game_averages[game]

    return game_sum / len(game_averages)


def main():
    read()
    global_average()
    map_users()
    map_games()
    svd()
#main()
