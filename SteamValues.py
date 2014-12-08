import json
import re
import numpy
import scipy
from scipy.sparse import linalg

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

    '''print "Writing to user averages..."
    file_five = open("user_averages", "w")
    file_five.write(str(user_averages))
    file_five.close()'''
    
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
    #global user_averages
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

    '''print "Reading user_averages"
    file_five = open("user_averages", "r")
    user_averages = eval(file_five.read())'''

    print "Reading global_rating"
    file_six = open("global_rating", "r")
    global_rating = eval(file_six.read())

    print "Reading game_hours"
    file_seven = open("game_hours", "r")
    game_hours = eval(file_seven.read())

    print "Reading game_user"
    file_eight = open("game_user", "r")
    game_user = eval(file_eight.read())


# Read in the dataset of Steam Users
# And reduce the size of the dataset by aggregating the hours for every 'block_size' many users
def read(file_name, block_size):
    global user_game_dict
    # read_game_dict[appid][data]
    read_game_dict = {}
    # current_aggregate[appid][(average_hours, num_users)]
    current_aggregate = {}
    read_count = 0

    data_file = open(file_name, "r")
    for line in data_file:
        line = re.sub('u', '', line)
        line = re.sub('\'', '\"', line)
        dataset = json.loads(line[18:])
        read_game_dict[line[:17]] = dataset
        read_count += 1

        # if reached the block_size then aggregate those users
        if read_count >= block_size:
            for user in read_game_dict:
                if 'games' in read_game_dict[user]['response']:
                    for game in read_game_dict[user]['response']['games']:
                        # check for the game and add it or average it with the existing amount
                        if game['appid'] in current_aggregate:
                            aggregate = current_aggregate[game['appid']][0]
                            num = current_aggregate[game['appid']][1]
                            aggregate = ((aggregate * num) + game['playtime_forever']) / float(num + 1)
                            num += 1
                            current_aggregate[game['appid']] = (aggregate, num)
                        else:
                            current_aggregate[game['appid']] = (game['playtime_forever'], 1)
            user_game_dict[str(len(user_game_dict))] = current_aggregate
            print 'Read', len(user_game_dict) * block_size, 'users...'
            current_aggregate = {}
            read_game_dict = {}
            read_count = 0

    # add in the last set which was less than block_size
    if current_aggregate != {}:
        user_game_dict[str(len(user_game_dict))] = current_aggregate
    data_file.close()


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


def orig_matrix_add_user(user, local_averages):
    global orig_matrix
    global user_mapping
    if user not in user_mapping:
        orig_matrix += [[]]
        index = len(orig_matrix) - 1
        for game in sorted(game_averages.keys()):
            orig_matrix[index] += [0]
        gameids = local_averages.keys()
        for game in gameids:
            if game in game_mapping:
                orig_matrix[index][game_mapping[game]] = local_averages[game]
        user_mapping[user] = index
    else:
        gameids = local_averages.keys()
        for game in gameids:
            if game in game_mapping:
                orig_matrix[user_mapping[user]][game_mapping[game]] = local_averages[game]


# create svd input matrix
def build_matrix():
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
def svd():
    global orig_matrix
    u, s, v = scipy.sparse.linalg.svds(orig_matrix)
    composite = numpy.dot(numpy.dot(u, numpy.diag(s)), v)
    return composite[-1]


# calculate global average values for the queried user
def calc_local_average(games):
    #user_total_hours = 0
    ratings_sum = 0
    local_averages = {}
    #for game in games:
        #user_total_hours += games[game]
    for game in games:
        if games[game] > 0 and game in game_averages:  # if user_total_hours != 0
            local_average = games[game] / (game_hours[game] / float(game_user[game]))  # float(user_total_hours)
            ratings_sum += local_average
            local_averages[game] = local_average
    return (ratings_sum / len(games)), local_averages


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
        for appid in user_game_dict[user]:
            # add up total hours per game
            game_hours[appid] = game_hours.get(appid, 0) + user_game_dict[user][appid][0]
            # add up number of users per game
            game_user[appid] = game_user.get(appid, 0) + 1
    for user in user_game_dict:
            # Then get the local averages per game, per user
            for appid in user_game_dict[user]:
                # Calculate local average
                if user_game_dict[user][appid][0] > 0:
                    local_average = user_game_dict[user][appid][0] / (game_hours[appid] / float(game_user[appid]))
                    user_averages[user][appid] = local_average
                    # Add each local average to global total
                    game_averages[appid] = game_averages.get(appid, 0) + local_average

    game_sum = 0
    for appid in game_averages:
        game_sum += game_averages[appid]
    global_rating = game_sum / len(game_averages)


# Used to populate data files
def main():
    print 'Overwrite In Progress...'
    read("final_dataset.txt", 500)
    print 'read Complete!'
    global_average()
    print 'global_average Complete!'
    map_users()
    print 'map_users Complete!'
    map_games()
    print 'map_games Complete!'
    build_matrix()
    print 'build_matrix Complete!'
    write_to_files()
    print 'Overwrite Complete!'

