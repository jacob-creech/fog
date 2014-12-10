import json
import re

'''
    This file is primarily used to pre-calculate the datafiles of most of the global variables.
    The only global variable not saved is user_game_dict being our primary dataset which is already
    saved in 'final_dataset.txt'. The only other reason to access this file is from the recommender
    in order to access the data once loaded from the data files.
'''

# user_game_dict[arbitrary_index][str(appid)][(aggregate_score, num_users)]
user_game_dict = {}
# game_averages[appid][global_average]
game_averages = {}
# game_hours[appid][total_hours_played]
game_hours = {}
# game_user[appid][num_of_users]
game_user = {}
# cluster_data[appid][appid][num_shared_users]
cluster_data = {}
# average rating across all collected users
global_rating = 0.0


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


# For every game store the top 2 games with highest shared user scores
def cluster_helper(game1, game2, shared_users):
    global cluster_data
    if game1 not in cluster_data:
        cluster_data[game1] = {}
        cluster_data[game1][game2] = shared_users
    else:
        if len(cluster_data[game1]) < 2:
            cluster_data[game1][game2] = shared_users
        else:
            stored_game1, stored_game2 = cluster_data[game1].keys()
            if shared_users > cluster_data[game1][stored_game1] > cluster_data[game1][stored_game2]:
                cluster_data[game1].pop(stored_game2)
                cluster_data[game1][game2] = shared_users
            elif shared_users > cluster_data[game1][stored_game2] > cluster_data[game1][stored_game1]:
                cluster_data[game1].pop(stored_game1)
                cluster_data[game1][game2] = shared_users
            elif cluster_data[game1][stored_game1] > shared_users > cluster_data[game1][stored_game2]:
                cluster_data[game1].pop(stored_game2)
                cluster_data[game1][game2] = shared_users
            elif cluster_data[game1][stored_game2] > shared_users > cluster_data[game1][stored_game1]:
                cluster_data[game1].pop(stored_game1)
                cluster_data[game1][game2] = shared_users


# Pull the 2 games and their shared users from the file and send to cluster_helper
def store_cluster_data(file_name):
    cluster_file = open(file_name, 'r')
    for line in cluster_file:
        game1, game2 = line.split(',')
        game2, shared_users = game2.split('\t')
        game1 = game1[1:]
        game2 = game2[:-1].strip()
        shared_users = int(shared_users.strip())
        score = shared_users / float(game_user[int(game1)] + game_user[int(game2)])
        cluster_helper(game1, game2, score)
        cluster_helper(game2, game1, score)
    cluster_file.close()


# Calculate Baseline Scores
def global_average():
    global user_game_dict
    global game_averages
    global global_rating
    global game_hours
    global game_user

    #initializing and finding needed values
    for user in user_game_dict:
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
                    # Add each local average to global total
                    game_averages[appid] = game_averages.get(appid, 0) + local_average

    game_sum = 0
    for appid in game_averages:
        game_sum += game_averages[appid]
    global_rating = game_sum / len(game_averages)


# Store values that are reused
def write_to_files():
    print "Writing to game averages..."
    file_one = open("game_averages", "w")
    file_one.write(str(game_averages))
    file_one.close()

    print "Writing to global rating..."
    file_two = open("global_rating", "w")
    file_two.write(str(global_rating))
    file_two.close()

    print "Writing to game hours..."
    file_three = open("game_hours", "w")
    file_three.write(str(game_hours))
    file_three.close()

    print "Writing to game user..."
    file_four = open("game_user", "w")
    file_four.write(str(game_user))
    file_four.close()

    print "Writing to cluster data..."
    file_four = open("cluster_data2", "w")
    file_four.write(str(cluster_data))
    file_four.close()


# read in stored values from previous calculations
def read_from_files():
    global game_averages
    global global_rating
    global game_hours
    global game_user
    global cluster_data

    print "Reading game averages"
    file_one = open("game_averages", "r")
    game_averages = eval(file_one.read())

    print "Reading global_rating"
    file_two = open("global_rating", "r")
    global_rating = eval(file_two.read())

    print "Reading game_hours"
    file_three = open("game_hours", "r")
    game_hours = eval(file_three.read())

    print "Reading game_user"
    file_four = open("game_user", "r")
    game_user = eval(file_four.read())

    print "Reading cluster_data"
    file_five = open("cluster_data2", "r")
    cluster_data = eval(file_five.read())


# Used to populate data files
def main():
    print 'Overwrite In Progress...'
    read("final_dataset.txt", 500)
    print 'read Complete!'

    print 'global_average running...!'
    global_average()
    print 'global_average Complete!'

    print 'cluster_data running...!'
    store_cluster_data('cluster2')
    print 'cluster_data Complete!'
    
    write_to_files()
    print 'Overwrite Complete!'

