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
global_rating = 0.0
# game_hours[appid][total_hours_played]
game_hours = {}
# game_user[appid][num_of_users]
game_user = {}


# Store values that are reused
def write_to_files():
    print "Writing to game averages..."
    file_one = open("game_averages", "w")
    file_one.write(str(game_averages))
    file_one.close()

    print "Writing to original matrix..."
    file_two = open("original_matrix", "w")
    for row in orig_matrix:
        file_two.write(str(row) + '\n')
    file_two.close()

    print "Writing to user mapping..."
    file_three = open("user_mapping", "w")
    file_three.write(str(user_mapping))
    file_three.close()

    print "Writing to game mapping..."
    file_four = open("game_mapping", "w")
    file_four.write(str(game_mapping))
    file_four.close()

    print "Writing to user averages..."
    file_five = open("user_averages", "w")
    file_five.write(str(user_averages))
    file_five.close()
    
    print "Writing to global rating..."
    file_five = open("global_rating", "w")
    file_five.write(str(global_rating))
    file_five.close()

    print "Writing to game hours..."
    file_six = open("game_hours", "w")
    file_six.write(str(game_hours))
    file_six.close()

    print "Writing to game user..."
    file_seven = open("game_user", "w")
    file_seven.write(str(game_user))
    file_seven.close()


# read in stored values from previous calculations
def read_from_files():
    global orig_matrix
    global game_averages
    global game_mapping
    global user_averages
    global user_mapping
    global global_rating
    global game_hours
    global game_user

    counter = 0
    
    orig_matrix = []
    for line in open("original_matrix", "r"):
        print "Reading original matrix @", counter
        line = line[1:-2]
        line = line.split(',')
        line = [float(elem) for elem in line]
        orig_matrix += [line]
        counter += 1

    print "Reading game averages"
    file_one = open("game_averages", "r")
    game_averages = eval(file_one.read())

    print "Reading user mapping"
    file_three = open("user_mapping", "r")
    user_mapping = eval(file_three.read())

    print "Reading game_mapping"
    file_four = open("game_mapping", "r")
    game_mapping = eval(file_four.read())

    print "Reading user_averages"
    file_five = open("user_averages", "r")
    user_averages = eval(file_five.read())

    print "Reading global_rating"
    file_six = open("global_rating", "r")
    global_rating = eval(file_six.read())

    print "Reading game_hours"
    file_seven = open("game_hours", "r")
    game_hours = eval(file_seven.read())

    print "Reading game_user"
    file_eight = open("game_user", "r")
    game_user = eval(file_eight.read())


# Read in the data set of Steam Users
def read():
    global user_game_dict
    dict_file = open("dataset.txt", "r")
    for line in dict_file:
        line = re.sub('u', '', line)
        line = re.sub('\'', '\"', line)
        dataset = json.loads(line[18:])
        user_game_dict[line[:17]] = dataset


# Assign each user an index value
def map_users():
    global user_mapping
    for i, user in enumerate(sorted(user_averages.keys())):
        user_mapping[user] = i


# Assign each game an index value
def map_games():
    global game_mapping
    for i, game in enumerate(sorted(game_averages.keys())):
        game_mapping[game] = i


# create svd input matrix
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


# create svd score matrix
def svd(user_id):
    global orig_matrix
    index_val = user_mapping[user_id]
    u, s, v = numpy.linalg.svd(orig_matrix, full_matrices=False)
    composite = numpy.dot(numpy.dot(u, numpy.diag(s)), v)
    return composite[index_val]


# calculate global average values for the queried user
def calc_local_average(user, games):
    global user_averages
    #user_total_hours = 0
    ratings_sum = 0
    user_averages[user] = {}
    #for game in games:
        #user_total_hours += games[game]
    for game in games:
        if games[game] > 0:  # if user_total_hours != 0
            local_average = games[game] / (game_hours[game] / float(game_user[game]))  # float(user_total_hours)
            ratings_sum += local_average
            user_averages[user][game] = local_average
    return ratings_sum / len(games)


def global_average():
    global user_game_dict
    global user_averages
    global game_averages
    global global_rating
    global game_hours
    global game_user

    #initializing and finding needed values
    for user in user_game_dict:
        user_averages[user] = {}
        if 'games' in user_game_dict[user]['response']:
            for game in user_game_dict[user]['response']['games']:
                # add up total hours per game
                game_hours[game['appid']] = game_hours.get(game['appid'], 0) + game['playtime_forever']
                # add up number of users per game
                game_user[game['appid']] = game_user.get(game['appid'], 0) + 1
    for user in user_game_dict:
        #user_total_hours = 0
        # for each game in the user's gamelist
        if 'games' in user_game_dict[user]['response']:
            # Then get the local averages per game, per user
            for game in user_game_dict[user]['response']['games']:
                # Calculate local average
                if game['playtime_forever'] > 0:  # if user_total_hours != 0
                    local_average = game['playtime_forever'] / (game_hours[game['appid']] / float(game_user[game['appid']]))  # float(user_total_hours)
                    user_averages[user][game['appid']] = local_average
                    # Add each local average to global total
                    game_averages[game['appid']] = game_averages.get(game['appid'], 0) + local_average
    for appid in game_averages:
        game_averages[appid] /= game_user[appid]

    game_sum = 0
    for game in game_averages:
        game_sum += game_averages[game]
    global_rating = game_sum / len(game_averages)


# Used to populate data files
def main():
    print 'Overwrite In Progress...'
    read()
    global_average()
    map_users()
    map_games()
    build_matrix()
    write_to_files()
    print 'Overwrite Complete!'

